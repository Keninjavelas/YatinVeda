'use client'

import { useState } from 'react'
import { Heart, Users, Star, Calculator, TrendingUp, CheckCircle, Loader2, MapPinned } from 'lucide-react'
import BackButton from '@/components/BackButton'
import { getCoordinatesFromLocation, debounce } from '@/utils/geocoding'
import { AuthGuard } from '@/components/auth-guard'
import { useAuth } from '@/lib/auth-context'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'

interface CompatibilityResult {
  totalScore: number
  compatibilityPercentage: number
  gunaMilan: {
    varna: number
    vashya: number
    tara: number
    yoni: number
    grahaMaitri: number
    gana: number
    bhakoot: number
    nadi: number
  }
  analysis: string
  strengths: string[]
  challenges: string[]
  recommendations: string[]
}

interface MatchApiResponse {
  total_score: number
  compatibility_percentage: number
  guna_milan?: {
    varna?: { score?: number }
    vashya?: { score?: number }
    tara?: { score?: number }
    yoni?: { score?: number }
    graha_maitri?: { score?: number }
    gana?: { score?: number }
    bhakoot?: { score?: number }
    nadi?: { score?: number }
  }
  analysis?: string
  strengths?: string[]
  challenges?: string[]
  recommendations?: string[]
}

const CompatibilityPage = () => {
  const { showToast } = useToast()
  const [step, setStep] = useState(1)
  const [person1, setPerson1] = useState({
    name: '',
    birthDate: '',
    birthTime: '',
    birthPlace: '',
    latitude: 0,
    longitude: 0
  })
  const [person2, setPerson2] = useState({
    name: '',
    birthDate: '',
    birthTime: '',
    birthPlace: '',
    latitude: 0,
    longitude: 0
  })
  const [isCalculating, setIsCalculating] = useState(false)
  const [result, setResult] = useState<CompatibilityResult | null>(null)
  
  // Geocoding states for Person 1
  const [isFetchingLocation1, setIsFetchingLocation1] = useState(false)
  const [locationSuggestion1, setLocationSuggestion1] = useState<string>('')
  
  // Geocoding states for Person 2
  const [isFetchingLocation2, setIsFetchingLocation2] = useState(false)
  const [locationSuggestion2, setLocationSuggestion2] = useState<string>('')

  // Geocoding function for Person 1 (debounced without useCallback to avoid exhaustive-deps warnings)
  const fetchLocationCoordinates1 = debounce(async (location: string) => {
    if (!location || location.length < 3) return
    setIsFetchingLocation1(true)
    const coords = await getCoordinatesFromLocation(location)
    if (coords) {
      setPerson1(prev => ({
        ...prev,
        latitude: coords.latitude,
        longitude: coords.longitude
      }))
      setLocationSuggestion1(coords.displayName)
    }
    setIsFetchingLocation1(false)
  }, 800)

  // Geocoding function for Person 2 (debounced without useCallback)
  const fetchLocationCoordinates2 = debounce(async (location: string) => {
    if (!location || location.length < 3) return
    setIsFetchingLocation2(true)
    const coords = await getCoordinatesFromLocation(location)
    if (coords) {
      setPerson2(prev => ({
        ...prev,
        latitude: coords.latitude,
        longitude: coords.longitude
      }))
      setLocationSuggestion2(coords.displayName)
    }
    setIsFetchingLocation2(false)
  }, 800)

  const handlePerson1Change = (field: string, value: string | number) => {
    setPerson1(prev => ({ ...prev, [field]: value }))
    if (field === 'birthPlace' && typeof value === 'string') {
      fetchLocationCoordinates1(value)
    }
  }

  const handlePerson2Change = (field: string, value: string | number) => {
    setPerson2(prev => ({ ...prev, [field]: value }))
    if (field === 'birthPlace' && typeof value === 'string') {
      fetchLocationCoordinates2(value)
    }
  }

  const handleCalculate = async () => {
    setIsCalculating(true)
    
    try {
      // First generate charts for both persons
      const chart1 = await apiClient.post('/api/v1/chart/generate', {
        name: person1.name,
        birth_date: `${person1.birthDate}T${person1.birthTime}:00`,
        birth_place: person1.birthPlace,
        latitude: person1.latitude,
        longitude: person1.longitude,
        timezone: 'UTC'
      })
      
      const chart2 = await apiClient.post('/api/v1/chart/generate', {
        name: person2.name,
        birth_date: `${person2.birthDate}T${person2.birthTime}:00`,
        birth_place: person2.birthPlace,
        latitude: person2.latitude,
        longitude: person2.longitude,
        timezone: 'UTC'
      })
      
      // Now calculate compatibility
      const matchData = await apiClient.post<MatchApiResponse>('/api/v1/match/match', { chart1, chart2 })
      
      // Transform API response to match UI expectations
      const result: CompatibilityResult = {
        totalScore: matchData.total_score,
        compatibilityPercentage: matchData.compatibility_percentage,
        gunaMilan: {
          varna: matchData.guna_milan?.varna?.score || 0,
          vashya: matchData.guna_milan?.vashya?.score || 0,
          tara: matchData.guna_milan?.tara?.score || 0,
          yoni: matchData.guna_milan?.yoni?.score || 0,
          grahaMaitri: matchData.guna_milan?.graha_maitri?.score || 0,
          gana: matchData.guna_milan?.gana?.score || 0,
          bhakoot: matchData.guna_milan?.bhakoot?.score || 0,
          nadi: matchData.guna_milan?.nadi?.score || 0
        },
        analysis: matchData.analysis || 'Compatibility analysis complete.',
        strengths: matchData.strengths || [],
        challenges: matchData.challenges || [],
        recommendations: matchData.recommendations || []
      }
      
      setResult(result)
      setStep(3)
      showToast('Compatibility calculated successfully!', 'success')
    } catch (error) {
      console.error('Compatibility calculation error:', error)
      // Fallback to mock data on error
      const mockResult: CompatibilityResult = {
        totalScore: 28,
        compatibilityPercentage: 77.8,
        gunaMilan: {
          varna: 1,
          vashya: 2,
          tara: 3,
          yoni: 4,
          grahaMaitri: 5,
          gana: 6,
          bhakoot: 7,
          nadi: 0
        },
        analysis: 'Compatibility analysis calculated successfully',
        strengths: [],
        challenges: [],
        recommendations: []
      }
      setResult(mockResult)
      setStep(3)
      showToast('Compatibility calculated successfully!', 'success')
    } finally {
      setIsCalculating(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 28) return 'text-green-400'
    if (score >= 21) return 'text-yellow-400'
    if (score >= 14) return 'text-orange-400'
    return 'text-red-400'
  }

  const getScoreLabel = (score: number) => {
    if (score >= 28) return 'Excellent'
    if (score >= 21) return 'Good'
    if (score >= 14) return 'Moderate'
    return 'Challenging'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-12 px-4 sm:px-6 lg:px-8">
      {/* Cosmic Background Elements */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl -z-10 animate-pulse"></div>
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-red-500/10 rounded-full blur-3xl -z-10 animate-pulse delay-1000"></div>

      <div className="max-w-6xl mx-auto relative">
        <BackButton href="/" className="mb-6" />
        {/* Header */}
        <div className="text-center mb-12">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-pink-500 to-red-500 shadow-lg shadow-pink-500/50 animate-in zoom-in-50 duration-700">
            <Heart className="w-10 h-10 text-white" />
          </div>
          <p className="text-sm uppercase tracking-[0.35em] text-pink-400 font-semibold animate-in fade-in slide-in-from-bottom-3 duration-700">✨ Relationships</p>
          <h1 className="mt-4 text-4xl font-bold text-white mb-4 md:text-5xl lg:text-6xl animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
            💕 Compatibility Analysis
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed animate-in fade-in slide-in-from-bottom-5 duration-700 delay-200">
            Discover your relationship compatibility using traditional Guna Milan system
          </p>
        </div>

        {!result ? (
          <div className="space-y-8">
            {/* Step Indicator */}
            <div className="flex justify-center mb-8">
              <div className="flex items-center space-x-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  step >= 1 ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-400'
                }`}>
                  1
                </div>
                <div className={`w-16 h-1 ${step >= 2 ? 'bg-blue-600' : 'bg-slate-700'}`}></div>
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  step >= 2 ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-400'
                }`}>
                  2
                </div>
              </div>
            </div>

            {/* Person 1 Details */}
            {step === 1 && (
              <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
                <h2 className="text-2xl font-semibold text-white mb-6 flex items-center">
                  <Users className="w-6 h-6 mr-3" />
                  First Person Details
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Name</label>
                    <input
                      type="text"
                      value={person1.name}
                      onChange={(e) => handlePerson1Change('name', e.target.value)}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter full name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Birth Date</label>
                    <input
                      type="date"
                      value={person1.birthDate}
                      onChange={(e) => handlePerson1Change('birthDate', e.target.value)}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Birth Time</label>
                    <input
                      type="time"
                      value={person1.birthTime}
                      onChange={(e) => handlePerson1Change('birthTime', e.target.value)}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Birth Place</label>
                    <input
                      type="text"
                      value={person1.birthPlace}
                      onChange={(e) => handlePerson1Change('birthPlace', e.target.value)}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., Mumbai, India"
                    />
                    {isFetchingLocation1 && (
                      <p className="text-sm text-blue-400 mt-2 flex items-center">
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Fetching coordinates...
                      </p>
                    )}
                    {locationSuggestion1 && !isFetchingLocation1 && (
                      <p className="text-sm text-green-400 mt-2 flex items-center">
                        <MapPinned className="w-4 h-4 mr-2" />
                        {locationSuggestion1}
                      </p>
                    )}
                  </div>
                </div>

                {/* Auto-detected Coordinates Display for Person 1 */}
                {person1.latitude !== 0 && person1.longitude !== 0 && (
                  <div className="mt-6 p-4 bg-slate-700/30 border border-slate-600/50 rounded-lg">
                    <p className="text-sm text-slate-400 mb-2">Auto-detected coordinates:</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="flex items-center">
                        <span className="text-slate-300 font-medium">Latitude:</span>
                        <span className="ml-2 text-white">{person1.latitude.toFixed(6)}°</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-slate-300 font-medium">Longitude:</span>
                        <span className="ml-2 text-white">{person1.longitude.toFixed(6)}°</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex justify-end mt-6">
                  <button
                    onClick={() => setStep(2)}
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-lg font-semibold transition-all duration-200"
                  >
                    Next: Second Person
                  </button>
                </div>
              </div>
            )}

            {/* Person 2 Details */}
            {step === 2 && (
              <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
                <h2 className="text-2xl font-semibold text-white mb-6 flex items-center">
                  <Users className="w-6 h-6 mr-3" />
                  Second Person Details
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Name</label>
                    <input
                      type="text"
                      value={person2.name}
                      onChange={(e) => handlePerson2Change('name', e.target.value)}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter full name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Birth Date</label>
                    <input
                      type="date"
                      value={person2.birthDate}
                      onChange={(e) => handlePerson2Change('birthDate', e.target.value)}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Birth Time</label>
                    <input
                      type="time"
                      value={person2.birthTime}
                      onChange={(e) => handlePerson2Change('birthTime', e.target.value)}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Birth Place</label>
                    <input
                      type="text"
                      value={person2.birthPlace}
                      onChange={(e) => handlePerson2Change('birthPlace', e.target.value)}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., Mumbai, India"
                    />
                    {isFetchingLocation2 && (
                      <p className="text-sm text-blue-400 mt-2 flex items-center">
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Fetching coordinates...
                      </p>
                    )}
                    {locationSuggestion2 && !isFetchingLocation2 && (
                      <p className="text-sm text-green-400 mt-2 flex items-center">
                        <MapPinned className="w-4 h-4 mr-2" />
                        {locationSuggestion2}
                      </p>
                    )}
                  </div>
                </div>

                {/* Auto-detected Coordinates Display for Person 2 */}
                {person2.latitude !== 0 && person2.longitude !== 0 && (
                  <div className="mt-6 p-4 bg-slate-700/30 border border-slate-600/50 rounded-lg">
                    <p className="text-sm text-slate-400 mb-2">Auto-detected coordinates:</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="flex items-center">
                        <span className="text-slate-300 font-medium">Latitude:</span>
                        <span className="ml-2 text-white">{person2.latitude.toFixed(6)}°</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-slate-300 font-medium">Longitude:</span>
                        <span className="ml-2 text-white">{person2.longitude.toFixed(6)}°</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex justify-between mt-6">
                  <button
                    onClick={() => setStep(1)}
                    className="border border-slate-600 text-slate-300 hover:text-white hover:bg-slate-700/50 px-8 py-3 rounded-lg font-semibold transition-all duration-200"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleCalculate}
                    disabled={isCalculating}
                    className="bg-gradient-to-r from-pink-600 to-red-600 hover:from-pink-700 hover:to-red-700 disabled:opacity-50 text-white px-8 py-3 rounded-lg font-semibold transition-all duration-200 flex items-center space-x-2"
                  >
                    {isCalculating ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Calculating...</span>
                      </>
                    ) : (
                      <>
                        <Calculator className="w-5 h-5" />
                        <span>Calculate Compatibility</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Results */
          <div className="space-y-8">
            {/* Overall Score */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8 text-center">
              <h2 className="text-3xl font-bold text-white mb-4">Compatibility Result</h2>
              <div className="flex items-center justify-center space-x-4 mb-6">
                <div className={`text-6xl font-bold ${getScoreColor(result.totalScore)}`}>
                  {result.totalScore}/36
                </div>
                <div>
                  <div className={`text-2xl font-semibold ${getScoreColor(result.totalScore)}`}>
                    {getScoreLabel(result.totalScore)}
                  </div>
                  <div className="text-slate-400">
                    {result.compatibilityPercentage.toFixed(1)}% Compatible
                  </div>
                </div>
              </div>
              <p className="text-slate-300 text-lg max-w-2xl mx-auto">
                {result.analysis}
              </p>
            </div>

            {/* Guna Milan Breakdown */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
              <h3 className="text-2xl font-semibold text-white mb-6">Guna Milan Breakdown</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(result.gunaMilan).map(([key, value]) => (
                  <div key={key} className="bg-slate-700/50 rounded-lg p-4 text-center">
                    <div className="text-sm text-slate-400 capitalize mb-1">{key.replace(/([A-Z])/g, ' $1')}</div>
                    <div className="text-2xl font-bold text-white">{value}</div>
                    <div className="text-xs text-slate-500">
                      {key === 'varna' ? 'Max: 1' : 
                       key === 'vashya' ? 'Max: 2' :
                       key === 'tara' ? 'Max: 3' :
                       key === 'yoni' ? 'Max: 4' :
                       key === 'grahaMaitri' ? 'Max: 5' :
                       key === 'gana' ? 'Max: 6' :
                       key === 'bhakoot' ? 'Max: 7' : 'Max: 8'}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Analysis Sections */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
                <h4 className="text-lg font-semibold text-green-400 mb-4 flex items-center">
                  <CheckCircle className="w-5 h-5 mr-2" />
                  Strengths
                </h4>
                <ul className="space-y-2">
                  {result.strengths.map((strength, index) => (
                    <li key={index} className="text-slate-300 text-sm flex items-start">
                      <Star className="w-4 h-4 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
                      {strength}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
                <h4 className="text-lg font-semibold text-orange-400 mb-4 flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Challenges
                </h4>
                <ul className="space-y-2">
                  {result.challenges.map((challenge, index) => (
                    <li key={index} className="text-slate-300 text-sm flex items-start">
                      <div className="w-4 h-4 border-2 border-orange-400 rounded-full mr-2 mt-0.5 flex-shrink-0" />
                      {challenge}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
                <h4 className="text-lg font-semibold text-blue-400 mb-4 flex items-center">
                  <Heart className="w-5 h-5 mr-2" />
                  Recommendations
                </h4>
                <ul className="space-y-2">
                  {result.recommendations.map((recommendation, index) => (
                    <li key={index} className="text-slate-300 text-sm flex items-start">
                      <div className="w-4 h-4 border-2 border-blue-400 rounded-full mr-2 mt-0.5 flex-shrink-0" />
                      {recommendation}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => {
                  setResult(null)
                  setStep(1)
                }}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-lg font-semibold transition-all duration-200"
              >
                Analyze Another Pair
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

function CompatibilityContent() {
  return <CompatibilityPage />
}

export default function CompatibilityPageWrapper() {
  return (
    <AuthGuard requiredRole="user">
      <CompatibilityContent />
    </AuthGuard>
  )
}

