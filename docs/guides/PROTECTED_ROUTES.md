# Protected Routes Implementation Guide

## Overview

The YatinVeda frontend now has a complete protected routes system using:
- **AuthProvider** (`lib/auth-context.tsx`) - Global authentication state management
- **AuthGuard** (`components/auth-guard.tsx`) - Client-side route protection with automatic redirects
- **useAuth hook** - Access to auth state, tokens, and CSRF tokens throughout the app

## Architecture

### AuthProvider (AuthContext)
Manages:
- User state (profile data)
- Access token storage (sessionStorage)
- CSRF token storage (sessionStorage)
- Loading state during auth checks
- Login/logout functions
- Token refresh logic

**Location**: `frontend/src/lib/auth-context.tsx`

### AuthGuard Component
- Wraps protected page content
- Shows loading state while checking authentication
- Redirects to login if not authenticated
- Supports role-based access (user vs admin)
- Preserves callback URL for redirect after login

**Location**: `frontend/src/components/auth-guard.tsx`

### ProtectedRoute Component
- Alternative wrapper for protected content
- Similar to AuthGuard but shows error for unauthorized access
- Useful for showing access denied messages

**Location**: `frontend/src/components/protected-route.tsx`

---

## How to Protect a Page

### Step 1: Create Page Content Component
```tsx
// app/my-protected-page/page.tsx
'use client'

import { AuthGuard } from '@/components/auth-guard'
import { useAuth } from '@/lib/auth-context'

function MyPageContent() {
  const { user, accessToken, csrfToken } = useAuth()
  
  return (
    <div>
      <h1>Welcome, {user?.full_name}</h1>
      {/* Page content */}
    </div>
  )
}

// Step 2: Export with AuthGuard wrapper
export default function MyPage() {
  return (
    <AuthGuard requiredRole="user">
      <MyPageContent />
    </AuthGuard>
  )
}
```

### Step 2: Use AuthGuard for Admin Pages
```tsx
export default function AdminPage() {
  return (
    <AuthGuard requiredRole="admin">
      <AdminContent />
    </AuthGuard>
  )
}
```

---

## Protected Pages

### Currently Protected (✅)
- `/dashboard` - User dashboard with bookings
- `/admin` - Admin dashboard (admin-only)

### Need Protection
- `/profile` - User profile management
- `/wallet` - Wallet and payment history
- `/book-appointment` - Booking page
- `/community-feed` - Community features
- `/chat` - AI chat interface
- `/prescriptions` - Prescription management
- `/chart` - Chart management

### Public Pages (No Protection Needed)
- `/` - Home page
- `/login` - Login page
- `/signup` - Sign up page
- `/forgot-password` - Password reset
- `/consultants` - Browse consultants
- `/library` - Learning library
- `/compatibility` - Compatibility tool
- `/dasha` - Dasha calculator

---

## Using Auth in Components

### Access Auth State
```tsx
'use client'

import { useAuth } from '@/lib/auth-context'

export function MyComponent() {
  const { user, accessToken, csrfToken, isAuthenticated, isLoading } = useAuth()
  
  if (isLoading) {
    return <div>Loading...</div>
  }
  
  if (!isAuthenticated) {
    return <div>Please log in</div>
  }
  
  return <div>Welcome, {user?.full_name}</div>
}
```

### Making API Calls
```tsx
async function fetchData() {
  const { accessToken, csrfToken } = useAuth()
  
  const response = await fetch('/api/v1/some-endpoint', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'x-csrf-token': csrfToken || '',
      'Content-Type': 'application/json',
    },
    credentials: 'include', // For cookie-based refresh
    body: JSON.stringify({ /* data */ })
  })
  
  return response.json()
}
```

### Login from Custom Form
```tsx
'use client'

import { useAuth } from '@/lib/auth-context'
import { useState } from 'react'

export function LoginForm() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login(email, password)
      // User will be redirected automatically
    } catch (error) {
      console.error('Login failed:', error)
    }
  }
  
  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button type="submit">Login</button>
    </form>
  )
}
```

---

## Token Management

### CSRF Token Handling
The CSRF token is automatically extracted from the login response header (`x-csrf-token`) and stored in sessionStorage. It's used for:
- Protected POST/PATCH/DELETE requests
- Cookie-based refresh token operations

**Important**: Always send CSRF token on protected endpoints:
```tsx
const csrfToken = sessionStorage.getItem('csrf_token') || ''

fetch('/api/endpoint', {
  method: 'POST',
  headers: {
    'x-csrf-token': csrfToken,
  }
})
```

### Access Token Refresh
When access token expires:
1. The refresh endpoint is called with CSRF token
2. Backend rotates the refresh token (in secure httpOnly cookie)
3. New access token is issued
4. Frontend stores new access token and CSRF token
5. Request is automatically retried

This is handled by the API client but needs integration with the auth-context.

---

## Session Storage

Tokens are stored in `sessionStorage` (cleared on browser tab close):
- `access_token` - JWT access token
- `csrf_token` - CSRF token for protected endpoints
- `refresh_token` - Refresh token (also in httpOnly cookie)

**Security Notes**:
- sessionStorage is cleared when browser tab closes
- httpOnly cookies cannot be accessed by JavaScript (prevents XSS attacks on refresh token)
- CSRF token prevents CSRF attacks on protected endpoints
- In production, consider additional measures like CSP headers

---

## Updated Pages

### 1. Dashboard (`/app/dashboard/page.tsx`)
✅ Protected with AuthGuard
- Uses `useAuth()` for accessToken
- Fetches bookings from `/api/v1/guru-booking/bookings`
- Shows user's upcoming sessions

### 2. Admin (`/app/admin/page.tsx`)
✅ Protected with AuthGuard (admin-only)
- Requires `is_admin: true`
- Uses accessToken for admin operations
- Fetches users, stats, and system data

---

## Next Steps

### Pages to Update (Add AuthGuard)
1. `/profile` - User profile management
2. `/wallet` - Wallet operations
3. `/book-appointment` - Booking creation
4. `/community-feed` - Community posts and comments
5. `/chat` - AI chat interface
6. `/prescriptions` - View/download prescriptions
7. `/chart` - Birth chart management

### Features to Implement
1. Update API client to handle CSRF tokens automatically
2. Implement token refresh in API client
3. Add loading states to components
4. Add error boundaries and error handling
5. Implement notification/toast system for errors
6. Add proper logout functionality
7. Implement social features UI (community, chat)

### Testing
- Test protected route access without login (should redirect)
- Test admin-only pages with non-admin user (should show access denied)
- Test token expiration and refresh flow
- Test CSRF token validation
- Test logout and session cleanup

---

## File Structure

```
frontend/src/
├── lib/
│   └── auth-context.tsx          # AuthProvider and useAuth hook
├── components/
│   ├── auth-guard.tsx             # AuthGuard component
│   └── protected-route.tsx         # ProtectedRoute component
├── app/
│   ├── layout.tsx                 # Root layout with AuthProvider
│   ├── page.tsx                   # Home (public)
│   ├── login/page.tsx             # Login (public)
│   ├── dashboard/page.tsx         # Dashboard (protected)
│   ├── admin/page.tsx             # Admin (protected, admin-only)
│   └── [other pages]
```

---

## CSRF Token Flow

```
1. User submits login form
   POST /api/v1/auth/login
   
2. Backend responds with:
   - access_token (in body)
   - x-csrf-token (in response header)
   - refresh_token (in httpOnly cookie)
   
3. Frontend extracts:
   - access_token → stored in sessionStorage
   - x-csrf-token → stored in sessionStorage
   - refresh_token → automatically in cookies
   
4. For protected endpoints:
   POST /api/v1/protected-endpoint
   Headers:
   - Authorization: Bearer {access_token}
   - x-csrf-token: {csrf_token}
   
5. Token refresh:
   POST /api/v1/auth/refresh
   Headers:
   - x-csrf-token: {csrf_token}
   Body: (empty, refresh_token in cookie)
```

---

## Troubleshooting

### User not redirected to login
- Check AuthProvider is in root layout
- Verify `useAuth()` is called from 'use client' component
- Check browser console for errors

### CSRF token missing
- Verify token extracted after login
- Check sessionStorage in DevTools
- Ensure CSRF token sent on protected endpoints

### Protected route shows white screen
- Check browser console for errors
- Verify callback URL preservation
- Check if token is expired

### Token doesn't refresh
- Verify refresh endpoint implementation (backend)
- Check CSRF token is sent on refresh
- Check httpOnly cookie permissions

