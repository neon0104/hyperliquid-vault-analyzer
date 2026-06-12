"""
Storage layer: SQLite for structured data + JSON snapshots on disk.

Database schema:
- vaults(address PRIMARY KEY, name, leader, tvl, is_closed, relationship,
         created_time_ms, last_updated_ms)
- vault_history(address, ts_ms, account_value, pnl,
                PRIMARY KEY(address, ts_ms))
- vault_metrics(address PRIMARY KEY, return_all, mdd, recovery_factor,
                drawdown_now, score_stable, score_recovery, computed_at_ms)
- portfolio_snapshots(id INTEGER PK, created_at_ms, payload_json)
"""
from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


class Storage:
    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "snapshots").mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "vaults.sqlite3"
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS vaults (
                    address TEXT PRIMARY KEY,
                    name TEXT,
                    leader TEXT,
                    tvl REAL,
                    is_closed INTEGER,
                    relationship TEXT,
                    created_time_ms INTEGER,
                    last_updated_ms INTEGER
                );

                CREATE TABLE IF NOT EXISTS vault_history (
                    address TEXT,
                    ts_ms INTEGER,
                    account_value REAL,
                    pnl REAL,
                    PRIMARY KEY(address, ts_ms)
                );

                CREATE TABLE IF NOT EXISTS vault_metrics (
                    address TEXT PRIMARY KEY,
                    return_all REAL,
                    mdd REAL,
                    recovery_factor REAL,
                    drawdown_now REAL,
                    score_stable REAL,
                    score_recovery REAL,
                    computed_at_ms INTEGER
                );

                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at_ms INTEGER,
                    payload_json TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_vaults_tvl ON vaults(tvl DESC);
                CREATE INDEX IF NOT EXISTS idx_history_address ON vault_history(address);
                """
            )

    # --- vault summaries ---------------------------------------------------
    def upsert_vault_summaries(self, summaries: Iterable[Dict[str, Any]]) -> None:
        now = int(time.time() * 1000)
        rows: List[Tuple] = []
        for s in summaries:
            rows.append(
                (
                    s.get("address"),
                    s.get("name"),
                    s.get("leader"),
                    float(s.get("tvl", 0.0) or 0.0),
                    1 if s.get("is_closed") else 0,
                    s.get("relationship"),
                    int(s.get("created_time_ms") or 0),
                    now,
                )
            )
        with self._conn() as c:
            c.executemany(
                """
                INSERT INTO vaults(address,name,leader,tvl,is_closed,relationship,created_time_ms,last_updated_ms)
                VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(address) DO UPDATE SET
                    name=excluded.name,
                    leader=excluded.leader,
                    tvl=excluded.tvl,
                    is_closed=excluded.is_closed,
                    relationship=excluded.relationship,
                    created_time_ms=excluded.created_time_ms,
                    last_updated_ms=excluded.last_updated_ms
                """,
                rows,
            )

    def get_top_vaults_by_tvl(self, n: int = 200, only_open: bool = True) -> List[Dict[str, Any]]:
        with self._conn() as c:
            cur = c.cursor()
            q = "SELECT address,name,leader,tvl,is_closed,relationship FROM vaults"
            if only_open:
                q += " WHERE is_closed=0"
            q += " ORDER BY tvl DESC LIMIT ?"
            cur.execute(q, (n,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    # --- history -----------------------------------------------------------
    def replace_vault_history(self, address: str, history: List[Tuple[int, float, float]]) -> None:
        """history: list of (ts_ms, account_value, pnl)."""
        with self._conn() as c:
            c.execute("DELETE FROM vault_history WHERE address=?", (address,))
            c.executemany(
                "INSERT OR REPLACE INTO vault_history(address,ts_ms,account_value,pnl) VALUES(?,?,?,?)",
                [(address, ts, av, pnl) for ts, av, pnl in history],
            )

    def get_vault_history(self, address: str) -> List[Tuple[int, float, float]]:
        with self._conn() as c:
            cur = c.execute(
                "SELECT ts_ms, account_value, pnl FROM vault_history WHERE address=? ORDER BY ts_ms ASC",
                (address,),
            )
            return [(int(ts), float(av), float(pnl)) for ts, av, pnl in cur.fetchall()]

    # --- metrics -----------------------------------------------------------
    def upsert_metrics(self, address: str, m: Dict[str, float]) -> None:
        now = int(time.time() * 1000)
        with self._conn() as c:
            c.execute(
                """
                INSERT INTO vault_metrics(address,return_all,mdd,recovery_factor,drawdown_now,
                                          score_stable,score_recovery,computed_at_ms)
                VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(address) DO UPDATE SET
                    return_all=excluded.return_all,
                    mdd=excluded.mdd,
                    recovery_factor=excluded.recovery_factor,
                    drawdown_now=excluded.drawdown_now,
                    score_stable=excluded.score_stable,
                    score_recovery=excluded.score_recovery,
                    computed_at_ms=excluded.computed_at_ms
                """,
                (
                    address,
                    float(m.get("return_all", 0.0)),
                    float(m.get("mdd", 0.0)),
                    float(m.get("recovery_factor", 0.0)),
                    float(m.get("drawdown_now", 0.0)),
                    float(m.get("score_stable", 0.0)),
                    float(m.get("score_recovery", 0.0)),
                    now,
                ),
            )

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        with self._conn() as c:
            cur = c.execute(
                """
                SELECT v.address,v.name,v.tvl,m.return_all,m.mdd,m.recovery_factor,
                       m.drawdown_now,m.score_stable,m.score_recovery
                FROM vault_metrics m JOIN vaults v ON v.address=m.address
                """
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    # --- portfolio snapshot ------------------------------------------------
    def save_portfolio_snapshot(self, payload: Dict[str, Any]) -> int:
        now = int(time.time() * 1000)
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO portfolio_snapshots(created_at_ms,payload_json) VALUES(?,?)",
                (now, json.dumps(payload, ensure_ascii=False)),
            )
            return cur.lastrowid

    def latest_portfolio_snapshot(self) -> Optional[Dict[str, Any]]:
        with self._conn() as c:
            cur = c.execute(
                "SELECT payload_json FROM portfolio_snapshots ORDER BY created_at_ms DESC LIMIT 1"
            )
            row = cur.fetchone()
            if not row:
                return None
            return json.loads(row[0])

    # --- raw JSON snapshots ------------------------------------------------
    def write_json_snapshot(self, name: str, payload: Any) -> Path:
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = self.data_dir / "snapshots" / f"{ts}_{name}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        return path
