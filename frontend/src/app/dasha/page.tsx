'use client'

import { useState } from 'react'
import { Moon, Calendar, Clock, TrendingUp, Star, Zap, Loader2, MapPinned } from 'lucide-react'
import BackButton from '@/components/BackButton'
import { getCoordinatesFromLocation, debounce } from '@/utils/geocoding'
import { AuthGuard } from '@/components/auth-guard'
import { useAuth } from '@/lib/auth-context'

interface DashaPeriod {
  planet: string
  startDate: string
  endDate: string
  durationYears: number
  isActive: boolean
}

interface Transit {
  planet: string
  currentSign: string
  entryDate: string
  exitDate: string
  effects: string[]
}

const DashaPage = () => {
  const { csrfToken } = useAuth()
  const [birthDetails, setBirthDetails] = useState({
    name: '',
    birthDate: '',
    birthTime: '',
    birthPlace: '',
    latitude: 0,
    longitude: 0
  })
  const [isCalculating, setIsCalculating] = useState(false)
  const [dashaData, setDashaData] = useState<{
    mahadasha: DashaPeriod[]
    currentMahadasha: DashaPeriod | null
    transits: Transit[]
  } | null>(null)
  
  // Geocoding states
  const [isFetchingLocation, setIsFetchingLocation] = useState(false)
  const [locationSuggestion, setLocationSuggestion] = useState<string>('')

  // Geocoding function (debounced without useCallback to avoid exhaustive-deps warnings)
  const fetchLocationCoordinates = debounce(async (location: string) => {
    if (!location || location.length < 3) return
    setIsFetchingLocation(true)
    const coords = await getCoordinatesFromLocation(location)
    if (coords) {
      setBirthDetails(prev => ({
        ...prev,
        latitude: coords.latitude,
        longitude: coords.longitude
      }))
      setLocationSuggestion(coords.displayName)
    }
    setIsFetchingLocation(false)
  }, 800)

  const handleInputChange = (field: string, value: string | number) => {
    setBirthDetails(prev => ({ ...prev, [field]: value }))
    if (field === 'birthPlace' && typeof value === 'string') {
      fetchLocationCoordinates(value)
    }
  }

  const handleCalculate = async () => {
    setIsCalculating(true)
    
    // Simulate API call
    setTimeout(() => {
      const mockDashaData = {
        mahadasha: [
          {
            planet: 'Sun',
            startDate: '2020-01-01',
            endDate: '2026-01-01',
            durationYears: 6,
            isActive: true
          },
          {
            planet: 'Moon',
            startDate: '2026-01-01',
            endDate: '2036-01-01',
            durationYears: 10,
            isActive: false
          },
          {
            planet: 'Mars',
            startDate: '2036-01-01',
            endDate: '2043-01-01',
            durationYears: 7,
            isActive: false
          }
        ],
        currentMahadasha: {
          planet: 'Sun',
          startDate: '2020-01-01',
          endDate: '2026-01-01',
          durationYears: 6,
          isActive: true
        },
        transits: [
          {
            planet: 'Jupiter',
            currentSign: 'Pisces',
            entryDate: '2024-01-01',
            exitDate: '2025-01-01',
            effects: ['Spiritual growth', 'Wisdom expansion', 'Good fortune']
          },
          {
            planet: 'Saturn',
            currentSign: 'Aquarius',
            entryDate: '2023-01-01',
            exitDate: '2026-01-01',
            effects: ['Discipline', 'Hard work', 'Long-term rewards']
          },
          {
            planet: 'Mars',
            currentSign: 'Scorpio',
            entryDate: '2024-06-01',
            exitDate: '2024-08-01',
            effects: ['Increased energy', 'Courage', 'Potential conflicts']
          }
        ]
      }
      setDashaData(mockDashaData)
      setIsCalculating(false)
    }, 2000)
  }

  const getPlanetColor = (planet: string) => {
    const colors: { [key: string]: string } = {
      'Sun': 'text-yellow-400',
      'Moon': 'text-slate-300',
      'Mars': 'text-red-400',
      'Mercury': 'text-green-400',
      'Jupiter': 'text-orange-400',
      'Venus': 'text-pink-400',
      'Saturn': 'text-blue-400',
      'Rahu': 'text-purple-400',
      'Ketu': 'text-indigo-400'
    }
    return colors[planet] || 'text-slate-400'
  }

  const getPlanetBgColor = (planet: string) => {
    const colors: { [key: string]: string } = {
      'Sun': 'bg-yellow-400/20 border-yellow-400/30',
      'Moon': 'bg-slate-300/20 border-slate-300/30',
      'Mars': 'bg-red-400/20 border-red-400/30',
      'Mercury': 'bg-green-400/20 border-green-400/30',
      'Jupiter': 'bg-orange-400/20 border-orange-400/30',
      'Venus': 'bg-pink-400/20 border-pink-400/30',
      'Saturn': 'bg-blue-400/20 border-blue-400/30',
      'Rahu': 'bg-purple-400/20 border-purple-400/30',
      'Ketu': 'bg-indigo-400/20 border-indigo-400/30'
    }
    return colors[planet] || 'bg-slate-400/20 border-slate-400/30'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-12 px-4 sm:px-6 lg:px-8">
      {/* Cosmic Background Elements */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl -z-10 animate-pulse"></div>
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl -z-10 animate-pulse delay-1000"></div>

      <div className="max-w-7xl mx-auto relative">
        <BackButton href="/" className="mb-6" />
        {/* Header */}
        <div className="text-center mb-12">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-purple-500 to-blue-500 shadow-lg shadow-purple-500/50 animate-in zoom-in-50 duration-700">
            <Moon className="w-10 h-10 text-white" />
          </div>
          <p className="text-sm uppercase tracking-[0.35em] text-purple-400 font-semibold animate-in fade-in slide-in-from-bottom-3 duration-700">✨ Planetary Periods</p>
          <h1 className="mt-4 text-4xl font-bold text-white mb-4 md:text-5xl lg:text-6xl animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
            🌙 Dasha & Transits
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed animate-in fade-in slide-in-from-bottom-5 duration-700 delay-200">
            Track your planetary periods and current transits affecting your life
          </p>
        </div>

        {!dashaData ? (
          /* Birth Details Form */
          <div className="rounded-2xl border border-slate-700/60 bg-slate-800/50 p-8 shadow-lg shadow-blue-900/10 animate-in fade-in slide-in-from-bottom-6 duration-700 delay-300">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <Calendar className="w-6 h-6" />
              Birth Details
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Name</label>
                <input
                  type="text"
                  value={birthDetails.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter your full name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Birth Date</label>
                <input
                  type="date"
                  value={birthDetails.birthDate}
                  onChange={(e) => handleInputChange('birthDate', e.target.value)}
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Birth Time</label>
                <input
                  type="time"
                  value={birthDetails.birthTime}
                  onChange={(e) => handleInputChange('birthTime', e.target.value)}
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Birth Place</label>
                <input
                  type="text"
                  value={birthDetails.birthPlace}
                  onChange={(e) => handleInputChange('birthPlace', e.target.value)}
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Mumbai, India"
                />
                {isFetchingLocation && (
                  <p className="text-sm text-blue-400 mt-2 flex items-center">
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Fetching coordinates...
                  </p>
                )}
                {locationSuggestion && !isFetchingLocation && (
                  <p className="text-sm text-green-400 mt-2 flex items-center">
                    <MapPinned className="w-4 h-4 mr-2" />
                    {locationSuggestion}
                  </p>
                )}
              </div>
            </div>

            {/* Auto-detected Coordinates Display */}
            {birthDetails.latitude !== 0 && birthDetails.longitude !== 0 && (
              <div className="mt-6 p-4 bg-slate-700/30 border border-slate-600/50 rounded-lg">
                <p className="text-sm text-slate-400 mb-2">Auto-detected coordinates:</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center">
                    <span className="text-slate-300 font-medium">Latitude:</span>
                    <span className="ml-2 text-white">{birthDetails.latitude.toFixed(6)}°</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-slate-300 font-medium">Longitude:</span>
                    <span className="ml-2 text-white">{birthDetails.longitude.toFixed(6)}°</span>
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-center mt-8">
              <button
                onClick={handleCalculate}
                disabled={isCalculating}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 text-white px-8 py-4 rounded-lg font-semibold text-lg transition-all duration-200 flex items-center space-x-2"
              >
                {isCalculating ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Calculating...</span>
                  </>
                ) : (
                  <>
                    <Moon className="w-5 h-5" />
                    <span>Calculate Dasha & Transits</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          /* Results */
          <div className="space-y-8">
            {/* Current Mahadasha */}
            {dashaData.currentMahadasha && (
              <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
                <h2 className="text-2xl font-semibold text-white mb-6 flex items-center">
                  <Star className="w-6 h-6 mr-3" />
                  Current Mahadasha Period
                </h2>
                <div className={`p-6 rounded-lg border ${getPlanetBgColor(dashaData.currentMahadasha.planet)}`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className={`text-2xl font-bold ${getPlanetColor(dashaData.currentMahadasha.planet)}`}>
                      {dashaData.currentMahadasha.planet} Mahadasha
                    </h3>
                    <div className="flex items-center space-x-2 text-slate-400">
                      <Clock className="w-4 h-4" />
                      <span>{dashaData.currentMahadasha.durationYears} years</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-slate-300">
                    <div>
                      <span className="text-slate-400">Start Date:</span>
                      <span className="ml-2">{new Date(dashaData.currentMahadasha.startDate).toLocaleDateString()}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">End Date:</span>
                      <span className="ml-2">{new Date(dashaData.currentMahadasha.endDate).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full"
                        style={{ width: '60%' }}
                      ></div>
                    </div>
                    <p className="text-slate-400 text-sm mt-2">60% completed</p>
                  </div>
                </div>
              </div>
            )}

            {/* Mahadasha Timeline */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
              <h3 className="text-2xl font-semibold text-white mb-6">Mahadasha Timeline</h3>
              <div className="space-y-4">
                {dashaData.mahadasha.map((period, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border transition-all duration-200 ${
                      period.isActive 
                        ? getPlanetBgColor(period.planet)
                        : 'bg-slate-700/50 border-slate-600/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                          period.isActive ? 'bg-gradient-to-br from-purple-500 to-blue-500' : 'bg-slate-600'
                        }`}>
                          <span className="text-white font-bold text-lg">
                            {period.planet.charAt(0)}
                          </span>
                        </div>
                        <div>
                          <h4 className={`text-lg font-semibold ${
                            period.isActive ? getPlanetColor(period.planet) : 'text-slate-300'
                          }`}>
                            {period.planet} Mahadasha
                          </h4>
                          <p className="text-slate-400 text-sm">
                            {new Date(period.startDate).toLocaleDateString()} - {new Date(period.endDate).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-slate-400 text-sm">Duration</div>
                        <div className="text-white font-semibold">{period.durationYears} years</div>
                        {period.isActive && (
                          <div className="text-green-400 text-sm font-medium">Active</div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Current Transits */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
              <h3 className="text-2xl font-semibold text-white mb-6 flex items-center">
                <TrendingUp className="w-6 h-6 mr-3" />
                Current Planetary Transits
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {dashaData.transits.map((transit, index) => (
                  <div
                    key={index}
                    className={`p-6 rounded-lg border ${getPlanetBgColor(transit.planet)}`}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h4 className={`text-lg font-semibold ${getPlanetColor(transit.planet)}`}>
                        {transit.planet}
                      </h4>
                      <div className="text-slate-400 text-sm">
                        {transit.currentSign}
                      </div>
                    </div>
                    <div className="space-y-2 text-slate-300 text-sm mb-4">
                      <div>
                        <span className="text-slate-400">Entry:</span>
                        <span className="ml-2">{new Date(transit.entryDate).toLocaleDateString()}</span>
                      </div>
                      <div>
                        <span className="text-slate-400">Exit:</span>
                        <span className="ml-2">{new Date(transit.exitDate).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div>
                      <h5 className="text-slate-400 text-sm font-medium mb-2">Effects:</h5>
                      <ul className="space-y-1">
                        {transit.effects.map((effect, effectIndex) => (
                          <li key={effectIndex} className="text-slate-300 text-sm flex items-start">
                            <Zap className="w-3 h-3 text-yellow-400 mr-2 mt-0.5 flex-shrink-0" />
                            {effect}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => setDashaData(null)}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition-all duration-200"
              >
                Calculate Another Chart
              </button>
              <button className="border border-slate-600 text-slate-300 hover:text-white hover:bg-slate-700/50 px-8 py-3 rounded-lg font-semibold transition-all duration-200">
                Save Report
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function DashaContent() {
  return <DashaPage />
}

export default function DashaPageWrapper() {
  return (
    <AuthGuard requiredRole="user">
      <DashaContent />
    </AuthGuard>
  )
}

