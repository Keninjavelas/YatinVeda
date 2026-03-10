'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { AuthGuard } from '@/components/auth-guard'
import { useAuth } from '@/lib/auth-context'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'
import { PractitionerSocketClient } from '@/lib/websocket'
import { useI18n } from '@/lib/i18n'
import PractitionerCard from '@/components/practitioner/PractitionerCard'
import BookingCard from '@/components/practitioner/BookingCard'
import EarningsChart from '@/components/practitioner/EarningsChart'
import ReviewCard from '@/components/practitioner/ReviewCard'
import BookingFilters from '@/components/practitioner/BookingFilters'

interface PractitionerProfile {
  guru_id: number
  user_id: number
  professional_title: string | null
  bio: string | null
  specializations: string[]
  experience_years: number
  languages: string[]
  price_per_hour: number
  verification_status: string
  verification_tier: string
  rating: number
}

interface PractitionerBooking {
  id: number
  client_name: string
  client_email: string
  booking_date: string
  time_slot: string
  duration_minutes: number
  session_type: string
  status: string
  payment_status: string
  payment_amount: number
}

interface Earnings {
  total_earnings: number
  earnings_this_month: number
  earnings_this_year: number
  pending_amount: number
  completed_sessions: number
  average_session_value: number
}

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

function PractitionerPortalContent() {
  const { user, accessToken } = useAuth()
  const { showToast } = useToast()
  const { t } = useI18n()

  const [profile, setProfile] = useState<PractitionerProfile | null>(null)
  const [bookings, setBookings] = useState<PractitionerBooking[]>([])
  const [earnings, setEarnings] = useState<Earnings | null>(null)
  const [reviews, setReviews] = useState<ReviewsAnalytics | null>(null)
  const [loading, setLoading] = useState(true)

  const [statusFilter, setStatusFilter] = useState('')
  const [periodFilter, setPeriodFilter] = useState('upcoming')

  const isPractitioner = useMemo(() => user?.role === 'practitioner', [user?.role])

  const loadPortalData = useCallback(async () => {
    try {
      setLoading(true)

      const [profileData, bookingsData, earningsData, reviewsData] = await Promise.all([
        apiClient.get<PractitionerProfile>('/api/v1/practitioner/profile'),
        apiClient.get<PractitionerBooking[]>(`/api/v1/practitioner/bookings?period=${periodFilter}${statusFilter ? `&status_filter=${statusFilter}` : ''}`),
        apiClient.get<Earnings>('/api/v1/practitioner/analytics/earnings'),
        apiClient.get<ReviewsAnalytics>('/api/v1/practitioner/analytics/reviews'),
      ])

      setProfile(profileData)
      setBookings(bookingsData)
      setEarnings(earningsData)
      setReviews(reviewsData)
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Failed to load practitioner portal'
      showToast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }, [periodFilter, statusFilter, showToast])

  useEffect(() => {
    if (isPractitioner) {
      loadPortalData()
    }
  }, [isPractitioner, loadPortalData])

  useEffect(() => {
    if (!isPractitioner || !accessToken) return

    const socket = new PractitionerSocketClient(accessToken, (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'new_booking' || data.type === 'booking_update') {
          loadPortalData()
          showToast('Live update received', 'info')
        }
      } catch {
        // Ignore non-JSON or unexpected payloads.
      }
    })

    socket.connect()
    return () => socket.close()
  }, [isPractitioner, accessToken, loadPortalData, showToast])

  const handleBookingAction = async (bookingId: number, action: 'accept' | 'decline') => {
    try {
      await apiClient.patch(`/api/v1/practitioner/bookings/${bookingId}`, { action })
      showToast(`Booking ${action}ed`, 'success')
      loadPortalData()
    } catch (error) {
      const msg = error instanceof Error ? error.message : `Failed to ${action} booking`
      showToast(msg, 'error')
    }
  }

  if (!isPractitioner) {
    return (
      <div className="min-h-screen bg-slate-950 p-6 text-slate-100">
        <div className="mx-auto max-w-3xl rounded-xl border border-slate-700 bg-slate-900/60 p-6">
          <h1 className="text-2xl font-bold">Practitioner Portal</h1>
          <p className="mt-2 text-slate-300">This portal is available only for practitioner accounts.</p>
        </div>
      </div>
    )
  }

  if (loading || !profile || !earnings || !reviews) {
    return (
      <div className="min-h-screen bg-slate-950 p-6">
        <p className="text-slate-300">Loading practitioner portal...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 p-4 md:p-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white">{t('practitioner_portal_title', 'Practitioner Portal')}</h1>
          <p className="mt-1 text-slate-300">{t('practitioner_portal_subtitle', 'Manage your sessions, earnings, and professional profile.')}</p>
          <div className="mt-3 flex flex-wrap gap-2 text-sm">
            <Link href="/practitioner-portal/bookings" className="rounded-md border border-slate-700 px-3 py-1 text-slate-200 hover:bg-slate-800">Bookings</Link>
            <Link href="/practitioner-portal/availability" className="rounded-md border border-slate-700 px-3 py-1 text-slate-200 hover:bg-slate-800">Availability</Link>
            <Link href="/practitioner-portal/earnings" className="rounded-md border border-slate-700 px-3 py-1 text-slate-200 hover:bg-slate-800">Earnings</Link>
            <Link href="/practitioner-portal/reviews" className="rounded-md border border-slate-700 px-3 py-1 text-slate-200 hover:bg-slate-800">Reviews</Link>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <PractitionerCard
              title={profile.professional_title || 'Practitioner'}
              verificationStatus={profile.verification_status}
              rating={reviews.average_rating || profile.rating || 0}
              sessions={earnings.completed_sessions}
              languages={profile.languages || []}
              specializations={profile.specializations || []}
            />
          </div>
          <div>
            <EarningsChart
              total={earnings.total_earnings}
              month={earnings.earnings_this_month}
              year={earnings.earnings_this_year}
              pending={earnings.pending_amount}
            />
          </div>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-5">
          <h2 className="mb-4 text-xl font-semibold text-white">Bookings</h2>
          <BookingFilters
            status={statusFilter}
            period={periodFilter}
            onStatusChange={setStatusFilter}
            onPeriodChange={setPeriodFilter}
          />
          <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
            {bookings.map((b) => (
              <BookingCard
                key={b.id}
                id={b.id}
                clientName={b.client_name}
                bookingDate={b.booking_date}
                timeSlot={b.time_slot}
                status={b.status}
                paymentAmount={b.payment_amount}
                onAccept={(id: number) => handleBookingAction(id, 'accept')}
                onDecline={(id: number) => handleBookingAction(id, 'decline')}
              />
            ))}
            {bookings.length === 0 && <p className="text-slate-300">No bookings found for selected filters.</p>}
          </div>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-5">
          <h2 className="mb-4 text-xl font-semibold text-white">Recent Reviews</h2>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {reviews.recent_reviews.map((review) => (
              <ReviewCard
                key={review.id}
                clientName={review.client_name}
                rating={review.rating}
                reviewText={review.review_text}
                createdAt={review.created_at}
              />
            ))}
            {reviews.recent_reviews.length === 0 && (
              <p className="text-slate-300">No reviews available yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function PractitionerPortalPage() {
  return (
    <AuthGuard>
      <PractitionerPortalContent />
    </AuthGuard>
  )
}
