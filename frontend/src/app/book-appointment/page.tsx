'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import Image from 'next/image'
import { 
  Search, Star, Clock, Video, Award, CheckCircle2, ArrowLeft
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { AuthGuard } from '@/components/auth-guard'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'

interface Guru {
  id: number
  name: string
  title: string
  specializations: string[]
  experience: number
  rating: number
  reviews: number
  hourlyRate: number
  avatar: string
  languages: string[]
  availability: string
  sessionTypes: string[]
  expertise: string[]
  bio: string
  verified: boolean
}

const GURUS: Guru[] = [
  {
    id: 1,
    name: "Yatin Sharma",
    title: "Vedic Astrology Expert & Life Coach",
    specializations: ["Birth Chart Analysis", "Career Guidance", "Relationship Compatibility", "Dasha Predictions"],
    experience: 3,
    rating: 4.9,
    reviews: 127,
    hourlyRate: 3100,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=yatin",
    languages: ["Hindi", "English"],
    availability: "Available Today",
    sessionTypes: ["Video Call", "Audio Call", "Chat"],
    expertise: ["Nadi Jyotish", "KP System", "Lal Kitab", "Prashna Kundali"],
    bio: "Specializing in detailed birth chart analysis and practical remedies. Helped 500+ clients find clarity in career, relationships, and life purpose using traditional Vedic wisdom.",
    verified: true
  },
  {
    id: 2,
    name: "Dr. Anjali Mehta",
    title: "PhD in Jyotish Shastra",
    specializations: ["Nakshatra Analysis", "Remedial Astrology", "Marriage Compatibility", "Health Astrology"],
    experience: 8,
    rating: 4.8,
    reviews: 342,
    hourlyRate: 4500,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=anjali",
    languages: ["Hindi", "English", "Sanskrit"],
    availability: "Available Tomorrow",
    sessionTypes: ["Video Call", "In-Person"],
    expertise: ["Parashari System", "Nakshatra Therapy", "Medical Astrology", "Muhurta"],
    bio: "PhD in Vedic Astrology with 8+ years of research and practice. Specializing in health predictions and remedial measures using gemstones and mantras.",
    verified: true
  },
  {
    id: 3,
    name: "Pandit Rajesh Kumar",
    title: "Traditional Jyotish Guru",
    specializations: ["Muhurta (Auspicious Timing)", "Business Astrology", "Spiritual Guidance", "Yoga Analysis"],
    experience: 15,
    rating: 5.0,
    reviews: 589,
    hourlyRate: 6000,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=rajesh",
    languages: ["Hindi", "English", "Bengali", "Tamil"],
    availability: "Next Week",
    sessionTypes: ["Video Call", "Audio Call", "In-Person"],
    expertise: ["Parashara Jyotish", "Jaimini System", "Tajika Yogas", "Varshaphal"],
    bio: "15 years of traditional Vedic astrology practice. Expert in business timing, wealth yogas, and spiritual counseling. Trained under renowned Jyotish lineage.",
    verified: true
  },
  {
    id: 4,
    name: "Meera Krishnan",
    title: "Nakshatra & Dasha Specialist",
    specializations: ["Nakshatra Counseling", "Dasha Analysis", "Karma & Past Life", "Women's Astrology"],
    experience: 5,
    rating: 4.9,
    reviews: 218,
    hourlyRate: 3500,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=meera",
    languages: ["Hindi", "English", "Tamil", "Telugu"],
    availability: "Available Today",
    sessionTypes: ["Video Call", "Chat"],
    expertise: ["Vimshottari Dasha", "Nakshatra Psychology", "Karmic Astrology", "Feminine Energies"],
    bio: "Specializing in nakshatra-based counseling and understanding karmic patterns. Empowering approach focusing on self-awareness and conscious living.",
    verified: true
  },
  {
    id: 5,
    name: "Vikram Singh Rathore",
    title: "Horary & Prashna Expert",
    specializations: ["Prashna Kundali", "Lost & Found", "Quick Predictions", "Emergency Consultations"],
    experience: 6,
    rating: 4.7,
    reviews: 195,
    hourlyRate: 2800,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=vikram",
    languages: ["Hindi", "English", "Punjabi"],
    availability: "Available Now",
    sessionTypes: ["Video Call", "Audio Call", "Chat"],
    expertise: ["Horary Astrology", "KP Prashna", "Electional Astrology", "Quick Analysis"],
    bio: "Expert in answering specific questions without birth details. Immediate clarity on pressing issues using Prashna (horary) techniques.",
    verified: true
  },
  {
    id: 6,
    name: "Dr. Priya Sharma",
    title: "Research Scholar & Consultant",
    specializations: ["Research-Based Analysis", "Chart Rectification", "Advanced Yogas", "Academic Guidance"],
    experience: 4,
    rating: 4.8,
    reviews: 156,
    hourlyRate: 3800,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=priya",
    languages: ["Hindi", "English"],
    availability: "Available Tomorrow",
    sessionTypes: ["Video Call", "Chat"],
    expertise: ["Divisional Charts", "Ashtakavarga", "Research Methodology", "Chart Rectification"],
    bio: "Research-oriented approach combining traditional wisdom with modern validation. Perfect for those seeking deep, analytical consultations.",
    verified: true
  }
]

function BookAppointmentContent() {
  const router = useRouter()
  const { csrfToken } = useAuth()
  const { showToast } = useToast()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedSpecialization, setSelectedSpecialization] = useState<string>('All')
  const [priceRange, setPriceRange] = useState<string>('All')
  const [availability, setAvailability] = useState<string>('All')
  const [selectedGuru, setSelectedGuru] = useState<Guru | null>(null)

  // Get unique specializations
  const allSpecializations = ['All', ...new Set(GURUS.flatMap(g => g.specializations))]

  // Filter gurus
  const filteredGurus = GURUS.filter(guru => {
    const matchesSearch = guru.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         guru.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         guru.specializations.some(s => s.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesSpecialization = selectedSpecialization === 'All' || 
                                 guru.specializations.includes(selectedSpecialization)
    
    const matchesPrice = priceRange === 'All' ||
                        (priceRange === 'budget' && guru.hourlyRate < 3500) ||
                        (priceRange === 'mid' && guru.hourlyRate >= 3500 && guru.hourlyRate < 5000) ||
                        (priceRange === 'premium' && guru.hourlyRate >= 5000)
    
    const matchesAvailability = availability === 'All' ||
                               guru.availability.toLowerCase().includes(availability.toLowerCase())

    return matchesSearch && matchesSpecialization && matchesPrice && matchesAvailability
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="bg-slate-900/50 backdrop-blur-sm border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-4"
          >
            <ArrowLeft className="w-5 h-5" />
            Back
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">Book an Appointment</h1>
              <p className="text-slate-400">Connect with experienced Vedic astrology experts</p>
            </div>
            <div className="hidden md:flex items-center gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-400">{GURUS.length}</div>
                <div className="text-xs text-slate-400">Expert Gurus</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-400">24/7</div>
                <div className="text-xs text-slate-400">Availability</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-400">4.8★</div>
                <div className="text-xs text-slate-400">Avg Rating</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Search and Filters */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700 p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-4 mb-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="Search by name, specialization, or expertise..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl pl-12 pr-4 py-3 text-white placeholder-slate-500 focus:border-purple-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-2">Specialization</label>
              <select
                value={selectedSpecialization}
                onChange={(e) => setSelectedSpecialization(e.target.value)}
                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-2 text-white focus:border-purple-500 focus:outline-none"
              >
                {allSpecializations.map(spec => (
                  <option key={spec} value={spec}>{spec}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">Price Range</label>
              <select
                value={priceRange}
                onChange={(e) => setPriceRange(e.target.value)}
                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-2 text-white focus:border-purple-500 focus:outline-none"
              >
                <option value="All">All Prices</option>
                <option value="budget">Budget (&lt;₹3,500)</option>
                <option value="mid">Mid-Range (₹3,500-5,000)</option>
                <option value="premium">Premium (&gt;₹5,000)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">Availability</label>
              <select
                value={availability}
                onChange={(e) => setAvailability(e.target.value)}
                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-2 text-white focus:border-purple-500 focus:outline-none"
              >
                <option value="All">All Times</option>
                <option value="now">Available Now</option>
                <option value="today">Available Today</option>
                <option value="tomorrow">Available Tomorrow</option>
              </select>
            </div>
          </div>
        </div>

        {/* Results Count */}
        <div className="mb-6">
          <p className="text-slate-400">
            Showing <span className="text-white font-semibold">{filteredGurus.length}</span> of {GURUS.length} experts
          </p>
        </div>

        {/* Guru Listings */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredGurus.map((guru) => (
            <motion.div
              key={guru.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700 p-6 hover:border-purple-500 transition-all duration-300"
            >
              <div className="flex items-start gap-4 mb-4">
                <Image
                  src={guru.avatar}
                  alt={guru.name}
                  width={80}
                  height={80}
                  className="w-20 h-20 rounded-xl border-2 border-purple-500"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-xl font-bold text-white">{guru.name}</h3>
                    {guru.verified && (
                      <span className="inline-flex items-center" aria-label="Verified Expert">
                        <CheckCircle2 className="w-5 h-5 text-blue-400" />
                        <span className="sr-only">Verified Expert</span>
                      </span>
                    )}
                  </div>
                  <p className="text-slate-400 text-sm mb-2">{guru.title}</p>
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1">
                      <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                      <span className="text-white font-semibold">{guru.rating}</span>
                      <span className="text-slate-400">({guru.reviews})</span>
                    </div>
                    <div className="flex items-center gap-1 text-slate-400">
                      <Award className="w-4 h-4" />
                      <span>{guru.experience} years</span>
                    </div>
                  </div>
                </div>
              </div>

              <p className="text-slate-300 text-sm mb-4 line-clamp-2">{guru.bio}</p>

              {/* Specializations */}
              <div className="mb-4">
                <div className="flex flex-wrap gap-2">
                  {guru.specializations.slice(0, 3).map((spec) => (
                    <span
                      key={spec}
                      className="px-3 py-1 bg-purple-500/20 text-purple-300 text-xs rounded-full border border-purple-500/30"
                    >
                      {spec}
                    </span>
                  ))}
                  {guru.specializations.length > 3 && (
                    <span className="px-3 py-1 bg-slate-700/50 text-slate-400 text-xs rounded-full">
                      +{guru.specializations.length - 3} more
                    </span>
                  )}
                </div>
              </div>

              {/* Availability and Session Types */}
              <div className="flex items-center gap-4 mb-4 text-sm">
                <div className="flex items-center gap-2 text-green-400">
                  <Clock className="w-4 h-4" />
                  <span>{guru.availability}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  {guru.sessionTypes.includes("Video Call") && <Video className="w-4 h-4" />}
                  <span>{guru.sessionTypes.join(", ")}</span>
                </div>
              </div>

              {/* Languages */}
              <div className="mb-4 text-sm text-slate-400">
                <span className="font-semibold text-slate-300">Languages:</span> {guru.languages.join(", ")}
              </div>

              {/* Price and Book Button */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                <div>
                  <div className="text-2xl font-bold text-white">₹{guru.hourlyRate}</div>
                  <div className="text-xs text-slate-400">per hour session</div>
                </div>
                <button
                  onClick={() => setSelectedGuru(guru)}
                  className="bg-gradient-to-r from-purple-500 to-blue-500 text-white font-semibold px-6 py-3 rounded-xl hover:from-purple-600 hover:to-blue-600 transition-all duration-300 shadow-lg hover:shadow-purple-500/50"
                >
                  Book Session
                </button>
              </div>
            </motion.div>
          ))}
        </div>

        {filteredGurus.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <p className="text-xl text-slate-400 mb-2">No experts found</p>
            <p className="text-slate-500">Try adjusting your filters or search terms</p>
          </div>
        )}
      </div>

      {/* Booking Modal */}
      {selectedGuru && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-slate-800 rounded-2xl border border-slate-700 max-w-2xl w-full p-6"
          >
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center gap-4">
                <Image
                  src={selectedGuru.avatar}
                  alt={selectedGuru.name}
                  width={64}
                  height={64}
                  className="w-16 h-16 rounded-xl border-2 border-purple-500"
                />
                <div>
                  <h2 className="text-2xl font-bold text-white">{selectedGuru.name}</h2>
                  <p className="text-slate-400">{selectedGuru.title}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedGuru(null)}
                className="text-slate-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-4 mb-6">
              <div className="bg-slate-900/50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-400">Session Duration</span>
                  <span className="text-white font-semibold">1 Hour</span>
                </div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-400">Session Type</span>
                  <span className="text-white font-semibold">Video Call</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Total Amount</span>
                  <span className="text-2xl font-bold text-purple-400">₹{selectedGuru.hourlyRate}</span>
                </div>
              </div>

              <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
                <p className="text-blue-300 text-sm">
                  📅 Select your preferred date and time after clicking &quot;Continue to Payment&quot;
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setSelectedGuru(null)}
                className="flex-1 bg-slate-700 text-white font-semibold px-6 py-3 rounded-xl hover:bg-slate-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  showToast(`Booking confirmed with ${selectedGuru.name}! Check your email for calendar invite.`, 'success')
                  setSelectedGuru(null)
                }}
                className="flex-1 bg-gradient-to-r from-purple-500 to-blue-500 text-white font-semibold px-6 py-3 rounded-xl hover:from-purple-600 hover:to-blue-600 transition-all duration-300"
              >
                Continue to Payment
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

export default function BookAppointmentPage() {
  return (
    <AuthGuard requiredRole="user">
      <BookAppointmentContent />
    </AuthGuard>
  )
}
