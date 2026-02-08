# Frontend Cookie Integration Test Plan

## Changes Made

### 1. Updated `api-client.ts` for Cookie-Based Auth

**Token Storage:**
- `setTokens()` now accepts optional refresh token (prefer httpOnly cookie)
- CSRF token stored in memory and sessionStorage
- Refresh token only stored if explicitly provided (fallback mode)

**Refresh Flow:**
- Prefers cookie-based refresh (httpOnly cookie sent automatically via `credentials: 'include'`)
- Includes CSRF token in `x-csrf-token` header when refreshing via cookie
- Falls back to body-based refresh if refresh token available in storage
- Extracts new CSRF token from response headers

**Request Handling:**
- All requests include `credentials: 'include'` to send/receive httpOnly cookies
- CSRF token automatically added to mutation requests (POST, PUT, PATCH, DELETE)
- CSRF tokens extracted from response headers and cached

**Login:**
- Extracts CSRF token from `x-csrf-token` response header
- Does not store refresh token in JavaScript (it's in httpOnly cookie)
- Uses `credentials: 'include'` to allow backend to set cookies

**Logout:**
- Uses cookie-based logout (no refresh token in body)
- Backend reads refresh token from httpOnly cookie
- Clears all client-side tokens

### 2. Security Improvements

✅ **HttpOnly Cookies**: Refresh tokens stored in httpOnly cookies (XSS-safe)
✅ **CSRF Protection**: CSRF tokens required for cookie-based refresh
✅ **Automatic Rotation**: CSRF tokens updated from response headers
✅ **Secure Transport**: All auth requests use `credentials: 'include'`

### 3. Backward Compatibility

- Still supports body-based refresh if refresh token in sessionStorage
- Graceful degradation for environments without cookie support

## Testing Checklist

### Manual Testing (Browser DevTools)

1. **Login Flow**
   - [ ] Check Application → Cookies for `refresh_token` (httpOnly, Secure, SameSite)
   - [ ] Verify `x-csrf-token` in response headers
   - [ ] Confirm only access token in sessionStorage, no refresh token

2. **Refresh Flow**
   - [ ] Network tab shows `refresh_token` cookie sent automatically
   - [ ] Request includes `x-csrf-token` header
   - [ ] New access token received
   - [ ] CSRF token updated if rotated

3. **Logout Flow**
   - [ ] `refresh_token` cookie deleted
   - [ ] sessionStorage cleared
   - [ ] Redirect to login

4. **API Requests**
   - [ ] All mutations include `x-csrf-token` header
   - [ ] Authorization header includes access token
   - [ ] Cookies sent with every request

### Integration Test Scenarios

```bash
# Test 1: Login and verify cookie
curl -i -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test@1234"}' \
  -c cookies.txt

# Check for Set-Cookie: refresh_token header
# Check for x-csrf-token header

# Test 2: Refresh with cookie
curl -i -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "x-csrf-token: <token-from-login>" \
  -b cookies.txt

# Should return new access token

# Test 3: Logout
curl -i -X POST http://localhost:8000/api/v1/auth/logout \
  -b cookies.txt

# Cookie should be cleared
```

## Expected Behavior

### Login Response
```
HTTP/1.1 200 OK
Set-Cookie: refresh_token=<jwt>; HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth; Max-Age=1209600
x-csrf-token: <random-token>
Content-Type: application/json

{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Refresh Request (Cookie-based)
```
POST /api/v1/auth/refresh
Cookie: refresh_token=<jwt>
x-csrf-token: <csrf-token>
```

### Refresh Response
```
HTTP/1.1 200 OK
Set-Cookie: refresh_token=<new-jwt>; HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth; Max-Age=1209600
x-csrf-token: <new-csrf-token>
Content-Type: application/json

{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

## Notes

- Refresh tokens never exposed to JavaScript (XSS protection)
- CSRF tokens required for cookie-based operations (CSRF protection)
- Cookies scoped to `/api/v1/auth` path for security
- SameSite=Lax provides CSRF mitigation
- Secure flag ensures HTTPS-only in production
