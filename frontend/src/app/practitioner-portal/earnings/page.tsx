'use client'

import { useEffect, useState } from 'react'
import { AuthGuard } from '@/components/auth-guard'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'
import { useI18n } from '@/lib/i18n'
import EarningsChart from '@/components/practitioner/EarningsChart'

interface Earnings {
  total_earnings: number
  earnings_this_month: number
  earnings_this_year: number
  pending_amount: number
  completed_sessions: number
  average_session_value: number
}

function EarningsContent() {
  const { showToast } = useToast()
  const { t } = useI18n()
  const [data, setData] = useState<Earnings | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await apiClient.get<Earnings>('/api/v1/practitioner/analytics/earnings')
        setData(res)
      } catch (error) {
        const msg = error instanceof Error ? error.message : 'Failed to load earnings'
        showToast(msg, 'error')
      }
    }
    load()
  }, [showToast])

  if (!data) {
    return <div className="min-h-screen bg-slate-950 p-6 text-slate-200">{t('practitioner_loading_earnings', 'Loading earnings...')}</div>
  }

  return (
    <div className="min-h-screen bg-slate-950 p-4 md:p-8">
      <div className="mx-auto max-w-4xl space-y-4">
        <h1 className="text-3xl font-bold text-white">{t('practitioner_earnings_title', 'Earnings')}</h1>
        <EarningsChart
          total={data.total_earnings}
          month={data.earnings_this_month}
          year={data.earnings_this_year}
          pending={data.pending_amount}
        />
        <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-5 text-slate-200">
          <p>{t('practitioner_completed_sessions', 'Completed Sessions')}: {data.completed_sessions}</p>
          <p>{t('practitioner_avg_session_value', 'Average Session Value')}: Rs. {data.average_session_value.toFixed(2)}</p>
        </div>
      </div>
    </div>
  )
}

export default function EarningsPage() {
  return (
    <AuthGuard>
      <EarningsContent />
    </AuthGuard>
  )
}
