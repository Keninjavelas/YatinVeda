'use client'

import { useEffect, useState } from 'react'
import { AuthGuard } from '@/components/auth-guard'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'
import { useI18n } from '@/lib/i18n'
import ReviewCard from '@/components/practitioner/ReviewCard'

interface Review {
  id: number
  client_name: string
  rating: number
  review_text: string
  created_at: string
}

interface ReviewsAnalytics {
  average_rating: number
  total_reviews: number
  recent_reviews: Review[]
}

function ReviewsContent() {
  const { showToast } = useToast()
  const { t } = useI18n()
  const [data, setData] = useState<ReviewsAnalytics | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await apiClient.get<ReviewsAnalytics>('/api/v1/practitioner/analytics/reviews')
        setData(res)
      } catch (error) {
        const msg = error instanceof Error ? error.message : 'Failed to load reviews'
        showToast(msg, 'error')
      }
    }
    load()
  }, [showToast])

  if (!data) {
    return <div className="min-h-screen bg-slate-950 p-6 text-slate-200">{t('practitioner_loading_reviews', 'Loading reviews...')}</div>
  }

  return (
    <div className="min-h-screen bg-slate-950 p-4 md:p-8">
      <div className="mx-auto max-w-5xl space-y-4">
        <h1 className="text-3xl font-bold text-white">{t('practitioner_reviews_title', 'Reviews')}</h1>
        <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-5 text-slate-200">
          <p>{t('practitioner_average_rating', 'Average Rating')}: {data.average_rating.toFixed(1)}</p>
          <p>{t('practitioner_total_reviews', 'Total Reviews')}: {data.total_reviews}</p>
        </div>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {data.recent_reviews.map((review) => (
            <ReviewCard
              key={review.id}
              clientName={review.client_name}
              rating={review.rating}
              reviewText={review.review_text}
              createdAt={review.created_at}
            />
          ))}
          {data.recent_reviews.length === 0 && (
            <p className="text-slate-300">{t('practitioner_no_reviews', 'No reviews available yet.')}</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ReviewsPage() {
  return (
    <AuthGuard>
      <ReviewsContent />
    </AuthGuard>
  )
}
