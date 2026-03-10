import React from 'react'
import { useI18n } from '@/lib/i18n'

interface BookingFiltersProps {
  status: string
  period: string
  onStatusChange: (value: string) => void
  onPeriodChange: (value: string) => void
}

export default function BookingFilters({ status, period, onStatusChange, onPeriodChange }: BookingFiltersProps) {
  const { t } = useI18n()

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      <select
        value={status}
        onChange={(e) => onStatusChange(e.target.value)}
        className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
      >
        <option value="">{t('booking_filter_all_statuses', 'All statuses')}</option>
        <option value="pending">{t('booking_filter_pending', 'Pending')}</option>
        <option value="confirmed">{t('booking_filter_confirmed', 'Confirmed')}</option>
        <option value="completed">{t('booking_filter_completed', 'Completed')}</option>
        <option value="cancelled">{t('booking_filter_cancelled', 'Cancelled')}</option>
      </select>

      <select
        value={period}
        onChange={(e) => onPeriodChange(e.target.value)}
        className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
      >
        <option value="upcoming">{t('booking_filter_upcoming', 'Upcoming')}</option>
        <option value="past">{t('booking_filter_past', 'Past')}</option>
        <option value="all">{t('booking_filter_all', 'All')}</option>
      </select>
    </div>
  )
}
