# Temp-Links-Containers
A robust, asynchronous REST API built with FastAPI for secure storage and management of encrypted secrets.

# 🔐 Secrets API

A secure REST API for storing and managing encrypted secrets with user authentication.

---

## Overview

Secrets API allows users to register, authenticate, and manage personal encrypted secrets. Each secret is tied to a user account and can only be decrypted by its owner.

---

## Authentication

The API uses **JWT Bearer tokens**. After logging in, include the token in all protected requests:

```
Authorization: Bearer <your_token>
```

---

## Docker

The API uses **JWT Bearer tokens**. After logging in, include the token in all protected requests:

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

#### Register
```http
POST /auth/register
Content-Type: application/json

{
  "username": "string",
  "email": "user@example.com",
  "password": "stringst"
}
```

#### Login
```http 
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "string"
}
```
**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

### 🗝️ Secrets

> All secrets endpoints require authentication.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/secrets/` | List all secrets for the current user |
| `POST` | `/secrets/` | Create a new encrypted secret |
| `POST` | `/secrets/decrypt/{secret_id}` | Decrypt a specific secret |
| `DELETE` | `/secrets/{secret_id}` | Delete a specific secret |

#### Create a Secret
```http
POST /secrets/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "GitHub Personal Access Token",
  "content": "ghp_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7",
  "expires_at": "2026-12-31T23:59:59.000Z",
  "encryption_password": "MyStr0ng#Pass"
}
```

#### List Secrets
```http
GET /secrets/
Authorization: Bearer <token>
```
Returns a list of secrets **without** decrypted content.

#### Decrypt a Secret
```http
POST /secrets/decrypt/{secret_id}
Authorization: Bearer <token>
```
Returns the decrypted content of the specified secret.

#### Delete a Secret
```http
DELETE /secrets/{secret_id}
Authorization: Bearer <token>
```

---

## Error Handling

The API returns standard HTTP status codes:

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request |
| `401` | Unauthorized — missing or invalid token |
| `403` | Forbidden — access denied |
| `404` | Not Found |
| `422` | Validation Error — invalid request body |

---

## Getting Started

1. **Register** a new account via `POST /auth/register`
2. **Login** via `POST /auth/login` to receive your JWT token
3. **Create secrets** via `POST /secrets/`
4. **Retrieve and decrypt** secrets as needed
5. **Delete** secrets or your account when done

---

## Tech Stack

- REST API — JSON over HTTP
- JWT-based stateless authentication (PyJWT)
- Encrypted secret storage
- FastAPI
- Asyncpg
- Pydantic
- SQLAlchemy
- Pytest
- Docker

## Patterns

- Repository
- Strategy

---

> ⚠️ **Security Notice:** Never share your JWT token. Tokens grant full access to your account and all stored secrets.
