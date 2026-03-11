# YatinVeda Mobile App

React Native mobile application for the YatinVeda Vedic Astrology platform.

## Prerequisites

- Node.js 18+
- React Native CLI or Expo CLI
- For iOS: macOS with Xcode 15+
- For Android: Android Studio with SDK 34+

## Quick Start with Expo

```bash
cd mobile
npm install
npx expo start
```

## Project Structure

```
mobile/
├── App.tsx                 # Root component with navigation
├── app.json               # Expo configuration
├── package.json           # Dependencies
├── tsconfig.json          # TypeScript config
├── src/
│   ├── api/
│   │   └── client.ts      # API client for backend
│   ├── components/
│   │   ├── BookingCard.tsx
│   │   ├── ChartView.tsx
│   │   └── LoadingSpinner.tsx
│   ├── navigation/
│   │   └── AppNavigator.tsx
│   ├── screens/
│   │   ├── LoginScreen.tsx
│   │   ├── DashboardScreen.tsx
│   │   ├── ChartScreen.tsx
│   │   ├── ChatScreen.tsx
│   │   ├── CommunityScreen.tsx
│   │   ├── BookingScreen.tsx
│   │   ├── ProfileScreen.tsx
│   │   └── VideoConsultScreen.tsx
│   ├── store/
│   │   └── auth.ts        # Authentication state
│   └── utils/
│       └── storage.ts     # Secure token storage
```

## Core Dependencies

- `@react-navigation/native` - Navigation
- `@react-navigation/bottom-tabs` - Tab navigation
- `@react-navigation/stack` - Stack navigation
- `react-native-webrtc` - Video consultations
- `@react-native-async-storage/async-storage` - Local storage
- `expo-secure-store` - Secure token storage

## Building for Production

### Android
```bash
npx expo build:android
# or
npx eas build --platform android
```

### iOS
```bash
npx expo build:ios
# or
npx eas build --platform ios
```

## Environment Configuration

Create a `.env` file:
```
API_BASE_URL=https://your-yatinveda-backend.com
WS_BASE_URL=wss://your-yatinveda-backend.com
```
