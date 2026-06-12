"""
PySide6 main window: 3 tabs - Portfolio, Vaults, Settings.

The UI runs the heavy collection/analysis pipeline on a background QThread
to keep the UI responsive. The same pipeline is also scheduled by
APScheduler in the background.
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QTime

from app.core.config import ConfigManager
from app.notifications.base import build_provider
from app.scheduler.scheduler import AppScheduler


LOG = logging.getLogger(__name__)


# --------------------------------------------------------------------- workers


class PipelineWorker(QThread):
    """Runs collect+analyze in background; emits results when done."""

    progress = Signal(str)
    finished_payload = Signal(dict)

    def __init__(self, scheduler: AppScheduler) -> None:
        super().__init__()
        self.scheduler = scheduler

    def run(self) -> None:
        self.progress.emit("Running pipeline...")
        payload = self.scheduler.run_pipeline_once()
        self.finished_payload.emit(payload)


# ----------------------------------------------------------------- main window


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Hyperliquid Vault Analyzer")
        self.resize(1200, 760)

        self.cm = ConfigManager()
        self.scheduler = AppScheduler(self.cm, on_pipeline_done=self._on_scheduler_done)

        self._build_ui()
        self._load_settings_into_ui()

        # Start the scheduler so background jobs run too.
        try:
            self.scheduler.start()
        except Exception as e:  # noqa: BLE001
            LOG.warning("Scheduler start failed: %s", e)

        self.statusBar().showMessage(
            f"Data dir: {self.cm.config.data_dir}", 8000
        )

    # ----- UI construction ----------------------------------------------
    def _build_ui(self) -> None:
        tabs = QTabWidget()
        tabs.addTab(self._build_portfolio_tab(), "Portfolio")
        tabs.addTab(self._build_vaults_tab(), "Vaults")
        tabs.addTab(self._build_settings_tab(), "Settings")
        self.setCentralWidget(tabs)
        self.setStatusBar(QStatusBar())

        # menu
        run_action = QAction("Run Now", self)
        run_action.triggered.connect(self._on_run_now)
        self.menuBar().addAction(run_action)
        test_action = QAction("Send Test Notification", self)
        test_action.triggered.connect(self._on_test_notification)
        self.menuBar().addAction(test_action)

    def _build_portfolio_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)

        top = QHBoxLayout()
        self.run_btn = QPushButton("Run Now")
        self.run_btn.clicked.connect(self._on_run_now)
        top.addWidget(self.run_btn)
        self.status_label = QLabel("Idle.")
        top.addWidget(self.status_label)
        top.addStretch(1)
        v.addLayout(top)

        self.portfolio_table = QTableWidget(0, 8)
        self.portfolio_table.setHorizontalHeaderLabels(
            ["Leg", "Name", "Address", "TVL", "Return", "MDD", "DDnow", "Weight"]
        )
        self.portfolio_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        v.addWidget(self.portfolio_table)
        return w

    def _build_vaults_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Top vaults by TVL with computed metrics:"))
        self.vaults_table = QTableWidget(0, 7)
        self.vaults_table.setHorizontalHeaderLabels(
            ["Name", "Address", "TVL", "Return", "MDD", "DDnow", "Recovery"]
        )
        self.vaults_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        v.addWidget(self.vaults_table)
        return w

    def _build_settings_tab(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        form = QFormLayout()

        self.data_dir_edit = QLineEdit()
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._pick_data_dir)
        row = QHBoxLayout()
        row.addWidget(self.data_dir_edit)
        row.addWidget(browse_btn)
        form.addRow("Data directory (D-drive recommended):", _wrap(row))

        self.top_n_spin = QSpinBox(); self.top_n_spin.setRange(50, 500)
        form.addRow("Top N vaults to track:", self.top_n_spin)

        self.max_port_spin = QSpinBox(); self.max_port_spin.setRange(2, 20)
        form.addRow("Max portfolio size (<=20):", self.max_port_spin)

        self.collect_interval_spin = QSpinBox(); self.collect_interval_spin.setRange(5, 24 * 60)
        form.addRow("Collection interval (minutes):", self.collect_interval_spin)

        self.big_move_spin = QDoubleSpinBox(); self.big_move_spin.setRange(0.1, 1000.0); self.big_move_spin.setSuffix(" %")
        form.addRow("Big move alert threshold:", self.big_move_spin)

        self.alert_change_chk = QCheckBox("Alert on portfolio change")
        form.addRow(self.alert_change_chk)

        self.daily_chk = QCheckBox("Enable daily report")
        self.daily_time = QTimeEdit()
        rh = QHBoxLayout(); rh.addWidget(self.daily_chk); rh.addWidget(self.daily_time)
        form.addRow("Daily report:", _wrap(rh))

        self.weekly_chk = QCheckBox("Enable weekly report on")
        self.weekly_day = QComboBox(); self.weekly_day.addItems(["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"])
        rh2 = QHBoxLayout(); rh2.addWidget(self.weekly_chk); rh2.addWidget(self.weekly_day)
        form.addRow("Weekly report:", _wrap(rh2))

        # Notification provider
        self.provider_combo = QComboBox(); self.provider_combo.addItems(["telegram", "expo", "fcm"])
        form.addRow("Notification provider:", self.provider_combo)
        self.tg_token_edit = QLineEdit(); self.tg_token_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Telegram bot token:", self.tg_token_edit)
        self.tg_chat_edit = QLineEdit()
        form.addRow("Telegram chat_id:", self.tg_chat_edit)

        outer.addLayout(form)

        # Help text
        help_text = QTextEdit(); help_text.setReadOnly(True)
        help_text.setMarkdown(
            "### How to create a Telegram bot\n"
            "1. Open Telegram and search for **@BotFather**.\n"
            "2. Send `/newbot` and follow prompts to choose a name and username.\n"
            "3. Copy the **bot token** that BotFather replies with.\n"
            "4. Open a chat with **your bot** and send `/start`.\n"
            "5. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser.\n"
            "6. In the JSON, find `chat.id` (an integer). Paste it as **chat_id** above.\n"
            "7. Click *Save & Apply* and then *Send Test Notification* in the menu.\n\n"
            "### Switching push channel later\n"
            "When the dedicated mobile app is ready, change `Notification provider` to `expo` or `fcm` and fill in the relevant credentials in `~/.hyperliquid_vault_analyzer/config.json`."
        )
        outer.addWidget(help_text, 1)

        save_btn = QPushButton("Save && Apply")
        save_btn.clicked.connect(self._on_save_settings)
        outer.addWidget(save_btn)
        return w

    # ----- handlers ------------------------------------------------------
    def _pick_data_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose data directory", self.data_dir_edit.text())
        if path:
            self.data_dir_edit.setText(path)

    def _load_settings_into_ui(self) -> None:
        c = self.cm.config
        self.data_dir_edit.setText(c.data_dir)
        self.top_n_spin.setValue(c.top_n_vaults)
        self.max_port_spin.setValue(c.max_portfolio_size)
        self.collect_interval_spin.setValue(c.collection_interval_minutes)
        self.big_move_spin.setValue(c.big_move_threshold_pct)
        self.alert_change_chk.setChecked(c.alert_on_portfolio_change)
        self.daily_chk.setChecked(c.daily_report_enabled)
        h, m = (c.daily_report_time.split(":") + ["0"])[:2]
        self.daily_time.setTime(QTime(int(h), int(m)))
        self.weekly_chk.setChecked(c.weekly_report_enabled)
        idx = max(0, self.weekly_day.findText(c.weekly_report_day.upper()))
        self.weekly_day.setCurrentIndex(idx)
        self.provider_combo.setCurrentText(c.notification_provider)
        self.tg_token_edit.setText(c.telegram_bot_token)
        self.tg_chat_edit.setText(c.telegram_chat_id)

    def _on_save_settings(self) -> None:
        t = self.daily_time.time()
        self.cm.update(
            data_dir=self.data_dir_edit.text().strip() or self.cm.config.data_dir,
            top_n_vaults=self.top_n_spin.value(),
            max_portfolio_size=self.max_port_spin.value(),
            collection_interval_minutes=self.collect_interval_spin.value(),
            big_move_threshold_pct=self.big_move_spin.value(),
            alert_on_portfolio_change=self.alert_change_chk.isChecked(),
            daily_report_enabled=self.daily_chk.isChecked(),
            daily_report_time=f"{t.hour():02d}:{t.minute():02d}",
            weekly_report_enabled=self.weekly_chk.isChecked(),
            weekly_report_day=self.weekly_day.currentText(),
            notification_provider=self.provider_combo.currentText(),
            telegram_bot_token=self.tg_token_edit.text().strip(),
            telegram_chat_id=self.tg_chat_edit.text().strip(),
        )
        self.cm.ensure_data_dir()
        try:
            self.scheduler.reload()
        except Exception as e:  # noqa: BLE001
            LOG.warning("Scheduler reload failed: %s", e)
        QMessageBox.information(self, "Saved", "Settings saved and applied.")

    def _on_run_now(self) -> None:
        self.run_btn.setEnabled(False)
        self.status_label.setText("Running pipeline...")
        self._worker = PipelineWorker(self.scheduler)
        self._worker.finished_payload.connect(self._on_worker_done)
        self._worker.start()

    def _on_worker_done(self, payload: Dict[str, Any]) -> None:
        self.run_btn.setEnabled(True)
        if not payload.get("ok"):
            self.status_label.setText(f"Failed: {payload.get('error')}")
            QMessageBox.warning(self, "Pipeline failed", str(payload.get("error", "Unknown error")))
            return
        self._render_payload(payload)

    def _on_scheduler_done(self, payload: Dict[str, Any]) -> None:
        # Called from a non-Qt thread by APScheduler; keep UI updates minimal.
        try:
            self._render_payload(payload)
        except Exception:  # noqa: BLE001
            pass

    def _render_payload(self, payload: Dict[str, Any]) -> None:
        portfolio = payload.get("portfolio") or {}
        holdings: List[Dict[str, Any]] = portfolio.get("holdings", [])
        self.portfolio_table.setRowCount(len(holdings))
        for r, h in enumerate(holdings):
            self.portfolio_table.setItem(r, 0, QTableWidgetItem((h.get("leg") or "").upper()))
            self.portfolio_table.setItem(r, 1, QTableWidgetItem(h.get("name") or ""))
            self.portfolio_table.setItem(r, 2, QTableWidgetItem(h.get("address") or ""))
            self.portfolio_table.setItem(r, 3, QTableWidgetItem(f"{(h.get('tvl') or 0):,.0f}"))
            self.portfolio_table.setItem(r, 4, QTableWidgetItem(f"{(h.get('return_all') or 0)*100:+.2f}%"))
            self.portfolio_table.setItem(r, 5, QTableWidgetItem(f"{(h.get('mdd') or 0)*100:.2f}%"))
            self.portfolio_table.setItem(r, 6, QTableWidgetItem(f"{(h.get('drawdown_now') or 0)*100:.2f}%"))
            self.portfolio_table.setItem(r, 7, QTableWidgetItem(f"{(h.get('weight') or 0)*100:.2f}%"))

        # Vaults tab: show all vaults computed in this run (use storage latest)
        self.status_label.setText(f"Done. Holdings: {len(holdings)}, metrics: {payload.get('metrics_count')}")

        try:
            from app.data.storage import Storage
            storage = Storage(self.cm.config.data_dir)
            metrics = storage.get_all_metrics()
            metrics.sort(key=lambda m: (m.get("tvl") or 0), reverse=True)
            self.vaults_table.setRowCount(len(metrics))
            for r, m in enumerate(metrics):
                self.vaults_table.setItem(r, 0, QTableWidgetItem(m.get("name") or ""))
                self.vaults_table.setItem(r, 1, QTableWidgetItem(m.get("address") or ""))
                self.vaults_table.setItem(r, 2, QTableWidgetItem(f"{(m.get('tvl') or 0):,.0f}"))
                self.vaults_table.setItem(r, 3, QTableWidgetItem(f"{(m.get('return_all') or 0)*100:+.2f}%"))
                self.vaults_table.setItem(r, 4, QTableWidgetItem(f"{(m.get('mdd') or 0)*100:.2f}%"))
                self.vaults_table.setItem(r, 5, QTableWidgetItem(f"{(m.get('drawdown_now') or 0)*100:.2f}%"))
                self.vaults_table.setItem(r, 6, QTableWidgetItem(f"{(m.get('recovery_factor') or 0):.2f}"))
        except Exception as e:  # noqa: BLE001
            LOG.warning("vaults table render failed: %s", e)

    def _on_test_notification(self) -> None:
        provider = build_provider(self.cm.config.to_dict())
        ok = provider.send_message(
            "Test notification",
            "This is a test from Hyperliquid Vault Analyzer.",
        )
        if ok:
            QMessageBox.information(self, "Sent", "Test notification sent successfully.")
        else:
            QMessageBox.warning(
                self,
                "Failed",
                "Could not send test notification. Verify your provider settings.",
            )

    def closeEvent(self, event) -> None:  # type: ignore[override]
        try:
            self.scheduler.stop()
        except Exception:  # noqa: BLE001
            pass
        super().closeEvent(event)


def _wrap(layout) -> QWidget:
    """Wrap a QLayout into a QWidget for use with QFormLayout.addRow."""
    w = QWidget()
    w.setLayout(layout)
    return w


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
