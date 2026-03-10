import React from 'react'
import { useI18n } from '@/lib/i18n'

interface BookingCardProps {
  id: number
  clientName: string
  bookingDate: string
  timeSlot: string
  status: string
  paymentAmount: number
  onAccept: (id: number) => void
  onDecline: (id: number) => void
}

export default function BookingCard({
  id,
  clientName,
  bookingDate,
  timeSlot,
  status,
  paymentAmount,
  onAccept,
  onDecline,
}: BookingCardProps) {
  const { t } = useI18n()
  const canAction = status === 'pending'

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-medium text-white">{clientName}</p>
          <p className="text-sm text-slate-300">{new Date(bookingDate).toLocaleDateString()} {t('booking_card_at', 'at')} {timeSlot}</p>
          <p className="text-sm text-emerald-300">Rs. {paymentAmount.toFixed(2)}</p>
        </div>
        <span className="rounded-full bg-slate-700 px-3 py-1 text-xs text-slate-200">{status}</span>
      </div>

      {canAction && (
        <div className="mt-3 flex gap-2">
          <button onClick={() => onAccept(id)} className="rounded-md bg-emerald-600 px-3 py-1 text-sm text-white">
            {t('booking_card_accept', 'Accept')}
          </button>
          <button onClick={() => onDecline(id)} className="rounded-md bg-rose-600 px-3 py-1 text-sm text-white">
            {t('booking_card_decline', 'Decline')}
          </button>
        </div>
      )}
    </div>
  )
}
