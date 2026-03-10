'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { AuthGuard } from '@/components/auth-guard'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'

interface CertificateAlertItem {
  domain: string
  status: string
  expires_at: string | null
  days_until_expiry: number | null
  issuer: string | null
  needs_attention: boolean
}

function CertificateAlertsContent() {
  const { showToast } = useToast()
  const [items, setItems] = useState<CertificateAlertItem[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      const data = await apiClient.get<CertificateAlertItem[]>('/api/v1/admin/certificate-alerts')
      setItems(data)
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Failed to load certificate alerts'
      showToast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="min-h-screen bg-slate-950 p-4 md:p-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Certificate Alerts</h1>
            <p className="text-slate-300">Monitor SSL certificate expiry and renewal risk.</p>
          </div>
          <div className="flex gap-2">
            <button onClick={load} className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white">Refresh</button>
            <Link href="/admin" className="rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-200">Back to Admin</Link>
          </div>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-700 bg-slate-900/60">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-700 text-slate-300">
              <tr>
                <th className="px-4 py-3">Domain</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Expires</th>
                <th className="px-4 py-3">Days Left</th>
                <th className="px-4 py-3">Issuer</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td className="px-4 py-3 text-slate-400" colSpan={5}>Loading...</td>
                </tr>
              )}
              {!loading && items.length === 0 && (
                <tr>
                  <td className="px-4 py-3 text-slate-400" colSpan={5}>No certificate data available.</td>
                </tr>
              )}
              {!loading && items.map((item) => (
                <tr key={item.domain} className="border-b border-slate-800 last:border-b-0">
                  <td className="px-4 py-3 text-white">{item.domain}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-1 text-xs ${item.needs_attention ? 'bg-rose-600/20 text-rose-300' : 'bg-emerald-600/20 text-emerald-300'}`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-300">{item.expires_at ? new Date(item.expires_at).toLocaleString() : '-'}</td>
                  <td className="px-4 py-3 text-slate-300">{item.days_until_expiry ?? '-'}</td>
                  <td className="px-4 py-3 text-slate-400">{item.issuer || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default function CertificateAlertsPage() {
  return (
    <AuthGuard requiredRole="admin">
      <CertificateAlertsContent />
    </AuthGuard>
  )
}
