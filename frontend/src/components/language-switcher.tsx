'use client'

import { useI18n } from '@/lib/i18n'

export default function LanguageSwitcher() {
  const { locale, setLocale } = useI18n()

  return (
    <select
      value={locale}
      onChange={(e) => setLocale(e.target.value as 'en' | 'hi')}
      className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200"
      aria-label="Language selector"
    >
      <option value="en">EN</option>
      <option value="hi">HI</option>
    </select>
  )
}
