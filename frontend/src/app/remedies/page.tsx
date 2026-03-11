'use client'

import { useState, useEffect } from 'react'
import { Sparkles, Leaf, Gem, Sun, Moon, Star, Loader2, ChevronRight, CheckCircle } from 'lucide-react'
import BackButton from '@/components/BackButton'
import { AuthGuard } from '@/components/auth-guard'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'

interface Remedy {
  id: string
  name: string
  type: string
  planet: string
  description: string
  instructions: string[]
  difficulty: 'easy' | 'medium' | 'advanced'
  effectiveness: number
}

interface RemedyCategory {
  name: string
  count: number
  icon: string
}

const difficultyColors = {
  easy: 'bg-emerald-500/20 text-emerald-400',
  medium: 'bg-amber-500/20 text-amber-400',
  advanced: 'bg-rose-500/20 text-rose-400',
}

const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']

export default function RemediesPage() {
  const { showToast } = useToast()
  const [remedies, setRemedies] = useState<Remedy[]>([])
  const [categories, setCategories] = useState<RemedyCategory[]>([])
  const [selectedPlanet, setSelectedPlanet] = useState('')
  const [loading, setLoading] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [recommendLoading, setRecommendLoading] = useState(false)
  const [recommended, setRecommended] = useState<Remedy[]>([])

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const data = await apiClient.get('/remedies/categories')
        setCategories(data.categories || [])
      } catch {}
    }
    fetchCategories()
  }, [])

  const fetchByPlanet = async (planet: string) => {
    setSelectedPlanet(planet)
    setLoading(true)
    try {
      const data = await apiClient.get(`/remedies/planets/${planet.toLowerCase()}`)
      setRemedies(data.remedies || [])
    } catch {
      showToast('Failed to load remedies', 'error')
      setRemedies([])
    } finally {
      setLoading(false)
    }
  }

  const getRecommendations = async () => {
    setRecommendLoading(true)
    try {
      const data = await apiClient.post('/remedies/recommend', {})
      setRecommended(data.remedies || [])
    } catch {
      showToast('Could not fetch recommendations', 'error')
    } finally {
      setRecommendLoading(false)
    }
  }

  return (
    <AuthGuard requiredRole="user">
      <div className="min-h-screen bg-slate-950 p-4 md:p-8">
        <div className="max-w-4xl mx-auto">
          <BackButton />
          <div className="flex items-center gap-3 mt-4 mb-6">
            <Sparkles className="w-7 h-7 text-amber-400" />
            <h1 className="text-2xl md:text-3xl font-bold text-white">Vedic Remedies</h1>
          </div>

          {/* Personalized Recommendations */}
          <div className="bg-gradient-to-r from-indigo-900/40 to-purple-900/40 border border-indigo-700/50 rounded-xl p-6 mb-8">
            <h2 className="text-lg font-semibold text-white mb-2">Personalized Remedies</h2>
            <p className="text-slate-400 text-sm mb-4">Get remedies tailored to your birth chart</p>
            <button
              onClick={getRecommendations}
              disabled={recommendLoading}
              className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition flex items-center gap-2"
            >
              {recommendLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              Get My Remedies
            </button>

            {recommended.length > 0 && (
              <div className="mt-4 space-y-3">
                {recommended.map((r) => (
                  <div key={r.id} className="bg-slate-800/60 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-white font-medium">{r.name}</h3>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${difficultyColors[r.difficulty]}`}>
                        {r.difficulty}
                      </span>
                    </div>
                    <p className="text-slate-400 text-sm mt-1">{r.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Planet Filter */}
          <h2 className="text-lg font-semibold text-white mb-3">Browse by Planet</h2>
          <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-9 gap-2 mb-6">
            {PLANETS.map((planet) => (
              <button
                key={planet}
                onClick={() => fetchByPlanet(planet)}
                className={`py-2 px-3 rounded-lg text-sm font-medium transition ${
                  selectedPlanet === planet
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
                }`}
              >
                {planet}
              </button>
            ))}
          </div>

          {/* Remedies List */}
          {loading && (
            <div className="flex justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            </div>
          )}

          {!loading && remedies.length > 0 && (
            <div className="space-y-3">
              {remedies.map((remedy) => (
                <div key={remedy.id} className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
                  <button
                    onClick={() => setExpandedId(expandedId === remedy.id ? null : remedy.id)}
                    className="w-full p-4 text-left flex items-center justify-between hover:bg-slate-800/80 transition"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-white font-medium">{remedy.name}</h3>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${difficultyColors[remedy.difficulty]}`}>
                          {remedy.difficulty}
                        </span>
                      </div>
                      <p className="text-slate-400 text-sm truncate">{remedy.description}</p>
                    </div>
                    <ChevronRight className={`w-5 h-5 text-slate-400 transition-transform ${expandedId === remedy.id ? 'rotate-90' : ''}`} />
                  </button>

                  {expandedId === remedy.id && (
                    <div className="px-4 pb-4 border-t border-slate-700 pt-3">
                      <p className="text-sm text-slate-300 mb-3">{remedy.description}</p>
                      <h4 className="text-xs font-semibold text-slate-400 uppercase mb-2">Instructions</h4>
                      <ul className="space-y-2">
                        {remedy.instructions.map((step, i) => (
                          <li key={i} className="flex gap-2 text-sm text-slate-300">
                            <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                            {step}
                          </li>
                        ))}
                      </ul>
                      <div className="mt-3 flex items-center gap-2">
                        <span className="text-xs text-slate-500">Effectiveness:</span>
                        <div className="flex-1 bg-slate-700 rounded-full h-2 max-w-[200px]">
                          <div
                            className="bg-indigo-500 h-2 rounded-full"
                            style={{ width: `${remedy.effectiveness}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-400">{remedy.effectiveness}%</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {!loading && selectedPlanet && remedies.length === 0 && (
            <p className="text-center text-slate-400 py-8">No remedies found for {selectedPlanet}</p>
          )}

          {/* Categories */}
          {categories.length > 0 && (
            <div className="mt-8">
              <h2 className="text-lg font-semibold text-white mb-3">Categories</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {categories.map((cat) => (
                  <div key={cat.name} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center">
                    <p className="text-white font-medium">{cat.name}</p>
                    <p className="text-slate-400 text-sm">{cat.count} remedies</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  )
}
