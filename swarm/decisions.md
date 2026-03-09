# 🗃️ Database Schema Design
**Agent**: Developer Agent
**Completed**: 2026-03-09
**Task ref**: tasks.md → Task 2

---

## Tables

### `users`
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| username | VARCHAR(64) | UNIQUE NOT NULL |
| email | VARCHAR(120) | UNIQUE NOT NULL |
| password_hash | VARCHAR(128) | bcrypt hash, NOT NULL |
| is_active | BOOLEAN | DEFAULT 1 |
| role | VARCHAR(20) | DEFAULT 'user' |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### `tokens` (JWT JTI blacklist)
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| jti | VARCHAR(36) | UNIQUE NOT NULL (JWT ID) |
| token_type | VARCHAR(10) | NOT NULL ('access' or 'refresh') |
| user_id | INTEGER | NOT NULL, FK → users.id |
| expires_at | DATETIME | NOT NULL |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| is_revoked | BOOLEAN | DEFAULT 0 |

---

## Indexes
- `idx_users_username` on `users(username)`
- `idx_users_email` on `users(email)`
- `idx_tokens_jti` on `tokens(jti)` ← critical for fast revocation checks
- `idx_tokens_user_id` on `tokens(user_id)`

---

## Migration Script (SQLite / PostgreSQL compatible)

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    role VARCHAR(20) DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jti VARCHAR(36) UNIQUE NOT NULL,
    token_type VARCHAR(10) NOT NULL,
    user_id INTEGER NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_revoked BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_tokens_jti ON tokens (jti);
CREATE INDEX IF NOT EXISTS idx_tokens_user_id ON tokens (user_id);
```

---

## Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Dev DB | SQLite | Zero config, easy for development |
| Prod DB | PostgreSQL | Concurrency, scalability, ACID compliance |
| Password hashing | bcrypt | Adaptive cost factor, built-in salt, industry standard |
| Token strategy | JWT + JTI table | Stateless JWT benefits + ability to revoke on logout/compromise |
| Role field | VARCHAR in users | Simple RBAC, expandable without schema change |