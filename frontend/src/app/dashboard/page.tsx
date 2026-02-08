'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Calendar, Clock, Video, Phone, MessageCircle } from 'lucide-react'
import BackButton from '@/components/BackButton'
import { AuthGuard } from '@/components/auth-guard'
import { useAuth } from '@/lib/auth-context'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'

interface Booking {
  id: number
  guru_id: number
  guru_name: string
  booking_date: string
  time_slot: string
  duration_minutes: number
  session_type: string
  status: string
  payment_status: string
  payment_amount: number
  meeting_link: string | null
  created_at: string
}

function DashboardContent() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const router = useRouter()

  const [bookings, setBookings] = useState<Booking[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchBookings = async () => {
      try {
        const data = await apiClient.get<Booking[]>('/api/v1/guru-booking/bookings')
        setBookings(data)
      } catch (err) {
        console.error('Error fetching bookings:', err)
        showToast('Failed to load bookings. Please try again.', 'error')
      } finally {
        setLoading(false)
      }
    }

    fetchBookings()
  }, [showToast])

  const now = new Date()
  const upcoming = bookings
    .filter((b) => {
      const date = new Date(b.booking_date)
      return (
        date >= now &&
        (b.status === 'pending' || b.status === 'confirmed')
      )
    })
    .sort(
      (a, b) =>
        new Date(a.booking_date).getTime() -
        new Date(b.booking_date).getTime(),
    )

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-slate-300">Loading your dashboard...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-purple-900 to-slate-900 p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        <BackButton />

        <div className="mt-6 mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">Your Upcoming Sessions</h1>
          <p className="text-slate-300">
            Track your confirmed and pending consultations with YatinVeda gurus.
          </p>
        </div>

        {upcoming.length === 0 ? (
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-8 text-center">
            <p className="text-slate-300 mb-4">You don&apos;t have any upcoming sessions yet.</p>
            <a
              href="/book-appointment-new"
              className="inline-block bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold px-6 py-3 rounded-xl hover:shadow-lg transition"
            >
              Book Your First Session
            </a>
          </div>
        ) : (
          <div className="space-y-4">
            {upcoming.map((booking) => {
              const date = new Date(booking.booking_date)
              const isConfirmed = booking.status === 'confirmed'
              const isPaid = booking.payment_status === 'paid'

              return (
                <div
                  key={booking.id}
                  className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4"
                >
                  <div>
                    <h2 className="text-xl font-semibold text-white mb-1">
                      {booking.guru_name}
                    </h2>
                    <p className="text-slate-400 text-sm mb-2">
                      Session ID #{booking.id} • {booking.session_type.replace('_', ' ')}
                    </p>
                    <div className="flex flex-wrap gap-3 text-sm text-slate-300">
                      <span className="inline-flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        {date.toLocaleDateString()}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {booking.time_slot}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        {booking.session_type === 'video_call' && <Video className="w-4 h-4" />}
                        {booking.session_type === 'audio_call' && <Phone className="w-4 h-4" />}
                        {booking.session_type === 'chat' && <MessageCircle className="w-4 h-4" />}
                        {booking.session_type.replace('_', ' ')}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        ₹{booking.payment_amount} • {booking.duration_minutes} min
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col items-start md:items-end gap-2">
                    <div className="flex flex-wrap gap-2">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          isConfirmed
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-yellow-500/20 text-yellow-400'
                        }`}
                      >
                        {booking.status.toUpperCase()}
                      </span>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          isPaid
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-orange-500/20 text-orange-400'
                        }`}
                      >
                        {isPaid ? 'PAID' : 'PAYMENT PENDING'}
                      </span>
                    </div>

                    {isPaid && booking.meeting_link && (
                      <a
                        href={booking.meeting_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-block bg-gradient-to-r from-blue-500 to-purple-500 text-white text-sm font-semibold px-4 py-2 rounded-xl hover:shadow-lg transition"
                      >
                        Join Session
                      </a>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <AuthGuard requiredRole="user">
      <DashboardContent />
    </AuthGuard>
  )
}
