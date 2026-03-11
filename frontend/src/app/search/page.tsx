'use client'

import { useState, useEffect, useCallback } from 'react'
import { Search as SearchIcon, Filter, X, Loader2, ChevronDown, Star } from 'lucide-react'
import BackButton from '@/components/BackButton'
import { AuthGuard } from '@/components/auth-guard'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'
import Link from 'next/link'

interface SearchResult {
  id: string
  type: 'practitioner' | 'article' | 'remedy' | 'community_post'
  title: string
  description: string
  score: number
  highlight?: string
}

interface SearchResponse {
  results: SearchResult[]
  total: number
  query: string
  suggestions?: string[]
}

const CATEGORIES = [
  { value: '', label: 'All' },
  { value: 'practitioner', label: 'Practitioners' },
  { value: 'article', label: 'Articles' },
  { value: 'remedy', label: 'Remedies' },
  { value: 'community_post', label: 'Community' },
]

export default function SearchPage() {
  const { showToast } = useToast()
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 2) { setSuggestions([]); return }
    try {
      const data = await apiClient.get(`/search/autocomplete?q=${encodeURIComponent(q)}`)
      setSuggestions(data.suggestions || [])
    } catch {
      setSuggestions([])
    }
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => fetchSuggestions(query), 300)
    return () => clearTimeout(timer)
  }, [query, fetchSuggestions])

  const handleSearch = async (searchQuery?: string) => {
    const q = searchQuery || query
    if (!q.trim()) return
    setLoading(true)
    setSearched(true)
    setSuggestions([])
    try {
      const params = new URLSearchParams({ q: q.trim() })
      if (category) params.set('type', category)
      const data: SearchResponse = await apiClient.get(`/search/global?${params}`)
      setResults(data.results || [])
      setTotal(data.total || 0)
    } catch {
      showToast('Search failed. Please try again.', 'error')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const typeColors: Record<string, string> = {
    practitioner: 'bg-indigo-500/20 text-indigo-400',
    article: 'bg-emerald-500/20 text-emerald-400',
    remedy: 'bg-amber-500/20 text-amber-400',
    community_post: 'bg-sky-500/20 text-sky-400',
  }

  return (
    <AuthGuard requiredRole="user">
      <div className="min-h-screen bg-slate-950 p-4 md:p-8">
        <div className="max-w-3xl mx-auto">
          <BackButton />
          <h1 className="text-2xl md:text-3xl font-bold text-white mt-4 mb-6">Search</h1>

          {/* Search Bar */}
          <div className="relative">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Search practitioners, articles, remedies..."
                  className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                {query && (
                  <button onClick={() => { setQuery(''); setSuggestions([]) }} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
              <button
                onClick={() => handleSearch()}
                disabled={loading || !query.trim()}
                className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Search'}
              </button>
            </div>

            {/* Autocomplete */}
            {suggestions.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow-xl">
                {suggestions.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => { setQuery(s); handleSearch(s) }}
                    className="w-full px-4 py-2 text-left text-slate-300 hover:bg-slate-700 transition"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Category Filter */}
          <div className="flex gap-2 mt-4 flex-wrap">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.value}
                onClick={() => setCategory(cat.value)}
                className={`px-3 py-1.5 rounded-lg text-sm transition ${
                  category === cat.value
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {/* Results */}
          <div className="mt-6 space-y-3">
            {loading && (
              <div className="flex justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
              </div>
            )}

            {!loading && searched && results.length === 0 && (
              <div className="text-center py-12 text-slate-400">
                <SearchIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No results found for &ldquo;{query}&rdquo;</p>
              </div>
            )}

            {!loading && results.length > 0 && (
              <>
                <p className="text-sm text-slate-400">{total} result{total !== 1 ? 's' : ''} found</p>
                {results.map((r) => (
                  <div key={r.id} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 hover:border-slate-600 transition">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${typeColors[r.type] || 'bg-slate-700 text-slate-300'}`}>
                            {r.type.replace('_', ' ')}
                          </span>
                        </div>
                        <h3 className="text-white font-medium truncate">{r.title}</h3>
                        <p className="text-slate-400 text-sm mt-1 line-clamp-2">{r.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </>
            )}

            {!loading && !searched && (
              <div className="text-center py-12 text-slate-400">
                <SearchIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Search across practitioners, articles, remedies, and community posts</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </AuthGuard>
  )
}
