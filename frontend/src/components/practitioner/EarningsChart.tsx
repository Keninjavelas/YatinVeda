import React from 'react'
import { useI18n } from '@/lib/i18n'

interface EarningsChartProps {
  total: number
  month: number
  year: number
  pending: number
}

export default function EarningsChart({ total, month, year, pending }: EarningsChartProps) {
  const { t } = useI18n()
  const max = Math.max(total, month, year, pending, 1)
  const bars = [
    { label: t('earnings_total', 'Total'), value: total, color: 'bg-indigo-500' },
    { label: t('earnings_this_month', 'This Month'), value: month, color: 'bg-emerald-500' },
    { label: t('earnings_this_year', 'This Year'), value: year, color: 'bg-amber-500' },
    { label: t('earnings_pending', 'Pending'), value: pending, color: 'bg-rose-500' },
  ]

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-5">
      <h3 className="text-lg font-semibold text-white">{t('earnings_snapshot', 'Earnings Snapshot')}</h3>
      <div className="mt-4 space-y-3">
        {bars.map((bar) => (
          <div key={bar.label}>
            <div className="mb-1 flex items-center justify-between text-sm text-slate-300">
              <span>{bar.label}</span>
              <span>Rs. {bar.value.toFixed(2)}</span>
            </div>
            <div className="h-2 rounded bg-slate-700">
              <div className={`h-2 rounded ${bar.color}`} style={{ width: `${(bar.value / max) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
