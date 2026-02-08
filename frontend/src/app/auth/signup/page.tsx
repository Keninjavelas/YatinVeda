'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

// Legacy signup route: redirect to the main /signup page
export default function LegacySignUpRedirect() {
  const router = useRouter()

  useEffect(() => {
    router.replace('/signup')
  }, [router])

  return null
}
