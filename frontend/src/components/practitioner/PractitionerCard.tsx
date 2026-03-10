import React from 'react'

interface PractitionerCardProps {
  title: string
  verificationStatus: string
  rating: number
  sessions: number
  languages: string[]
  specializations: string[]
}

export default function PractitionerCard({
  title,
  verificationStatus,
  rating,
  sessions,
  languages,
  specializations,
}: PractitionerCardProps) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-white">{title || 'Practitioner Profile'}</h2>
        <span className="rounded-full bg-slate-700 px-3 py-1 text-xs text-slate-200">
          {verificationStatus}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
        <div>
          <p className="text-xs text-slate-400">Rating</p>
          <p className="text-white">{rating.toFixed(1)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400">Sessions</p>
          <p className="text-white">{sessions}</p>
        </div>
        <div className="col-span-2">
          <p className="text-xs text-slate-400">Languages</p>
          <p className="text-white">{languages.length ? languages.join(', ') : 'Not set'}</p>
        </div>
      </div>

      <div className="mt-4">
        <p className="text-xs text-slate-400">Specializations</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {specializations.length ? (
            specializations.map((s) => (
              <span key={s} className="rounded-md bg-indigo-500/20 px-2 py-1 text-xs text-indigo-200">
                {s}
              </span>
            ))
          ) : (
            <span className="text-sm text-slate-300">No specializations yet</span>
          )}
        </div>
      </div>
    </div>
  )
}
