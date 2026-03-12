# YatinVeda Mobile App

React Native (Expo) mobile application for the YatinVeda Vedic Astrology platform.  
Provides a native experience on iOS and Android with secure token storage, offline-ready navigation, and deep linking to the backend API.

> **Web users** can also install the web frontend as a Progressive Web App (PWA) — see `frontend/README.md` for details.

## Prerequisites

| Tool | Version |
|------|---------|
| Node.js | 18 + |
| Expo CLI | `npx expo` (bundled with SDK 51) |
| iOS | macOS + Xcode 15 + (simulator or device) |
| Android | Android Studio + SDK 34 + |

## Quick Start

```bash
cd mobile
npm install
npx expo start          # Opens Expo DevTools
# Press  i  for iOS simulator,  a  for Android emulator
```

To connect to a local backend, update `app.json → expo.extra.apiBaseUrl` or set the environment variable:

```bash
API_BASE_URL=http://192.168.x.x:8000 npx expo start
```

## Project Structure

```
mobile/
├── App.tsx                    # Root — wraps AppNavigator
├── app.json                   # Expo config (bundle IDs, splash, icons)
├── package.json
├── tsconfig.json
└── src/
    ├── api/
    │   └── client.ts          # Fetch wrapper + SecureStore token management + auto-refresh
    ├── navigation/
    │   └── AppNavigator.tsx   # Stack (Login → Home) + Bottom-tab navigator
    └── screens/
        ├── LoginScreen.tsx    # Email / password login
        ├── DashboardScreen.tsx
        ├── ChartScreen.tsx    # Birth chart generation
        ├── ChatScreen.tsx     # AI astrology chat
        ├── CommunityScreen.tsx
        └── ProfileScreen.tsx
```

## Key Libraries

| Package | Purpose |
|---------|---------|
| `expo` ~51.0 | Managed workflow runtime |
| `react-native` 0.74 | Core framework |
| `@react-navigation/native` | Navigation container |
| `@react-navigation/bottom-tabs` | 5-tab home layout (Dashboard · Chart · Chat · Community · Profile) |
| `@react-navigation/stack` | Auth → Home stack |
| `expo-secure-store` | Encrypted token storage (Keychain / Keystore) |
| `@react-native-async-storage/async-storage` | Non-sensitive local storage |

## Authentication Flow

1. User submits credentials on `LoginScreen`.
2. `api/client.ts` calls `POST /api/v1/auth/login` and stores the access + refresh tokens in `SecureStore`.
3. Every subsequent API call attaches `Authorization: Bearer <token>`.
4. On 401, the client automatically attempts a token refresh before retrying the original request.

## Building for Production

Use [EAS Build](https://docs.expo.dev/build/introduction/) (recommended):

```bash
# Install EAS CLI once
npm install -g eas-cli

# Android (APK / AAB)
eas build --platform android --profile production

# iOS (IPA)
eas build --platform ios --profile production
```

### Over-the-Air Updates

```bash
eas update --branch production --message "v1.x patch"
```

## Environment Configuration

Backend URL is configured in `app.json` under `expo.extra.apiBaseUrl`.  
For production, point this to your deployed API:

```jsonc
// app.json
{
  "expo": {
    "extra": {
      "apiBaseUrl": "https://api.yatinveda.com"
    }
  }
}
```

## Platform Strategy

YatinVeda supports **three** client surfaces:

| Surface | Stack | Install |
|---------|-------|---------|
| **Web** | Next.js 14 (PWA-enabled) | Visit site → browser "Install App" |
| **Android** | Expo / React Native | Google Play or EAS Build |
| **iOS** | Expo / React Native | App Store or TestFlight |

All three share the same backend API (`/api/v1/*`).
