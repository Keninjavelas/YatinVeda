'use client'

import { AuthGuard } from '@/components/auth-guard'
import { useToast } from '@/lib/toast-context'
import { apiClient } from '@/lib/api-client'
import { useI18n } from '@/lib/i18n'
import AvailabilityCalendar from '@/components/practitioner/AvailabilityCalendar'

function AvailabilityContent() {
  const { showToast } = useToast()
  const { t } = useI18n()

  const saveAvailability = async (slots: { date: string; start_time: string; end_time: string; is_available: boolean }[]) => {
    try {
      await apiClient.post('/api/v1/practitioner/availability/bulk', { slots, clear_existing: false })
      showToast(t('availability_save', 'Save Availability'), 'success')
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Failed to save availability'
      showToast(msg, 'error')
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 p-4 md:p-8">
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-4 text-3xl font-bold text-white">{t('practitioner_availability_title', 'Availability Management')}</h1>
        <AvailabilityCalendar onSave={saveAvailability} />
      </div>
    </div>
  )
}

export default function AvailabilityPage() {
  return (
    <AuthGuard>
      <AvailabilityContent />
    </AuthGuard>
  )
}
