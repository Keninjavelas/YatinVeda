import { NextAuthOptions, User } from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email', placeholder: 'you@example.com' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null
        }

        // Authenticate with backend API
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
        
        try {
          // Backend login expects 'username' field; it accepts either username or email
          const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              username: credentials.email, // map email to username field for backend
              password: credentials.password
            })
          })

          if (!response.ok) {
            return null
          }

          const login = await response.json()

          // Fetch user profile using the returned access token to populate session details
          if (login?.access_token) {
            const profileRes = await fetch(`${API_BASE_URL}/api/v1/auth/profile`, {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${login.access_token}`
              }
            })

            if (profileRes.ok) {
              const profile = await profileRes.json()
              const user: User & { accessToken?: string } = {
                id: profile.username, // backend profile does not include id; use username as stable id
                email: profile.email,
                name: profile.full_name || profile.username,
                accessToken: login.access_token
              }
              return user
            }
          }

          return null
        } catch (error) {
          console.error('Auth error:', error)
          return null
        }
      }
    })
  ],
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  pages: {
    signIn: '/login',
    signOut: '/login',
    error: '/login',
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id
        token.email = user.email
        token.name = user.name
        // persist access token if available
        if ('accessToken' in user && (user as { accessToken?: string }).accessToken) {
          token.accessToken = (user as { accessToken: string }).accessToken
        }
      }
      return token
    },
    async session({ session, token }) {
      if (token && session.user) {
        session.user.id = token.id as string
        session.user.email = token.email as string
        session.user.name = token.name as string
        const maybeToken = token as unknown as { accessToken?: string }
        if (maybeToken.accessToken) {
          (session as { accessToken?: string }).accessToken = maybeToken.accessToken
        }
      }
      return session
    }
  },
  secret: process.env.NEXTAUTH_SECRET || 'development-secret-please-change-in-production'
}
