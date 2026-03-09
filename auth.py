"""
auth.py — Login API
=====================
Flask Blueprint for JWT-based authentication.

Endpoints:
  POST /auth/login   → issue access + refresh token
  POST /auth/logout  → revoke current token (JTI blacklist)
  GET  /auth/me      → return current user info

Usage:
  from auth import auth_bp, init_db
  app.register_blueprint(auth_bp)
  init_db(app)

Requirements:
  pip install flask flask-jwt-extended bcrypt
"""

import os
import sqlite3
import bcrypt
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)

# ── Blueprint ─────────────────────────────────────────────────────────────────
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

DB_PATH = os.path.join(os.path.dirname(__file__), "vault_data", "auth.db")


# ── DB helpers ────────────────────────────────────────────────────────────────
def get_db():
    """Return a thread-local SQLite connection."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db(app):
    """Create tables if they don't exist. Call once at startup."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with app.app_context():
        conn = sqlite3.connect(DB_PATH)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      VARCHAR(64)  UNIQUE NOT NULL,
                email         VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                is_active     BOOLEAN DEFAULT 1,
                role          VARCHAR(20)  DEFAULT 'user',
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tokens (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                jti        VARCHAR(36) UNIQUE NOT NULL,
                token_type VARCHAR(10) NOT NULL,
                user_id    INTEGER NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_revoked BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_users_email    ON users  (email);
            CREATE INDEX IF NOT EXISTS idx_tokens_jti     ON tokens (jti);
            CREATE INDEX IF NOT EXISTS idx_tokens_user_id ON tokens (user_id);
        """)
        conn.commit()
        conn.close()


# ── JWT token-in-blocklist check ──────────────────────────────────────────────
def is_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    db  = sqlite3.connect(DB_PATH)
    row = db.execute(
        "SELECT is_revoked FROM tokens WHERE jti = ?", (jti,)
    ).fetchone()
    db.close()
    return bool(row and row[0])


def setup_jwt(jwt: JWTManager):
    """Wire the revocation check into JWTManager."""
    jwt.token_in_blocklist_loader(is_token_revoked)


# ── Utility ───────────────────────────────────────────────────────────────────
def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _revoke_token(jti: str, token_type: str, user_id: int, expires_at: datetime):
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """INSERT OR IGNORE INTO tokens (jti, token_type, user_id, expires_at, is_revoked)
           VALUES (?, ?, ?, ?, 1)""",
        (jti, token_type, user_id, expires_at.isoformat()),
    )
    db.commit()
    db.close()


# ── Routes ────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /auth/login
    Body: { "email": "...", "password": "..." }
    Returns: { "access_token": "...", "refresh_token": "..." }
    """
    data = request.get_json(silent=True) or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # --- Validate input ---
    if not email or not password:
        return jsonify(error="email and password are required"), 422

    # --- Lookup user ---
    db  = get_db()
    row = db.execute(
        "SELECT id, username, email, password_hash, is_active, role FROM users WHERE email = ?",
        (email,),
    ).fetchone()

    if not row:
        return jsonify(error="Invalid email or password"), 401

    if not row["is_active"]:
        return jsonify(error="Account is disabled"), 403

    if not _check_password(password, row["password_hash"]):
        return jsonify(error="Invalid email or password"), 401

    # --- Issue tokens ---
    identity = str(row["id"])
    additional_claims = {"role": row["role"], "username": row["username"]}

    access_token  = create_access_token(
        identity=identity,
        additional_claims=additional_claims,
        expires_delta=timedelta(hours=1),
    )
    refresh_token = create_refresh_token(
        identity=identity,
        expires_delta=timedelta(days=30),
    )

    return jsonify(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id":       row["id"],
            "username": row["username"],
            "email":    row["email"],
            "role":     row["role"],
        },
    ), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    POST /auth/logout
    Header: Authorization: Bearer <access_token>
    Revokes the current access token.
    """
    jwt_data = get_jwt()
    jti      = jwt_data["jti"]
    user_id  = int(get_jwt_identity())
    exp      = datetime.fromtimestamp(jwt_data["exp"], tz=timezone.utc)

    _revoke_token(jti, "access", user_id, exp)
    return jsonify(message="Successfully logged out"), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    GET /auth/me
    Header: Authorization: Bearer <access_token>
    Returns current user info.
    """
    user_id = int(get_jwt_identity())
    claims  = get_jwt()

    db  = get_db()
    row = db.execute(
        "SELECT id, username, email, role, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()

    if not row:
        return jsonify(error="User not found"), 404

    return jsonify(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        role=row["role"],
        created_at=row["created_at"],
    ), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    POST /auth/refresh
    Header: Authorization: Bearer <refresh_token>
    Returns a new access token.
    """
    identity = get_jwt_identity()
    claims   = get_jwt()
    new_access = create_access_token(
        identity=identity,
        additional_claims={"role": claims.get("role"), "username": claims.get("username")},
        expires_delta=timedelta(hours=1),
    )
    return jsonify(access_token=new_access), 200


# ── Dev-only: register a user (remove in production) ─────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    """
    POST /auth/register  [DEV ONLY — disable in production]
    Body: { "username": "...", "email": "...", "password": "..." }
    """
    data     = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify(error="username, email and password are required"), 422
    if len(password) < 8:
        return jsonify(error="password must be at least 8 characters"), 422

    pw_hash = _hash_password(password)
    try:
        db = get_db()
        db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, pw_hash),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify(error="username or email already exists"), 409

    return jsonify(message="User created successfully"), 201
