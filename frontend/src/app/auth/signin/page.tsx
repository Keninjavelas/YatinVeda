'use client'

import { useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

export const dynamic = 'force-dynamic'

function SignInContent() {
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    const callback = searchParams.get('callbackUrl') || '/'
    const qs = callback ? `?callbackUrl=${encodeURIComponent(callback)}` : ''
    router.replace(`/login${qs}`)
  }, [router, searchParams])

  return null
}

export default function SignInPage() {
  return (
    <Suspense fallback={null}>
      <SignInContent />
    </Suspense>
  )
}
