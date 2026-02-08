# 🔐 Multi-Factor Authentication (MFA) Guide

## Overview

YatinVeda implements a **user-friendly MFA system** that balances security with convenience:

✅ **TOTP-based 2FA** (Google Authenticator, Authy, Microsoft Authenticator)  
✅ **Backup Codes** for account recovery (8 codes)  
✅ **Trusted Devices** - Skip MFA for 30 days on trusted devices  
✅ **Smooth UX** - Minimal friction, maximum security

---

## 🚀 Quick Start

### 1. Setup MFA

**Endpoint:** `POST /api/v1/mfa/setup`

```bash
curl -X POST "http://localhost/api/v1/mfa/setup" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "qr_code": "iVBORw0KGgoAAAANS...",  // Base64 QR code image
  "secret_key": "JBSWY3DPEHPK3PXP",  // Manual entry key
  "backup_codes": [
    "A3K7N9P2Q4",
    "B8M2X6Y4Z9",
    // ... 6 more codes
  ]
}
```

**Important:** Save backup codes securely! They won't be shown again.

---

### 2. Enable MFA

Scan the QR code with your authenticator app, then verify:

**Endpoint:** `POST /api/v1/mfa/enable`

```bash
curl -X POST "http://localhost/api/v1/mfa/enable" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "123456"
  }'
```

**Response:**
```json
{
  "message": "MFA enabled successfully! Your account is now more secure.",
  "is_enabled": true
}
```

---

### 3. Login with MFA

#### Step 1: Initial Login (Password Only)

```bash
curl -X POST "http://localhost/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Response (MFA Required):**
```json
{
  "access_token": "",
  "token_type": "bearer",
  "expires_in": 0,
  "requires_mfa": true,
  "mfa_token": "eyJhbGciOiJI..."  // 5-minute temporary token
}
```

#### Step 2: Submit MFA Code

```bash
curl -X POST "http://localhost/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "SecurePass123!",
    "mfa_code": "123456",
    "trust_device": true
  }'
```

**Response (Success):**
```json
{
  "access_token": "eyJhbGciOiJI...",
  "token_type": "bearer",
  "expires_in": 1800,
  "requires_mfa": false
}
```

---

## 🔑 Backup Codes

### View Status

**Endpoint:** `GET /api/v1/mfa/backup-codes/status`

```bash
curl -X GET "http://localhost/api/v1/mfa/backup-codes/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "total": 8,
  "used": 2,
  "remaining": 6
}
```

### Regenerate Codes

**Endpoint:** `POST /api/v1/mfa/backup-codes/regenerate`

```bash
curl -X POST "http://localhost/api/v1/mfa/backup-codes/regenerate" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
[
  "N2P4Q6R8S9",
  "T3V5W7X9Y2",
  // ... 6 more codes
]
```

⚠️ **Warning:** Old backup codes will stop working immediately!

---

## 📱 Trusted Devices

### How It Works

When logging in with MFA, set `trust_device: true` to skip MFA for **30 days** on that device.

**Device Fingerprint:** Combination of User-Agent + IP subnet (handles dynamic IPs)

### List Trusted Devices

**Endpoint:** `GET /api/v1/mfa/devices`

```bash
curl -X GET "http://localhost/api/v1/mfa/devices" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
[
  {
    "id": 1,
    "device_name": "Chrome on Windows",
    "trusted_at": "2025-12-01T10:00:00Z",
    "expires_at": "2025-12-31T10:00:00Z",
    "last_used_at": "2025-12-05T14:30:00Z",
    "ip_address": "192.168.1.100"
  },
  {
    "id": 2,
    "device_name": "Safari on macOS",
    "trusted_at": "2025-12-03T12:00:00Z",
    "expires_at": "2026-01-02T12:00:00Z",
    "last_used_at": "2025-12-04T09:15:00Z",
    "ip_address": "192.168.1.101"
  }
]
```

### Revoke Device Trust

**Endpoint:** `DELETE /api/v1/mfa/devices/{device_id}`

```bash
curl -X DELETE "http://localhost/api/v1/mfa/devices/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "message": "Device trust revoked successfully"
}
```

---

## 🔄 Complete User Flows

### Flow 1: First-Time MFA Setup

```
User
  ↓
1. Call /mfa/setup
  ↓
2. Scan QR code with authenticator app
  ↓
3. Save backup codes securely
  ↓
4. Call /mfa/enable with TOTP code
  ↓
✅ MFA Enabled
```

### Flow 2: Login with MFA (New Device)

```
User
  ↓
1. Enter username/password → /auth/login
  ↓
2. Receive requires_mfa=true + mfa_token
  ↓
3. Enter TOTP code from app
  ↓
4. Call /auth/login with mfa_code + trust_device=true
  ↓
✅ Logged In + Device Trusted for 30 Days
```

### Flow 3: Login with MFA (Trusted Device)

```
User
  ↓
1. Enter username/password → /auth/login
  ↓
✅ Logged In Immediately (MFA Skipped)
```

### Flow 4: Account Recovery (Lost Phone)

```
User
  ↓
1. Enter username/password → /auth/login
  ↓
2. Receive requires_mfa=true
  ↓
3. Enter backup code instead of TOTP
  ↓
4. Call /auth/login with mfa_code (backup code)
  ↓
✅ Logged In (Backup Code Consumed)
  ↓
5. Disable old MFA → /mfa/disable
  ↓
6. Setup new MFA → /mfa/setup
```

---

## 🛡️ Security Features

### 1. TOTP Parameters
- **Algorithm:** SHA-1 (industry standard)
- **Interval:** 30 seconds
- **Digits:** 6
- **Validity Window:** ±1 interval (handles clock drift)

### 2. Backup Codes
- **Count:** 8 codes per user
- **Length:** 10 characters (uppercase alphanumeric, no ambiguous chars)
- **Storage:** SHA-256 hashed in database
- **One-Time Use:** Each code works only once

### 3. Trusted Devices
- **Duration:** 30 days from last use
- **Fingerprint:** SHA-256(User-Agent + IP Subnet)
- **Auto-Renewal:** Each login extends trust by 30 days
- **User Control:** Can revoke individual devices anytime

### 4. Rate Limiting
- Login attempts: 10/minute per IP
- MFA setup: Inherits user authentication rate limits
- Prevents brute force attacks on TOTP codes

---

## 📊 API Reference

### Check MFA Status

```http
GET /api/v1/mfa/status
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "is_enabled": true,
  "verified_at": "2025-12-01T10:00:00Z",
  "backup_codes_status": {
    "total": 8,
    "used": 1,
    "remaining": 7
  },
  "trusted_devices_count": 2
}
```

### Disable MFA

```http
POST /api/v1/mfa/disable
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "code": "123456"  // Required if MFA is enabled
}
```

**Response:**
```json
{
  "message": "MFA disabled successfully",
  "is_enabled": false
}
```

---

## 🧪 Testing

### Install Dependencies

```bash
pip install pyotp==2.9.0 qrcode[pil]==7.4.2
```

### Run Migration

```bash
cd backend
alembic upgrade head
```

### Test MFA Flow (cURL)

```bash
# 1. Register user
curl -X POST "http://localhost/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!@#"
  }'

# 2. Login to get access token
ACCESS_TOKEN=$(curl -X POST "http://localhost/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Test123!@#"
  }' | jq -r '.access_token')

# 3. Setup MFA
curl -X POST "http://localhost/api/v1/mfa/setup" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq

# 4. Manually enter TOTP code from authenticator app
# 5. Enable MFA
curl -X POST "http://localhost/api/v1/mfa/enable" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "ENTER_6_DIGIT_CODE"
  }' | jq

# 6. Test MFA login
curl -X POST "http://localhost/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Test123!@#",
    "mfa_code": "ENTER_6_DIGIT_CODE",
    "trust_device": true
  }' | jq
```

---

## 🎨 Frontend Integration Examples

### React/Next.js Example

```typescript
// hooks/useMFA.ts
import { useState } from 'react';

interface MFASetupResponse {
  qr_code: string;
  secret_key: string;
  backup_codes: string[];
}

export function useMFA() {
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);

  const setupMFA = async (accessToken: string) => {
    const res = await fetch('/api/v1/mfa/setup', {
      headers: { Authorization: `Bearer ${accessToken}` }
    });
    const data: MFASetupResponse = await res.json();
    
    setQrCode(data.qr_code);
    setBackupCodes(data.backup_codes);
    
    return data;
  };

  const enableMFA = async (accessToken: string, code: string) => {
    const res = await fetch('/api/v1/mfa/enable', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ code })
    });
    
    return res.ok;
  };

  return { setupMFA, enableMFA, qrCode, backupCodes };
}

// components/MFASetup.tsx
export function MFASetup({ accessToken }: { accessToken: string }) {
  const { setupMFA, enableMFA, qrCode, backupCodes } = useMFA();
  const [totpCode, setTotpCode] = useState('');

  const handleSetup = async () => {
    await setupMFA(accessToken);
  };

  const handleEnable = async () => {
    const success = await enableMFA(accessToken, totpCode);
    if (success) {
      alert('MFA enabled successfully!');
    }
  };

  return (
    <div>
      <h2>Setup Multi-Factor Authentication</h2>
      
      {!qrCode && (
        <button onClick={handleSetup}>Start MFA Setup</button>
      )}
      
      {qrCode && (
        <>
          <img src={`data:image/png;base64,${qrCode}`} alt="QR Code" />
          
          <h3>Backup Codes (Save These!)</h3>
          <ul>
            {backupCodes.map((code, i) => (
              <li key={i}><code>{code}</code></li>
            ))}
          </ul>
          
          <input 
            type="text" 
            placeholder="Enter 6-digit code"
            value={totpCode}
            onChange={e => setTotpCode(e.target.value)}
            maxLength={6}
          />
          
          <button onClick={handleEnable}>Enable MFA</button>
        </>
      )}
    </div>
  );
}
```

---

## 🔧 Configuration

### Environment Variables

```env
# MFA is always available, no special config needed
# Existing auth settings apply:
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14
COOKIE_SECURE=false  # Set to true in production with HTTPS
COOKIE_SAMESITE=lax
```

### Database Schema

```sql
-- MFA Settings (1 per user)
CREATE TABLE mfa_settings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    is_enabled BOOLEAN DEFAULT 0,
    secret_key TEXT NOT NULL,  -- TOTP secret
    backup_codes_hash TEXT,    -- Not used (codes stored separately)
    verified_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Trusted Devices (multiple per user)
CREATE TABLE trusted_devices (
    id INTEGER PRIMARY KEY,
    mfa_settings_id INTEGER NOT NULL REFERENCES mfa_settings(id),
    device_fingerprint TEXT UNIQUE NOT NULL,
    device_name TEXT,
    trusted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    last_used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT
);

-- Backup Codes (8 per user)
CREATE TABLE mfa_backup_codes (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    code_hash TEXT NOT NULL,  -- SHA-256 hash
    used_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📱 Supported Authenticator Apps

- **Google Authenticator** (iOS, Android)
- **Microsoft Authenticator** (iOS, Android)
- **Authy** (iOS, Android, Desktop)
- **1Password** (iOS, Android, Desktop, Browser)
- **Bitwarden** (iOS, Android, Desktop, Browser)
- Any TOTP-compatible app

---

## ❓ Troubleshooting

### "Invalid MFA code" Error

**Causes:**
1. Clock drift on server/phone
2. Wrong code from authenticator
3. Code already used (codes expire in 30 seconds)

**Solutions:**
1. Ensure phone/server clocks are synced
2. Wait for next code (30 seconds)
3. Use backup code if TOTP continues to fail

### Lost Phone / Can't Access Authenticator

**Solution:** Use a backup code

```bash
curl -X POST "http://localhost/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "SecurePass123!",
    "mfa_code": "A3K7N9P2Q4"  // Backup code (10 chars)
  }'
```

After logging in:
1. Disable old MFA: `POST /api/v1/mfa/disable`
2. Setup new MFA: `POST /api/v1/mfa/setup`

### All Backup Codes Used

**Solution:** Regenerate backup codes while logged in

```bash
curl -X POST "http://localhost/api/v1/mfa/backup-codes/regenerate" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🎯 Best Practices

### For Users
1. ✅ Save backup codes in a password manager
2. ✅ Use "Trust Device" on personal devices only
3. ✅ Regenerate backup codes if you suspect exposure
4. ✅ Review trusted devices periodically
5. ❌ Don't share backup codes with anyone

### For Developers
1. ✅ Show backup codes only once during setup
2. ✅ Provide clear UX for backup code entry (10 chars vs 6 digits)
3. ✅ Display backup code usage status in settings
4. ✅ Allow users to download/print backup codes
5. ✅ Implement admin override for locked-out users

---

## 📚 Additional Resources

- [RFC 6238: TOTP Specification](https://tools.ietf.org/html/rfc6238)
- [OWASP MFA Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html)
- [PyOTP Documentation](https://pyauth.github.io/pyotp/)
- [QRCode Library](https://github.com/lincolnloop/python-qrcode)

---

## 🆘 Support

**Issues?** Open a GitHub issue with:
- Steps to reproduce
- Error messages
- Browser/authenticator app details
- MFA status from `/api/v1/mfa/status`

**Security Concerns?** Email security@yatinveda.com

---

**Made with 🔐 by YatinVeda Team**
