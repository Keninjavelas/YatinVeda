'use client'

import { useState } from 'react'
import { Calendar, Clock, MapPin, User, Star, Loader2, MapPinned } from 'lucide-react'
import SimpleKundliCanvas from '@/components/SimpleKundliCanvas'
import BackButton from '@/components/BackButton'
import { getCoordinatesFromLocation, debounce } from '@/utils/geocoding'
import { AuthGuard } from '@/components/auth-guard'
import { useAuth } from '@/lib/auth-context'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'

interface ChartData {
  planetary_positions: Array<{
    planet: string
    sign: string
    house: string
    degree?: number
    nakshatra?: string
  }>
  ascendant: string
  moon_sign: string
  sun_sign: string
  birth_details: {
    name: string
    birthDate: string
    birthTime: string
    birthPlace: string
    latitude: number
    longitude: number
    timezone: string
  }
}

interface BirthDetails {
  name: string
  birthDate: string
  birthTime: string
  birthPlace: string
  latitude: number
  longitude: number
  timezone: string
}

const ChartGenerator = () => {
  const { showToast } = useToast()
  const [formData, setFormData] = useState<BirthDetails>({
    name: '',
    birthDate: '',
    birthTime: '',
    birthPlace: '',
    latitude: 0,
    longitude: 0,
    timezone: 'UTC'
  })
  
  const [isGenerating, setIsGenerating] = useState(false)
  const [isFetchingLocation, setIsFetchingLocation] = useState(false)
  const [chartData, setChartData] = useState<ChartData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [locationSuggestion, setLocationSuggestion] = useState<string>('')

  // Debounced location fetching (no React hook wrapper to avoid exhaustive-deps warnings)
  const fetchLocationCoordinates = debounce(async (location: string) => {
    if (!location || location.length < 3) return
    
    setIsFetchingLocation(true)
    try {
      const coords = await getCoordinatesFromLocation(location)
      if (coords) {
        setFormData(prev => ({
          ...prev,
          latitude: coords.latitude,
          longitude: coords.longitude,
          timezone: coords.timezone
        }))
        setLocationSuggestion(coords.displayName)
      }
    } catch (error) {
      console.error('Failed to fetch coordinates:', error)
    } finally {
      setIsFetchingLocation(false)
    }
  }, 800)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))

    // Auto-fetch coordinates when birth place changes
    if (name === 'birthPlace') {
      fetchLocationCoordinates(value)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsGenerating(true)
    setError(null)

    try {
      const data = await apiClient.post<ChartData>('/api/v1/chart/generate', {
        name: formData.name,
        birth_date: `${formData.birthDate}T${formData.birthTime}:00`,
        birth_place: formData.birthPlace,
        latitude: formData.latitude,
        longitude: formData.longitude,
        timezone: formData.timezone
      })

      setChartData(data)
      showToast('Chart generated successfully!', 'success')
    } catch (err) {
      const errorMsg = 'Failed to generate chart. Please check your details and try again.'
      setError(errorMsg)
      showToast(errorMsg, 'error')
      console.error('Chart generation error:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-12 px-4 sm:px-6 lg:px-8">
      {/* Cosmic Background Elements */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-yellow-500/10 rounded-full blur-3xl -z-10 animate-pulse"></div>
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl -z-10 animate-pulse delay-1000"></div>

      <div className="max-w-4xl mx-auto relative">
        {/* Back Button */}
        <BackButton href="/" className="mb-6" />
        
        {/* Header */}
        <div className="text-center mb-12">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 shadow-lg shadow-orange-500/50 animate-in zoom-in-50 duration-700">
            <Star className="w-10 h-10 text-white" />
          </div>
          <p className="text-sm uppercase tracking-[0.35em] text-orange-400 font-semibold animate-in fade-in slide-in-from-bottom-3 duration-700">✨ Birth Chart</p>
          <h1 className="mt-4 text-4xl font-bold text-white mb-4 md:text-5xl lg:text-6xl animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
            🌟 Generate Your Birth Chart
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed animate-in fade-in slide-in-from-bottom-5 duration-700 delay-200">
            Enter your birth details to create an accurate Vedic astrology birth chart
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form */}
          <div className="rounded-2xl border border-slate-700/60 bg-slate-800/50 p-8 shadow-lg shadow-blue-900/10 animate-in fade-in slide-in-from-left-6 duration-700 delay-300">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <span className="text-2xl">📋</span>
              Birth Information
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <User className="w-4 h-4 inline mr-2" />
                  Full Name
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your full name"
                />
              </div>

              {/* Birth Date */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <Calendar className="w-4 h-4 inline mr-2" />
                  Birth Date
                </label>
                <input
                  type="date"
                  name="birthDate"
                  value={formData.birthDate}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Birth Time */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <Clock className="w-4 h-4 inline mr-2" />
                  Birth Time
                </label>
                <input
                  type="time"
                  name="birthTime"
                  value={formData.birthTime}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Birth Place */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <MapPin className="w-4 h-4 inline mr-2" />
                  Birth Place
                </label>
                <input
                  type="text"
                  name="birthPlace"
                  value={formData.birthPlace}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Mumbai, India or New York, USA"
                />
                {isFetchingLocation && (
                  <p className="text-xs text-blue-400 mt-2 flex items-center gap-2">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Fetching coordinates...
                  </p>
                )}
                {locationSuggestion && !isFetchingLocation && (
                  <p className="text-xs text-green-400 mt-2 flex items-center gap-1">
                    <MapPinned className="w-3 h-3" />
                    {locationSuggestion}
                  </p>
                )}
              </div>

              {/* Auto-detected Coordinates - Read Only Display */}
              {formData.latitude !== 0 && formData.longitude !== 0 && (
                <div className="bg-slate-700/30 border border-slate-600/50 rounded-lg p-4">
                  <p className="text-xs text-slate-400 mb-2">📍 Auto-detected Coordinates</p>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-400">Latitude:</span>
                      <span className="text-white ml-2 font-mono">{formData.latitude.toFixed(6)}°</span>
                    </div>
                    <div>
                      <span className="text-slate-400">Longitude:</span>
                      <span className="text-white ml-2 font-mono">{formData.longitude.toFixed(6)}°</span>
                    </div>
                  </div>
                  <div className="mt-2">
                    <span className="text-slate-400 text-xs">Timezone:</span>
                    <span className="text-white ml-2 text-xs">{formData.timezone}</span>
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isGenerating}
                className="group w-full bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 disabled:opacity-50 text-white py-4 rounded-xl font-bold text-lg transition-all duration-300 flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/50 hover:shadow-blue-500/70 hover:scale-105"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Generating Chart...</span>
                  </>
                ) : (
                  <>
                    <Star className="w-5 h-5" />
                    <span>Generate Birth Chart</span>
                    <span className="transition-transform duration-300 group-hover:translate-x-1">→</span>
                  </>
                )}
              </button>

              {error && (
                <div className="bg-red-500/20 border border-red-500/50 text-red-400 px-4 py-3 rounded-xl font-semibold">
                  {error}
                </div>
              )}
            </form>
          </div>

          {/* Chart Preview */}
          <div className="rounded-2xl border border-slate-700/60 bg-slate-800/50 p-8 shadow-lg shadow-blue-900/10 animate-in fade-in slide-in-from-right-6 duration-700 delay-400">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <span className="text-2xl">🎯</span>
              Chart Preview
            </h2>
            
            {chartData ? (
              <div className="space-y-6">
                {/* Chart Visualization */}
                <div className="rounded-xl overflow-hidden border border-slate-600/50">
                  <SimpleKundliCanvas chartData={chartData} />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="rounded-xl border border-slate-700/50 bg-slate-700/30 p-4 hover:border-blue-500/40 transition-all duration-300">
                    <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                      <span>ℹ️</span>
                      Basic Information
                    </h3>
                    <div className="space-y-2 text-sm">
                      <p><span className="text-slate-400 font-semibold">Name:</span> <span className="text-white">{chartData.birth_details.name}</span></p>
                      <p><span className="text-slate-400 font-semibold">Ascendant:</span> <span className="text-blue-400 font-bold">{chartData.ascendant}</span></p>
                      <p><span className="text-slate-400 font-semibold">Sun Sign:</span> <span className="text-yellow-400 font-bold">{chartData.sun_sign}</span></p>
                      <p><span className="text-slate-400 font-semibold">Moon Sign:</span> <span className="text-slate-300 font-bold">{chartData.moon_sign}</span></p>
                    </div>
                  </div>

                  <div className="rounded-xl border border-slate-700/50 bg-slate-700/30 p-4 hover:border-blue-500/40 transition-all duration-300">
                    <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                      <span>🪐</span>
                      Planetary Positions
                    </h3>
                    <div className="space-y-1 text-sm max-h-48 overflow-y-auto">
                      {chartData.planetary_positions.map((planet: {planet: string, sign: string, house: string}, index: number) => (
                        <p key={index} className="hover:text-blue-300 transition-colors">
                          <span className="text-slate-400 font-semibold">{planet.planet}:</span> 
                          <span className="text-white ml-2">{planet.sign} ({planet.house})</span>
                        </p>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-slate-700/50 border border-slate-600/30">
                  <Star className="w-8 h-8 text-slate-400" />
                </div>
                <p className="text-slate-400 text-lg">
                  Your birth chart will appear here after generation
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function ChartContent() {
  return <ChartGenerator />
}

export default function ChartPage() {
  return (
    <AuthGuard requiredRole="user">
      <ChartContent />
    </AuthGuard>
  )
}

