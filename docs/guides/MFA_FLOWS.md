# 🔐 MFA User Flow Diagrams

## 📱 Setup Flow

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       │ 1. POST /mfa/setup
       ├────────────────────────────────┐
       │                                │
       ▼                                ▼
┌─────────────────┐            ┌──────────────┐
│  Generate QR    │            │   Generate   │
│   + Secret      │            │ Backup Codes │
└────────┬────────┘            └──────┬───────┘
         │                            │
         │ 2. Return QR + Codes       │
         └────────────┬───────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  User scans QR with    │
         │  Google Authenticator  │
         └────────────┬───────────┘
                      │
                      │ 3. Enter TOTP from app
                      │
                      ▼
         ┌────────────────────────┐
         │ POST /mfa/enable       │
         │ {"code": "123456"}     │
         └────────────┬───────────┘
                      │
                      │ 4. Verify TOTP
                      │
                      ▼
         ┌────────────────────────┐
         │   ✅ MFA Enabled!      │
         │   Save backup codes    │
         └────────────────────────┘
```

---

## 🔐 Login Flow (MFA Enabled, New Device)

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       │ 1. Enter username + password
       │
       ▼
┌──────────────────┐
│  POST /auth/login│
│  {username, pwd} │
└────────┬─────────┘
         │
         │ 2. Validate credentials ✅
         │    Check MFA status → Enabled
         │    Check device → Not trusted
         │
         ▼
┌────────────────────────────┐
│  Response:                 │
│  {                         │
│    requires_mfa: true,     │
│    mfa_token: "temp123"    │
│  }                         │
└────────────┬───────────────┘
             │
             │ 3. User opens authenticator app
             │    Gets 6-digit code
             │
             ▼
┌────────────────────────────┐
│  POST /auth/login          │
│  {                         │
│    username,               │
│    password,               │
│    mfa_code: "456789",     │
│    trust_device: true      │
│  }                         │
└────────────┬───────────────┘
             │
             │ 4. Verify TOTP ✅
             │    Trust device (30 days)
             │
             ▼
┌────────────────────────────┐
│  Response:                 │
│  {                         │
│    access_token: "xyz",    │
│    requires_mfa: false     │
│  }                         │
│                            │
│  ✅ Logged In!             │
│  ✅ Device Trusted         │
└────────────────────────────┘
```

---

## ✅ Login Flow (Trusted Device)

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       │ 1. Enter username + password
       │
       ▼
┌──────────────────┐
│  POST /auth/login│
│  {username, pwd} │
└────────┬─────────┘
         │
         │ 2. Validate credentials ✅
         │    Check MFA status → Enabled
         │    Generate device fingerprint
         │    Check device → Trusted ✅
         │
         ▼
┌────────────────────────────┐
│  Response:                 │
│  {                         │
│    access_token: "xyz",    │
│    requires_mfa: false     │
│  }                         │
│                            │
│  ✅ Logged In!             │
│  🚀 MFA Skipped            │
└────────────────────────────┘
```

---

## 🔑 Backup Code Recovery Flow

```
┌─────────────┐
│    User     │
│ (Lost Phone)│
└──────┬──────┘
       │
       │ 1. Enter username + password
       │
       ▼
┌──────────────────┐
│  POST /auth/login│
│  {username, pwd} │
└────────┬─────────┘
         │
         │ 2. Validate credentials ✅
         │    MFA required
         │
         ▼
┌────────────────────────────┐
│  Response:                 │
│  {                         │
│    requires_mfa: true      │
│  }                         │
└────────────┬───────────────┘
             │
             │ 3. User retrieves saved
             │    backup code from secure storage
             │
             ▼
┌────────────────────────────┐
│  POST /auth/login          │
│  {                         │
│    username,               │
│    password,               │
│    mfa_code: "A3K7N9P2Q4" │ ← 10-char backup code
│  }                         │
└────────────┬───────────────┘
             │
             │ 4. Verify backup code ✅
             │    Mark code as used
             │
             ▼
┌────────────────────────────┐
│  Response:                 │
│  {                         │
│    access_token: "xyz"     │
│  }                         │
│                            │
│  ✅ Logged In!             │
│  ⚠️ Code consumed          │
│  → Remaining: 7/8 codes    │
└────────────────────────────┘
       │
       │ 5. User should now:
       │    - Disable old MFA
       │    - Setup new MFA
       │    - Get new backup codes
       │
       ▼
┌────────────────────────────┐
│  POST /mfa/disable         │
│  POST /mfa/setup           │
│  POST /mfa/enable          │
└────────────────────────────┘
```

---

## 🔄 Device Management Flow

```
┌─────────────────────────────────────┐
│        Account Settings             │
└─────────────┬───────────────────────┘
              │
              │ GET /mfa/devices
              │
              ▼
┌─────────────────────────────────────┐
│  Trusted Devices:                   │
│                                     │
│  1. Chrome on Windows               │
│     Trusted: Dec 1, 2025            │
│     Expires: Dec 31, 2025           │
│     Last used: 2 hours ago          │
│     [Revoke]                        │
│                                     │
│  2. Safari on macOS                 │
│     Trusted: Dec 3, 2025            │
│     Expires: Jan 2, 2026            │
│     Last used: 1 day ago            │
│     [Revoke]                        │
│                                     │
│  3. Firefox on Linux                │
│     Trusted: Nov 28, 2025           │
│     Expires: Dec 28, 2025           │
│     Last used: 1 week ago           │
│     [Revoke]                        │
└─────────────┬───────────────────────┘
              │
              │ User clicks [Revoke] on #3
              │
              ▼
┌─────────────────────────────────────┐
│  DELETE /mfa/devices/3              │
└─────────────┬───────────────────────┘
              │
              │ Device trust revoked ✅
              │
              ▼
┌─────────────────────────────────────┐
│  Updated List:                      │
│                                     │
│  1. Chrome on Windows               │
│  2. Safari on macOS                 │
│                                     │
│  ⚠️ Firefox will require MFA        │
│     on next login                   │
└─────────────────────────────────────┘
```

---

## 🔐 Complete System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      Frontend (React/Next.js)            │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Login   │  │   MFA    │  │ Settings │              │
│  │   Page   │  │  Setup   │  │   Page   │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │             │              │                     │
└───────┼─────────────┼──────────────┼─────────────────────┘
        │             │              │
        │             │              │ API Calls
        ▼             ▼              ▼
┌──────────────────────────────────────────────────────────┐
│                    FastAPI Backend                       │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │           API Endpoints                            │ │
│  │                                                    │ │
│  │  /auth/login ────┐                                │ │
│  │  /auth/register  │  Authentication                │ │
│  │                  │                                │ │
│  │  /mfa/setup ─────┤                                │ │
│  │  /mfa/enable     │  MFA Management                │ │
│  │  /mfa/disable    │                                │ │
│  │  /mfa/devices    │                                │ │
│  └────────┬─────────┴────────────────────────────────┘ │
│           │                                            │
│           ▼                                            │
│  ┌─────────────────────────────────────────────────┐  │
│  │         Business Logic Layer                    │  │
│  │                                                 │  │
│  │  ┌──────────────┐  ┌──────────────┐            │  │
│  │  │ Auth Module  │  │ MFA Manager  │            │  │
│  │  │              │  │              │            │  │
│  │  │ - JWT        │  │ - TOTP       │            │  │
│  │  │ - Bcrypt     │  │ - QR Codes   │            │  │
│  │  │ - Refresh    │  │ - Backup     │            │  │
│  │  │   Tokens     │  │   Codes      │            │  │
│  │  │              │  │ - Device     │            │  │
│  │  │              │  │   Trust      │            │  │
│  │  └──────────────┘  └──────────────┘            │  │
│  └─────────────────────────────────────────────────┘  │
│           │                                            │
│           ▼                                            │
│  ┌─────────────────────────────────────────────────┐  │
│  │              Database (PostgreSQL)              │  │
│  │                                                 │  │
│  │  ┌─────────┐  ┌──────────────┐  ┌──────────┐  │  │
│  │  │  users  │  │ mfa_settings │  │ trusted_ │  │  │
│  │  │         │  │              │  │ devices  │  │  │
│  │  │ - id    │  │ - user_id    │  │          │  │  │
│  │  │ - email │  │ - secret_key │  │ - finger │  │  │
│  │  │ - pwd   │  │ - is_enabled │  │   print  │  │  │
│  │  └────┬────┘  └──────┬───────┘  └────┬─────┘  │  │
│  │       │              │               │        │  │
│  │       └──────────────┴───────────────┘        │  │
│  │                                                │  │
│  │  ┌──────────────────┐                         │  │
│  │  │ mfa_backup_codes │                         │  │
│  │  │                  │                         │  │
│  │  │ - user_id        │                         │  │
│  │  │ - code_hash      │                         │  │
│  │  │ - used_at        │                         │  │
│  │  └──────────────────┘                         │  │
│  └─────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘

External Services:
┌──────────────────┐
│  Authenticator   │
│      Apps        │
│                  │
│ - Google Auth    │
│ - Authy          │
│ - Microsoft Auth │
└──────────────────┘
```

---

## 📊 Device Fingerprinting Process

```
┌──────────────────────────────────────────────┐
│           Incoming Login Request             │
└────────────────────┬─────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   Extract Headers      │
        │                        │
        │ - User-Agent           │
        │ - X-Forwarded-For      │
        │   (or client IP)       │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  Parse User-Agent      │
        │                        │
        │  "Mozilla/5.0          │
        │   (Windows NT 10.0;    │
        │   Win64; x64)          │
        │   Chrome/120.0"        │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │   Extract IP Subnet    │
        │                        │
        │  192.168.1.100         │
        │       ↓                │
        │  192.168.1             │
        │  (first 3 octets)      │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │   Combine Data         │
        │                        │
        │  Mozilla/5.0...:       │
        │  192.168.1             │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │   SHA-256 Hash         │
        │                        │
        │  a7f3c8e2d1b9...       │
        │  (device fingerprint)  │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  Check in DB           │
        │                        │
        │  SELECT * FROM         │
        │  trusted_devices       │
        │  WHERE fingerprint=?   │
        │  AND expires_at > now  │
        └────────┬───────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
   ┌─────────┐      ┌─────────┐
   │  Found  │      │Not Found│
   │  ✅     │      │  ⚠️     │
   └────┬────┘      └────┬────┘
        │                │
        ▼                ▼
   Skip MFA        Require MFA
```

---

## 🎯 Security Layers

```
┌───────────────────────────────────────────────┐
│            Defense in Depth                   │
│                                               │
│  Layer 1: Password Authentication             │
│  ├─ Bcrypt hashing (cost factor 12)          │
│  ├─ 8-72 character length                    │
│  └─ Rate limiting (10 attempts/min)          │
│                                               │
│  Layer 2: Multi-Factor Authentication         │
│  ├─ TOTP (RFC 6238)                          │
│  ├─ 6-digit codes, 30-second window          │
│  ├─ Clock drift tolerance (±30s)             │
│  └─ Backup codes (SHA-256 hashed)            │
│                                               │
│  Layer 3: Device Trust                        │
│  ├─ Fingerprint verification                 │
│  ├─ 30-day automatic expiry                  │
│  ├─ User-revocable anytime                   │
│  └─ Auto-renewal on each login               │
│                                               │
│  Layer 4: Token Security                      │
│  ├─ JWT access tokens (30 min)               │
│  ├─ Refresh tokens (14 days)                 │
│  ├─ SHA-256 token storage                    │
│  └─ HttpOnly cookies                         │
│                                               │
│  Layer 5: Transport Security                  │
│  ├─ HTTPS only (production)                  │
│  ├─ CSRF protection                          │
│  └─ CORS configuration                       │
└───────────────────────────────────────────────┘
```

---

## 📈 MFA Adoption Funnel

```
Total Users: 1000
     │
     ▼
┌────────────────────┐
│  MFA Available     │  1000 users (100%)
└─────────┬──────────┘
          │
          │ 40% enable MFA
          ▼
┌────────────────────┐
│  MFA Enabled       │  400 users (40%)
└─────────┬──────────┘
          │
          │ 80% trust at least 1 device
          ▼
┌────────────────────┐
│  Device Trusted    │  320 users (32%)
└─────────┬──────────┘
          │
          │ 5% use backup code once
          ▼
┌────────────────────┐
│  Backup Code Used  │  20 users (2%)
└────────────────────┘

Key Metrics to Track:
- MFA adoption rate: 40%
- Device trust rate: 80% of MFA users
- Backup code usage: 5% (account recovery)
- Failed MFA attempts: Monitor for attacks
```

---

**Created:** 2025-12-05  
**Purpose:** Visual reference for MFA implementation  
**Audience:** Developers, QA, Product Managers
