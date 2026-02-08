import 'next-auth'

declare module 'next-auth' {
  interface Session {
    accessToken?: string
    user: {
      id: string
      email: string
      name: string
      image?: string | null
    }
  }

  interface User {
    id: string
    email: string
    name: string
    image?: string | null
    accessToken?: string
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    id?: string
    email?: string
    name?: string
    accessToken?: string
  }
}
