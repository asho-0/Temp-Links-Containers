# Temp-Links-Containers
A robust, asynchronous REST API built with FastAPI for secure storage and management of encrypted secrets.

# 🔐 Secrets API

A secure REST API for storing and managing encrypted secrets with user authentication.

---

## Overview

Secrets API allows users to register, authenticate, and manage personal encrypted secrets. Each secret is tied to a user account and can only be decrypted by its owner. Secrets can optionally be shared via a time-limited public link — no authentication required to view them.

---

## Authentication

The API uses **JWT Bearer tokens**. After logging in, include the token in all protected requests:

```
Authorization: Bearer <your_token>
```

---

## Secret key generation
```
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Docker

```
make build
make dev
```

---

## Endpoints

### 🔑 Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register a new user account |
| `POST` | `/auth/login` | Login and receive a JWT token |
| `DELETE` | `/auth/delete` | Delete the authenticated user's account |

---

### 🗝️ Secrets

> All secrets endpoints require authentication, except `GET /secrets/shared/{token}`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/secrets/` | List all secrets for the current user |
| `POST` | `/secrets/` | Create a new encrypted secret |
| `POST` | `/secrets/decrypt/{secret_id}` | Decrypt a specific secret |
| `DELETE` | `/secrets/{secret_id}` | Delete a specific secret |
| `POST` | `/secrets/{secret_id}/share_link` | Generate a public share link |
| `GET` | `/secrets/shared/{token}` | Access a secret via share link — **no auth required** |

#### Create a Secret
```http
POST /secrets/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "GitHub Personal Access Token",
  "content": "ghp_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7",
  "encryption_password": "MyStr0ng#Pass"
}
```

#### Decrypt a Secret
```http
POST /secrets/decrypt/{secret_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "encryption_password": "MyStr0ng#Pass"
}
```

#### Generate a Share Link
```http
POST /secrets/{secret_id}/share_link
Authorization: Bearer <token>
Content-Type: application/json

{
  "encryption_password": "MyStr0ng#Pass",
  "expires_minutes": 60
}
```

> ⚠️ **Important:** `encryption_password` must be **exactly the same password used when the secret was created**.

**Response:**
```json
{
  "share_url": "https://yourdomain.com/secrets/shared/eyJhbGciOiJIUzI1NiIs..."
}
```

#### Access via Share Link
```http
GET /secrets/shared/{token}
```

No authentication required. Valid until the token expires.

---

## Share Link Security Model

```
Secret created with password "mypass"
             ↓
POST /secrets/{id}/share_link  { "encryption_password": "mypass", "expires_minutes": 60 }
             ↓
Server embeds secret_id + owner_id + password inside a signed JWT
             ↓
/secrets/shared/eyJ...  ← only an opaque token visible in the URL
             ↓
Anyone with the link can read the secret — no login needed
```

- Secret ID and owner ID are **never visible** in the URL
- The password lives **inside the signed token**, not in the database
- Expired tokens are rejected automatically

---

## Error Handling

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `401` | Unauthorized |
| `404` | Not Found — also returned for invalid/expired share links |
| `410` | Gone — secret has expired |
| `422` | Validation Error or decryption failure |

---

## Tech Stack

FastAPI · SQLAlchemy · Asyncpg · Pydantic · PyJWT · Celery · Redis · Docker · AES-256-GCM · PBKDF2-SHA256 ·

## Patterns

- Repository
- Strategy

---

> ⚠️ **Security Notice:** Never share your JWT auth token — it grants full access to your account. Share link tokens are scoped to a single secret and expire automatically.