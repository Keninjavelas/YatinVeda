'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { AuthGuard } from '@/components/auth-guard'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'
import { useI18n } from '@/lib/i18n'

interface TrendPoint {
  date: string
  new_users: number
  new_bookings: number
  completed_bookings: number
  gross_inr: number
  net_inr: number
}

interface AnalyticsPayload {
  period_days: number
  users: { total: number; new_in_period: number }
  practitioners: { total: number; verified: number }
  bookings: { total: number; in_period: number; completed_in_period: number; by_status: Record<string, number> }
  revenue: { gross_inr: number; refund_inr: number; net_inr: number; by_payment_status: Record<string, number> }
  daily_trends: TrendPoint[]
}

function AnalyticsContent() {
  const { showToast } = useToast()
  const { t } = useI18n()
  const [period, setPeriod] = useState(30)
  const [data, setData] = useState<AnalyticsPayload | null>(null)

  const load = useCallback(async () => {
    try {
      const res = await apiClient.get<AnalyticsPayload>(`/api/v1/admin/analytics?period_days=${period}`)
      setData(res)
    } catch (error) {
      const msg = error instanceof Error ? error.message : t('admin_loading_analytics', 'Failed to load analytics')
      showToast(msg, 'error')
    }
  }, [period, showToast, t])

  useEffect(() => {
    load()
  }, [load])

  const maxNet = Math.max(...(data?.daily_trends.map((p) => p.net_inr) ?? [1]), 1)

  return (
    <div className="min-h-screen bg-slate-950 p-4 md:p-8">
      <div className="mx-auto max-w-5xl space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-3xl font-bold text-white">{t('admin_analytics_title', 'Advanced Analytics')}</h1>
          <div className="flex gap-2">
            <select
              value={period}
              onChange={(e) => setPeriod(Number(e.target.value))}
              className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
            >
              <option value={7}>{t('period_last_7_days', 'Last 7 days')}</option>
              <option value={30}>{t('period_last_30_days', 'Last 30 days')}</option>
              <option value={90}>{t('period_last_90_days', 'Last 90 days')}</option>
              <option value={365}>{t('period_last_365_days', 'Last 365 days')}</option>
            </select>
            <Link href="/admin" className="rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-200">{t('common_back', 'Back')}</Link>
          </div>
        </div>

        {!data ? (
          <p className="text-slate-300">{t('admin_loading_analytics', 'Loading analytics...')}</p>
        ) : (
          <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 text-slate-200">
              <h2 className="text-lg font-semibold">{t('admin_users', 'Users')}</h2>
              <p>{t('common_total', 'Total')}: {data.users.total}</p>
              <p>{t('admin_new_in_period', 'New In Period')}: {data.users.new_in_period}</p>
            </div>
            <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 text-slate-200">
              <h2 className="text-lg font-semibold">{t('admin_practitioners', 'Practitioners')}</h2>
              <p>{t('common_total', 'Total')}: {data.practitioners.total}</p>
              <p>{t('admin_verified', 'Verified')}: {data.practitioners.verified}</p>
            </div>
            <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 text-slate-200">
              <h2 className="text-lg font-semibold">{t('admin_bookings', 'Bookings')}</h2>
              <p>{t('common_total', 'Total')}: {data.bookings.total}</p>
              <p>{t('admin_in_period', 'In Period')}: {data.bookings.in_period}</p>
              <p>{t('admin_completed_in_period', 'Completed In Period')}: {data.bookings.completed_in_period}</p>
            </div>
            <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 text-slate-200">
              <h2 className="text-lg font-semibold">{t('admin_revenue', 'Revenue')}</h2>
              <p>{t('admin_gross_inr', 'Gross (INR)')}: {data.revenue.gross_inr.toFixed(2)}</p>
              <p>{t('admin_refund_inr', 'Refunds (INR)')}: {data.revenue.refund_inr.toFixed(2)}</p>
              <p>{t('admin_net_inr', 'Net (INR)')}: {data.revenue.net_inr.toFixed(2)}</p>
            </div>
          </div>

          <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 text-slate-200">
            <h2 className="text-lg font-semibold">{t('admin_daily_trends', 'Daily Trends')}</h2>
            <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
              {data.daily_trends.slice(-10).map((point) => (
                <div key={point.date} className="rounded-md border border-slate-700 p-3">
                  <div className="mb-2 flex items-center justify-between text-xs text-slate-300">
                    <span>{new Date(point.date).toLocaleDateString()}</span>
                    <span>Net INR {point.net_inr.toFixed(2)}</span>
                  </div>
                  <div className="h-2 rounded bg-slate-700">
                    <div className="h-2 rounded bg-emerald-500" style={{ width: `${Math.max(2, (point.net_inr / maxNet) * 100)}%` }} />
                  </div>
                  <div className="mt-2 text-xs text-slate-300">
                    +{point.new_users} users, +{point.new_bookings} bookings, {point.completed_bookings} completed
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 text-slate-200">
              <h2 className="text-lg font-semibold">{t('admin_booking_status_breakdown', 'Booking Status Breakdown')}</h2>
              <div className="mt-3 space-y-2">
                {Object.entries(data.bookings.by_status).length === 0 && (
                  <p className="text-sm text-slate-400">{t('admin_no_breakdown_data', 'No breakdown data available for this period.')}</p>
                )}
                {Object.entries(data.bookings.by_status).map(([status, value]) => (
                  <div key={status} className="flex items-center justify-between rounded border border-slate-700 px-3 py-2 text-sm">
                    <span className="capitalize">{status}</span>
                    <span>{value}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 text-slate-200">
              <h2 className="text-lg font-semibold">{t('admin_payment_status_breakdown', 'Payment Status Breakdown')}</h2>
              <div className="mt-3 space-y-2">
                {Object.entries(data.revenue.by_payment_status).length === 0 && (
                  <p className="text-sm text-slate-400">{t('admin_no_breakdown_data', 'No breakdown data available for this period.')}</p>
                )}
                {Object.entries(data.revenue.by_payment_status).map(([status, value]) => (
                  <div key={status} className="flex items-center justify-between rounded border border-slate-700 px-3 py-2 text-sm">
                    <span className="capitalize">{status}</span>
                    <span>{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          </>
        )}
      </div>
    </div>
  )
}

export default function AnalyticsPage() {
  return (
    <AuthGuard requiredRole="admin">
      <AnalyticsContent />
    </AuthGuard>
  )
}
