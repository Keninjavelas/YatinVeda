import React, { useState } from 'react'
import { useI18n } from '@/lib/i18n'

interface Slot {
  date: string
  start_time: string
  end_time: string
  is_available: boolean
}

interface AvailabilityCalendarProps {
  onSave: (slots: Slot[]) => Promise<void>
}

export default function AvailabilityCalendar({ onSave }: AvailabilityCalendarProps) {
  const { t } = useI18n()
  const [date, setDate] = useState('')
  const [startTime, setStartTime] = useState('09:00')
  const [endTime, setEndTime] = useState('10:00')
  const [slots, setSlots] = useState<Slot[]>([])

  const addSlot = () => {
    if (!date) return
    setSlots((prev) => [
      ...prev,
      { date, start_time: startTime, end_time: endTime, is_available: true },
    ])
  }

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-5">
      <h3 className="text-lg font-semibold text-white">{t('availability_planner_title', 'Availability Planner')}</h3>
      <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-4">
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100" />
        <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100" />
        <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100" />
        <button onClick={addSlot} className="rounded-md bg-indigo-600 px-3 py-2 text-white">{t('availability_add_slot', 'Add Slot')}</button>
      </div>

      <div className="mt-4 space-y-2">
        {slots.map((slot, idx) => (
          <div key={`${slot.date}-${idx}`} className="rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-200">
            {slot.date} | {slot.start_time} - {slot.end_time}
          </div>
        ))}
      </div>

      <button onClick={() => onSave(slots)} className="mt-4 rounded-md bg-emerald-600 px-4 py-2 text-white">
        {t('availability_save', 'Save Availability')}
      </button>
    </div>
  )
}
