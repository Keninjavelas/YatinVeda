# MFA Frontend Integration Guide

## Overview

This guide explains how to integrate the MFA frontend components with your YatinVeda application's authentication flow.

**Components Created:**
- `MFASetup.tsx` - 4-step guided setup wizard
- `MFAVerify.tsx` - Login-time verification interface
- `TrustedDevices.tsx` - Manage trusted devices
- `MFASettings.tsx` - Central settings management page

## Architecture

```
Authentication Flow:
├── Login Page
│   ├── Email + Password
│   └── If MFA enabled → MFAVerify
├── MFAVerify (Login-time)
│   ├── TOTP code input
│   ├── Backup code fallback
│   └── Trust device option
├── Settings/Profile
│   └── MFASettings (Status, Setup, Manage)
│       ├── Enable/Disable MFA
│       ├── Regenerate backup codes
│       └── TrustedDevices (Revoke, View)
```

## API Endpoints Required

Ensure your backend has these endpoints:

### Setup & Status
```
POST   /api/v1/mfa/setup              → { qr_code, secret, backup_codes }
POST   /api/v1/mfa/enable             → { success }
POST   /api/v1/mfa/disable            → { success }
GET    /api/v1/mfa/status             → { mfa_enabled, setup_date, backup_codes_count, trusted_devices_count }
```

### Verification
```
POST   /api/v1/auth/verify-mfa        → { access_token, refresh_token }
GET    /api/v1/mfa/devices            → [{ id, device_name, trusted_at, expires_at, last_used_at, ip_address }]
DELETE /api/v1/mfa/devices/{id}       → { success }
POST   /api/v1/mfa/backup-codes/regenerate → { backup_codes: [{ code, used }] }
```

## Integration Steps

### 1. Update Login Flow

**File:** `frontend/src/app/(auth)/login/page.tsx` (or similar)

```typescript
import MFAVerify from '@/components/MFAVerify';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function LoginPage() {
  const router = useRouter();
  const [requiresMFA, setRequiresMFA] = useState(false);
  const [tempToken, setTempToken] = useState('');

  const handleLoginSubmit = async (email: string, password: string) => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (data.requires_mfa) {
        // MFA is enabled on this account
        setTempToken(data.temp_token); // Temporary token for MFA verification
        setRequiresMFA(true);
      } else {
        // No MFA, login successful
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        router.push('/dashboard');
      }
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  if (requiresMFA) {
    return (
      <MFAVerify
        tempToken={tempToken}
        onSuccess={() => router.push('/dashboard')}
        onCancel={() => {
          setRequiresMFA(false);
          setTempToken('');
        }}
      />
    );
  }

  // Regular login form
  return (
    <div>
      {/* Email and password input */}
      <button onClick={() => handleLoginSubmit(email, password)}>
        Sign In
      </button>
    </div>
  );
}
```

### 2. Update MFAVerify Component (Optional Props)

The `MFAVerify` component can accept optional props for customization:

```typescript
interface MFAVerifyProps {
  tempToken?: string;        // Temporary token from login
  onSuccess?: () => void;     // Callback on successful verification
  onCancel?: () => void;      // Callback on cancel
  inline?: boolean;          // Use inline (login flow) vs modal (settings)
}
```

**Example - Update MFAVerify.tsx:**

```typescript
interface MFAVerifyProps {
  tempToken?: string;
  onSuccess?: () => void;
  onCancel?: () => void;
  inline?: boolean;
}

const MFAVerify: React.FC<MFAVerifyProps> = ({ 
  tempToken, 
  onSuccess, 
  onCancel,
  inline = false 
}) => {
  const [verificationMethod, setVerificationMethod] = useState<'totp' | 'backup'>('totp');
  const [code, setCode] = useState('');
  const [trustDevice, setTrustDevice] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleVerify = async () => {
    if (!code) {
      setError('Please enter a code');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      };

      // Use temp token if provided (from login flow)
      if (tempToken) {
        headers['Authorization'] = `Bearer ${tempToken}`;
      } else {
        // Otherwise use stored access token (from settings)
        const token = localStorage.getItem('access_token');
        if (token) headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch('/api/v1/auth/verify-mfa', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          code,
          code_type: verificationMethod === 'totp' ? 'totp' : 'backup',
          trust_device: trustDevice
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Verification failed');
      }

      const data = await response.json();

      if (inline) {
        // Login flow - store tokens and redirect
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        if (data.device_token) {
          localStorage.setItem('device_token', data.device_token);
        }
        onSuccess?.();
      } else {
        // Settings flow - just call callback
        onSuccess?.();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  // ... rest of component
};
```

### 3. Add MFA Settings to Profile/Settings Page

**File:** `frontend/src/app/(authenticated)/settings/page.tsx` (or similar)

```typescript
import MFASettings from '@/components/MFASettings';

export default function SettingsPage() {
  return (
    <div className="max-w-2xl mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Account Settings</h1>

      {/* Other settings sections */}
      <div className="mb-8">
        {/* Profile settings, password change, etc. */}
      </div>

      {/* MFA Settings */}
      <div className="mt-12 pt-8 border-t">
        <MFASettings 
          onMFAStatusChange={(enabled) => {
            console.log('MFA status changed:', enabled);
            // Update UI or show notification
          }}
        />
      </div>
    </div>
  );
}
```

### 4. Protect MFA Endpoints with Authentication

Ensure your backend checks authorization headers:

```python
# backend/api/v1/mfa.py example

from fastapi import APIRouter, Depends, HTTPException, Request
from ..modules.auth import verify_token

router = APIRouter(prefix="/mfa")

@router.get("/status")
async def get_mfa_status(current_user = Depends(verify_token)):
    """Get current MFA status for authenticated user"""
    # Implementation...
    pass

@router.post("/setup")
async def setup_mfa(current_user = Depends(verify_token)):
    """Initialize MFA setup for authenticated user"""
    # Implementation...
    pass

@router.post("/enable")
async def enable_mfa(
    body: MFASetupComplete,
    current_user = Depends(verify_token)
):
    """Enable MFA after verification"""
    # Implementation...
    pass

@router.delete("/devices/{device_id}")
async def revoke_device(
    device_id: int,
    current_user = Depends(verify_token)
):
    """Revoke trust for a specific device"""
    # Implementation...
    pass
```

## State Management

### Option 1: Local Storage (Simple)

```typescript
// Store after successful login
localStorage.setItem('access_token', token.access_token);
localStorage.setItem('refresh_token', token.refresh_token);
if (token.device_token) {
  localStorage.setItem('device_token', token.device_token); // Optional 30-day device token
}

// Clear on logout
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
localStorage.removeItem('device_token');
```

### Option 2: Context/Provider (Recommended)

```typescript
// frontend/src/context/AuthContext.tsx

import React, { createContext, useContext, useState, useEffect } from 'react';

interface AuthContextType {
  isAuthenticated: boolean;
  user: any;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if token exists on mount
    const token = localStorage.getItem('access_token');
    if (token) {
      setIsAuthenticated(true);
      // Optionally fetch user info
    }
  }, []);

  const login = (token: string) => {
    localStorage.setItem('access_token', token);
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('device_token');
    setIsAuthenticated(false);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
```

## Testing

### Unit Test Example (MFASetup)

```typescript
// frontend/src/components/__tests__/MFASetup.test.tsx

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MFASetup from '../MFASetup';

describe('MFASetup', () => {
  it('displays QR code on step 2', async () => {
    render(<MFASetup onSetupComplete={jest.fn()} />);
    
    // Click next to go to setup step
    const nextButton = screen.getByText('Next');
    await userEvent.click(nextButton);
    
    await waitFor(() => {
      expect(screen.getByAltText('MFA QR Code')).toBeInTheDocument();
    });
  });

  it('verifies code and shows backup codes', async () => {
    render(<MFASetup onSetupComplete={jest.fn()} />);
    
    // Navigate to verification step
    // Enter code
    // Verify it shows backup codes
  });
});
```

### E2E Test Example (Cypress)

```typescript
// frontend/cypress/e2e/mfa-flow.cy.ts

describe('MFA Setup and Verification', () => {
  it('enables MFA and verifies login', () => {
    // 1. Login
    cy.visit('/login');
    cy.get('input[name="email"]').type('user@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    // 2. Go to settings
    cy.visit('/settings');
    cy.contains('button', 'Enable Two-Factor Authentication').click();

    // 3. Complete setup
    cy.contains('Next').click();
    cy.get('img[alt="MFA QR Code"]').should('be.visible');
    
    // 4. Enter code (use test authenticator)
    cy.get('input[placeholder="000000"]').type('123456');
    cy.contains('Verify').click();

    // 5. Save backup codes
    cy.contains('I\'ve saved my backup codes').click();
    cy.contains('Setup Complete').should('be.visible');
  });
});
```

## Error Handling

### Common Error Scenarios

**1. Invalid Code**
```typescript
// Backend response
{ "detail": "Invalid verification code", "error_code": "INVALID_CODE" }

// Frontend handling
if (err.error_code === 'INVALID_CODE') {
  setError('The code you entered is invalid. Please try again.');
}
```

**2. Too Many Attempts**
```typescript
// Backend response
{ "detail": "Too many verification attempts. Try again in 15 minutes.", "retry_after": 900 }

// Frontend handling
if (err.error_code === 'TOO_MANY_ATTEMPTS') {
  setError(`Too many attempts. Please wait 15 minutes before trying again.`);
  setCodeInputDisabled(true);
}
```

**3. Expired Temp Token**
```typescript
// If MFA verification takes too long, temp token might expire
// Redirect to login
if (err.status === 401 && tempToken) {
  onCancel?.();
}
```

## Customization

### Change QR Code Colors

In `MFASetup.tsx`:
```typescript
// Modify backend request to include styling
const setupData = await fetch('/api/v1/mfa/setup?color=blue', {
  // ...
});
```

### Custom Backup Code Layout

In `MFASettings.tsx`, modify the backup codes grid:
```typescript
<div className="grid grid-cols-3 gap-2">  // Change from grid-cols-2
  {backupCodes.map((code) => (...))}
</div>
```

### Add Authenticator App Suggestions

In `MFASetup.tsx`, add step 2.5:
```typescript
<div className="mt-4 text-sm text-gray-600">
  <p className="font-semibold mb-2">Recommended authenticator apps:</p>
  <ul className="list-disc list-inside space-y-1">
    <li>Google Authenticator</li>
    <li>Authy</li>
    <li>Microsoft Authenticator</li>
    <li>1Password</li>
  </ul>
</div>
```

## Performance Optimization

### Lazy Load MFA Components

```typescript
import dynamic from 'next/dynamic';

const MFASettings = dynamic(() => import('@/components/MFASettings'), {
  loading: () => <div>Loading MFA settings...</div>,
  ssr: false
});
```

### Memoize Expensive Computations

```typescript
const TrustedDevices = React.memo(({ onRefresh }: TrustedDevicesProps) => {
  // Component implementation
});

export default TrustedDevices;
```

## Debugging

### Enable Debug Logging

```typescript
// In components, add debug flag
const DEBUG = process.env.NODE_ENV === 'development';

if (DEBUG) {
  console.log('MFA Status:', mfaStatus);
  console.log('Devices:', devices);
}
```

### Test with Mock API Responses

```typescript
// Mock for development/testing
const mockMFAStatus = {
  mfa_enabled: true,
  setup_date: '2024-01-15',
  backup_codes_count: 8,
  trusted_devices_count: 2
};
```

## Security Best Practices

1. **Never Store Secrets Client-Side**
   - QR codes and secrets should only be displayed temporarily during setup
   - Never save TOTP secrets in localStorage or state

2. **Use HTTPS Only**
   - MFA endpoints must be served over HTTPS
   - Device trust tokens should be HttpOnly cookies when possible

3. **Validate on Both Sides**
   - Frontend validation for UX
   - Backend validation for security

4. **Rate Limiting**
   - Backend should rate-limit verification attempts
   - Prevent brute force attacks

5. **Session Management**
   - Clear tokens on logout
   - Refresh tokens periodically
   - Verify token expiration before API calls

## Troubleshooting

### QR Code Not Displaying

```typescript
// Check if fetch succeeded
if (!setupData.qr_code) {
  setError('Failed to generate QR code');
  // Show manual entry option
}
```

### MFA Verification Loops

Ensure `tempToken` is properly cleared:
```typescript
const handleSuccess = () => {
  localStorage.setItem('access_token', data.access_token);
  setTempToken(''); // Clear temp token
  onSuccess?.();
};
```

### Device Trust Not Working

Verify backend is:
1. Extracting device identifier (user agent, fingerprint)
2. Storing trust duration (30 days)
3. Checking device on each login

## Migration Path

If users already have MFA enabled:

1. Add migration script to check existing MFA status
2. Show setup prompt only for new users
3. Allow users to opt-in to migrate to new setup if needed

```typescript
// Check if MFA already exists
const mfaExists = await checkMFAStatus();
if (!mfaExists) {
  showMFASetupPrompt();
}
```

## Summary

- ✅ 4 React components created and ready to integrate
- ✅ All API endpoints documented
- ✅ State management patterns provided
- ✅ Error handling examples included
- ✅ Security best practices documented
- ✅ Testing strategies outlined

**Next Steps:**
1. Update backend auth endpoints to support MFA flow
2. Integrate MFAVerify into login page
3. Add MFASettings to settings/profile page
4. Test end-to-end flow
5. Deploy and monitor usage

