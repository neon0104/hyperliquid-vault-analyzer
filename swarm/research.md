# 🔬 Research: Authentication Libraries
**Agent**: Research Agent
**Completed**: 2026-03-09
**Task ref**: tasks.md → Task 1

---

## Options Compared

| Library | Type | Pros | Cons |
|---------|------|------|------|
| **Flask-JWT-Extended** | Token (JWT) | Feature-rich, refresh tokens, fresh tokens, revocation support, great for APIs & SPAs | Stateless by default (requires DB for revocation) |
| **Flask-Login** | Session (Cookie) | Simple, battle-tested, great for server-rendered apps | Not ideal for cross-origin APIs, cookie-based |
| **Authlib** | OAuth2 / OpenID | Standards-compliant, social login, most flexible for 2025 | More setup complexity |
| **Flask-Dance** | OAuth2 | Simple setup for common providers (Google, GitHub) | Less flexible than Authlib |

---

## Security Best Practices

1. **HTTPS everywhere** — enforce in all non-local environments
2. **Environment variables** — use `python-dotenv` for secrets, never hardcode
3. **Short-lived Access Tokens + Refresh Tokens** — store refresh tokens in Secure/HttpOnly cookies
4. **OAuth2 `state` parameter** — always use to prevent CSRF attacks
5. **bcrypt for passwords** — adaptive hashing with built-in salts
6. **Token revocation** — maintain a JTI (JWT ID) blacklist table in DB

---

## ✅ Recommendation

> **Authlib (OAuth2) + Flask-JWT-Extended** combined approach

### Rationale:
- **Authlib** handles the complex OAuth2 state/token exchange securely (e.g., Google login)
- **Flask-JWT-Extended** secures subsequent API communications after login
- Together they cover both user identity (OAuth2) and API auth (JWT)
- Most production-ready combination for a Flask dashboard in 2025

---

## Notes for Developer Agent (Task 3)

### Quick Start — Flask-JWT-Extended:
```python
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "your-secret-key-from-env"  # use os.environ
jwt = JWTManager(app)

@app.route("/auth/login", methods=["POST"])
def login():
    # verify credentials → create token
    access_token = create_access_token(identity=user_id)
    return jsonify(access_token=access_token)

@app.route("/auth/me")
@jwt_required()
def me():
    return jsonify(user_id=get_jwt_identity())
```

### pip install:
```
flask-jwt-extended
authlib
python-dotenv
bcrypt
```
