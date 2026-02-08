# Authentication System

## Overview
YatinVeda uses JWT-based authentication with access and refresh tokens for secure, stateless session management.

## Token Types

### Access Token
- **Purpose:** Authorize API requests
- **TTL:** 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Claims:** `sub` (username), `user_id`, `is_admin`, `iat`, `nbf`, `exp`
- **Storage:** Client (memory or secure storage; avoid localStorage for XSS protection)
- **Usage:** Include in `Authorization: Bearer <access_token>` header

### Refresh Token
- **Purpose:** Obtain new access/refresh tokens without re-login
- **TTL:** 14 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
- **Claims:** Same as access token, plus `typ=refresh`, `jti` (unique ID)
- **Storage:** Database (hashed with SHA-256), client (httpOnly cookie recommended)
- **Usage:** Send to `/api/v1/auth/refresh` to rotate tokens

## Lifecycle

### Login Flow
1. User submits credentials to `POST /api/v1/auth/login`
2. Server verifies password, issues access + refresh tokens
3. Refresh token is hashed and persisted in `refresh_tokens` table with `user_id`, `expires_at`
4. Client receives both tokens in response

### Refresh Flow
1. Client sends refresh token to `POST /api/v1/auth/refresh`
2. Server verifies JWT signature and `typ=refresh` claim
3. DB record is checked: not revoked, not expired
4. Old refresh token is revoked (`revoked_at` set)
5. New access + refresh tokens are issued; new refresh token hashed and stored
6. Client replaces old tokens with new ones

### Logout Flow
1. Client sends refresh token to `POST /api/v1/auth/logout`
2. Server revokes the token in DB (`revoked_at` set)
3. Client discards both access and refresh tokens

### Revoke All (Admin/Security)
- `POST /api/v1/auth/revoke-all` with `user_id` revokes all active refresh tokens for a user
- Useful for password changes, security incidents, or admin lockout

## Error Semantics

### HTTP 401 (Unauthorized)
- **When:** Missing, malformed, expired, or invalid token
- **Endpoints:** All protected routes; explicit on `/api/v1/auth/refresh` for bad refresh tokens
- **Action:** Client should redirect to login or attempt refresh (if access token expired)

### HTTP 403 (Forbidden)
- **When:** Valid token but insufficient permissions (e.g., non-admin accessing admin route)
- **Action:** Inform user of access restriction; do not retry

### Strict vs Lenient Bearer
- **`LenientHTTPBearer`:** Returns 403 when `Authorization` header is missing (default FastAPI)
- **`Strict401HTTPBearer`:** Returns 401 for missing credentials (used in `/api/v1/user_charts` for test compatibility)

## Security Best Practices

- **Hashing:** Refresh tokens stored as SHA-256 hashes to prevent token leakage from DB compromise
- **Rotation:** Each refresh invalidates the old token, mitigating replay attacks
- **Rate Limiting:** Login and registration endpoints are rate-limited (disabled in tests via `PYTEST_CURRENT_TEST`)
- **Password Truncation:** Passwords truncated to 71 bytes for bcrypt safety (see `modules/auth.py`)
- **Logging:** Auth events (login, failures) logged via `logging_config.py` for audit trails

## Configuration

Environment variables (`.env` or system):
- `SECRET_KEY`: JWT signing key (change in production)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Access token TTL (default 30)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token TTL (default 14)
- `DISABLE_RATELIMIT`: Set to `1` to bypass rate limits (tests only)

## Database Schema

### `refresh_tokens` Table
| Column       | Type       | Description                              |
|--------------|------------|------------------------------------------|
| `id`         | Integer    | Primary key                              |
| `user_id`    | Integer    | Foreign key to `users.id`                |
| `token_hash` | String     | SHA-256 hash of the refresh token (unique) |
| `jti`        | String     | JWT ID from token claims (optional)      |
| `created_at` | DateTime   | Token issuance timestamp                 |
| `expires_at` | DateTime   | Token expiry timestamp                   |
| `revoked_at` | DateTime   | Revocation timestamp (null if active)    |

## Endpoints

- `POST /api/v1/auth/register` – Create new user
- `POST /api/v1/auth/login` – Issue access + refresh tokens
- `POST /api/v1/auth/refresh` – Rotate tokens
- `POST /api/v1/auth/logout` – Revoke refresh token
- `POST /api/v1/auth/revoke-all` – Revoke all tokens for a user (admin)

## Client Integration (Recommended)

1. **Login:** Store access token in memory, refresh token in httpOnly cookie or secure storage
2. **API calls:** Send access token in `Authorization: Bearer <token>`
3. **401 on API call:** Attempt refresh; if refresh fails, redirect to login
4. **Logout:** Call logout endpoint, clear tokens
5. **Auto-refresh:** Optionally refresh proactively before access token expires (e.g., at 25min mark)

## Testing Notes

- Tests use in-memory SQLite; refresh tokens table created via `Base.metadata.create_all`
- Rate limiting bypassed when `PYTEST_CURRENT_TEST` or `DISABLE_RATELIMIT=1` is set
- Test fixtures should clean up refresh tokens to avoid cross-test pollution
