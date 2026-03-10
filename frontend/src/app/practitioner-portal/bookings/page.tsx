'use client'

import { useCallback, useEffect, useState } from 'react'
import { AuthGuard } from '@/components/auth-guard'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'
import { useI18n } from '@/lib/i18n'
import BookingCard from '@/components/practitioner/BookingCard'
import BookingFilters from '@/components/practitioner/BookingFilters'

interface Booking {
  id: number
  client_name: string
  booking_date: string
  time_slot: string
  status: string
  payment_amount: number
}

function BookingsContent() {
  const { showToast } = useToast()
  const { t } = useI18n()
  const [bookings, setBookings] = useState<Booking[]>([])
  const [statusFilter, setStatusFilter] = useState('')
  const [periodFilter, setPeriodFilter] = useState('upcoming')

  const load = useCallback(async () => {
    try {
      const data = await apiClient.get<Booking[]>(`/api/v1/practitioner/bookings?period=${periodFilter}${statusFilter ? `&status_filter=${statusFilter}` : ''}`)
      setBookings(data)
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Failed to load bookings'
      showToast(msg, 'error')
    }
  }, [periodFilter, statusFilter, showToast])

  useEffect(() => {
    load()
  }, [load])

  const action = async (id: number, a: 'accept' | 'decline') => {
    try {
      await apiClient.patch(`/api/v1/practitioner/bookings/${id}`, { action: a })
      showToast(`${t('common_booking', 'Booking')} ${a}ed`, 'success')
      load()
    } catch (error) {
      const msg = error instanceof Error ? error.message : `Failed to ${a} booking`
      showToast(msg, 'error')
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 p-4 md:p-8">
      <div className="mx-auto max-w-5xl">
        <h1 className="mb-4 text-3xl font-bold text-white">{t('practitioner_booking_title', 'Booking Management')}</h1>
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
              onAccept={(id) => action(id, 'accept')}
              onDecline={(id) => action(id, 'decline')}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function BookingsPage() {
  return (
    <AuthGuard>
      <BookingsContent />
    </AuthGuard>
  )
}
