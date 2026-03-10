'use client'

import { FormEvent, useState } from 'react'
import { AuthGuard } from '@/components/auth-guard'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'
import { useI18n } from '@/lib/i18n'

interface VideoSessionResponse {
  booking_id: number
  meeting_link: string
  session_type: string
  status: string
  payment_status: string
  scheduled_start_utc: string | null
  scheduled_end_utc: string | null
  join_window_opens_utc: string | null
  join_window_closes_utc: string | null
  lifecycle_state: 'scheduled' | 'join_window_open' | 'expired'
  can_join: boolean
  join_hint: string
}

function VideoConsultContent() {
  const { showToast } = useToast()
  const { t } = useI18n()
  const [bookingId, setBookingId] = useState('')
  const [session, setSession] = useState<VideoSessionResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const loadSession = async (e: FormEvent) => {
    e.preventDefault()
    if (!bookingId.trim()) return

    try {
      setLoading(true)
      const data = await apiClient.get<VideoSessionResponse>(`/api/v1/guru-booking/bookings/${bookingId}/video-session`)
      setSession(data)
    } catch (error) {
      const msg = error instanceof Error ? error.message : t('video_load_failed', 'Failed to load video session')
      showToast(msg, 'error')
      setSession(null)
    } finally {
      setLoading(false)
    }
  }

  const refreshMeetingLink = async () => {
    if (!session) return

    try {
      await apiClient.patch(`/api/v1/guru-booking/bookings/${session.booking_id}/refresh-meeting-link`, {})
      showToast(t('video_link_refreshed', 'Meeting link refreshed'), 'success')
      const data = await apiClient.get<VideoSessionResponse>(`/api/v1/guru-booking/bookings/${session.booking_id}/video-session`)
      setSession(data)
    } catch (error) {
      const msg = error instanceof Error ? error.message : t('video_refresh_failed', 'Failed to refresh meeting link')
      showToast(msg, 'error')
    }
  }

  const lifecycleHint = (lifecycleState: VideoSessionResponse['lifecycle_state']) => {
    if (lifecycleState === 'scheduled') return t('video_lifecycle_scheduled', 'Session not yet open. Join window starts 15 minutes before session time.')
    if (lifecycleState === 'expired') return t('video_lifecycle_expired', 'Join window has ended. You can refresh the link if your practitioner allows extension.')
    return t('video_lifecycle_open', 'Join window is open. You can enter the session now.')
  }

  return (
    <div className="min-h-screen bg-slate-950 p-4 md:p-8">
      <div className="mx-auto max-w-3xl space-y-5">
        <h1 className="text-3xl font-bold text-white">{t('video_consult_title', 'Video Consultation')}</h1>
        <p className="text-slate-300">{t('video_consult_subtitle', 'Enter your booking ID to generate or retrieve the secure meeting link.')}</p>

        <form onSubmit={loadSession} className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              value={bookingId}
              onChange={(e) => setBookingId(e.target.value)}
              placeholder={t('video_booking_id_placeholder', 'Booking ID')}
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
            />
            <button disabled={loading} className="rounded-md bg-indigo-600 px-4 py-2 text-white disabled:opacity-60" type="submit">
              {loading ? t('common_loading', 'Loading...') : t('video_get_session_link', 'Get Session Link')}
            </button>
          </div>
        </form>

        {session && (
          <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 text-slate-200">
            <p>{t('common_booking', 'Booking')}: {session.booking_id}</p>
            <p>{t('common_session_type', 'Session Type')}: {session.session_type}</p>
            <p>{t('common_status', 'Status')}: {session.status}</p>
            <p>{t('common_payment', 'Payment')}: {session.payment_status}</p>
            {session.join_window_opens_utc && (
              <p>Join Opens: {new Date(session.join_window_opens_utc).toLocaleString()}</p>
            )}
            {session.join_window_closes_utc && (
              <p>Join Closes: {new Date(session.join_window_closes_utc).toLocaleString()}</p>
            )}
            <p className="mt-2 text-sm text-amber-300">{lifecycleHint(session.lifecycle_state)}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <a
                href={session.meeting_link}
                target="_blank"
                rel="noreferrer"
                className={`inline-block rounded-md px-4 py-2 text-white ${session.can_join ? 'bg-emerald-600' : 'pointer-events-none bg-slate-600 opacity-60'}`}
              >
                {t('video_join_session', 'Join Video Session')}
              </a>
              {session.lifecycle_state === 'expired' && (
                <button
                  type="button"
                  onClick={refreshMeetingLink}
                  className="rounded-md bg-indigo-600 px-4 py-2 text-white"
                >
                  {t('video_refresh_link', 'Refresh Session Link')}
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function VideoConsultPage() {
  return (
    <AuthGuard>
      <VideoConsultContent />
    </AuthGuard>
  )
}
