'use client'

import { useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'

interface BackButtonProps {
  href?: string
  className?: string
}

export default function BackButton({ href, className = 'mb-6' }: BackButtonProps) {
  const router = useRouter()

  const handleClick = () => {
    if (href) {
      router.push(href)
    } else {
      router.back()
    }
  }

  return (
    <button
      onClick={handleClick}
      className={`flex items-center gap-2 text-white hover:text-blue-400 transition-colors ${className}`}
    >
      <ArrowLeft className="w-5 h-5" />
      <span>Back</span>
    </button>
  )
}
