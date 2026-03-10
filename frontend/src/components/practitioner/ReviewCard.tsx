import React from 'react'
import { useI18n } from '@/lib/i18n'

interface ReviewCardProps {
  clientName: string
  rating: number
  reviewText: string
  createdAt: string
}

export default function ReviewCard({ clientName, rating, reviewText, createdAt }: ReviewCardProps) {
  const { t } = useI18n()
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
      <div className="flex items-center justify-between">
        <p className="font-medium text-white">{clientName}</p>
        <p className="text-sm text-amber-300">{rating}/5</p>
      </div>
      <p className="mt-2 text-sm text-slate-300">{reviewText || t('review_no_written_feedback', 'No written feedback.')}</p>
      <p className="mt-2 text-xs text-slate-400">{new Date(createdAt).toLocaleDateString()}</p>
    </div>
  )
}
