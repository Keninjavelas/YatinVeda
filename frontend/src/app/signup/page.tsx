'use client'

import { useState, FormEvent, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import Link from 'next/link'
import { Mail, Lock, User, AlertCircle, CheckCircle, Eye, EyeOff, Star, UserCheck, Briefcase, FileText, Award, Clock, DollarSign, Globe } from 'lucide-react'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'

type UserRole = 'user' | 'practitioner'

interface UserRegistrationData {
  username: string
  email: string
  password: string
  full_name: string
  role: 'user'
}

interface PractitionerRegistrationData {
  username: string
  email: string
  password: string
  full_name: string
  role: 'practitioner'
  professional_title: string
  bio: string
  specializations: string[]
  experience_years: number
  certification_details: {
    certification_type: string
    issuing_authority: string
  }
  languages: string[]
  price_per_hour?: number
}

const SPECIALIZATIONS = [
  { value: 'vedic_astrology', label: 'Vedic Astrology' },
  { value: 'western_astrology', label: 'Western Astrology' },
  { value: 'numerology', label: 'Numerology' },
  { value: 'tarot', label: 'Tarot Reading' },
  { value: 'palmistry', label: 'Palmistry' },
  { value: 'vastu', label: 'Vastu Shastra' },
  { value: 'gemology', label: 'Gemology' },
  { value: 'horoscope_matching', label: 'Horoscope Matching' },
  { value: 'career_guidance', label: 'Career Guidance' },
  { value: 'relationship_counseling', label: 'Relationship Counseling' },
  { value: 'health_astrology', label: 'Health Astrology' },
  { value: 'financial_astrology', label: 'Financial Astrology' },
  { value: 'spiritual_guidance', label: 'Spiritual Guidance' }
]

const LANGUAGES = [
  { value: 'english', label: 'English' },
  { value: 'hindi', label: 'Hindi' },
  { value: 'sanskrit', label: 'Sanskrit' },
  { value: 'tamil', label: 'Tamil' },
  { value: 'telugu', label: 'Telugu' },
  { value: 'bengali', label: 'Bengali' },
  { value: 'marathi', label: 'Marathi' },
  { value: 'gujarati', label: 'Gujarati' },
  { value: 'kannada', label: 'Kannada' },
  { value: 'malayalam', label: 'Malayalam' }
]

const CERTIFICATION_TYPES = [
  { value: 'diploma', label: 'Diploma' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'degree', label: 'Degree' },
  { value: 'professional_certification', label: 'Professional Certification' },
  { value: 'traditional_training', label: 'Traditional Training' }
]

export default function SignUpPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()
  
  // Common fields
  const [role, setRole] = useState<UserRole>('user')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  
  // Practitioner-specific fields
  const [professionalTitle, setProfessionalTitle] = useState('')
  const [bio, setBio] = useState('')
  const [specializations, setSpecializations] = useState<string[]>([])
  const [experienceYears, setExperienceYears] = useState<number>(0)
  const [certificationType, setCertificationType] = useState('')
  const [issuingAuthority, setIssuingAuthority] = useState('')
  const [languages, setLanguages] = useState<string[]>(['english'])
  const [pricePerHour, setPricePerHour] = useState<number>(1000)
  
  // UI state
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [currentStep, setCurrentStep] = useState(1)

  // Redirect if already logged in
  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/dashboard')
    }
  }, [isAuthenticated, router])

  const validatePassword = (): boolean => {
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return false
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return false
    }

    if (password.length > 71) {
      setError('Password must be 71 characters or less (bcrypt safe limit)')
      return false
    }

    if (!/[A-Z]/.test(password)) {
      setError('Password must contain at least one uppercase letter')
      return false
    }

    if (!/[a-z]/.test(password)) {
      setError('Password must contain at least one lowercase letter')
      return false
    }

    if (!/[0-9]/.test(password)) {
      setError('Password must contain at least one number')
      return false
    }

    return true
  }

  const validatePractitionerFields = (): boolean => {
    if (!professionalTitle.trim()) {
      setError('Professional title is required')
      return false
    }

    if (!bio.trim() || bio.length < 50) {
      setError('Bio must be at least 50 characters')
      return false
    }

    if (specializations.length === 0) {
      setError('At least one specialization is required')
      return false
    }

    if (experienceYears < 0) {
      setError('Experience years must be a positive number')
      return false
    }

    if (!certificationType) {
      setError('Certification type is required')
      return false
    }

    if (!issuingAuthority.trim()) {
      setError('Issuing authority is required')
      return false
    }

    if (languages.length === 0) {
      setError('At least one language is required')
      return false
    }

    return true
  }

  const handleNextStep = () => {
    setError('')
    
    if (currentStep === 1) {
      if (!validatePassword()) {
        return
      }
      setCurrentStep(2)
    } else if (currentStep === 2 && role === 'practitioner') {
      if (!validatePractitionerFields()) {
        return
      }
      setCurrentStep(3)
    }
  }

  const handlePrevStep = () => {
    setError('')
    setCurrentStep(currentStep - 1)
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    if (!validatePassword()) {
      setLoading(false)
      return
    }

    if (role === 'practitioner' && !validatePractitionerFields()) {
      setLoading(false)
      return
    }

    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      
      // Generate unique username from email with timestamp to prevent collisions
      const emailPrefix = email.split('@')[0].toLowerCase().replace(/[^a-z0-9]/g, '')
      const timestamp = Date.now().toString().slice(-6)
      const uniqueUsername = `${emailPrefix}${timestamp}`.slice(0, 50)
      
      let registrationData: UserRegistrationData | PractitionerRegistrationData
      
      if (role === 'user') {
        registrationData = {
          username: uniqueUsername,
          email: email,
          password: password,
          full_name: name,
          role: 'user'
        }
      } else {
        registrationData = {
          username: uniqueUsername,
          email: email,
          password: password,
          full_name: name,
          role: 'practitioner',
          professional_title: professionalTitle,
          bio: bio,
          specializations: specializations,
          experience_years: experienceYears,
          certification_details: {
            certification_type: certificationType,
            issuing_authority: issuingAuthority
          },
          languages: languages,
          price_per_hour: pricePerHour > 0 ? pricePerHour : undefined
        }
      }
      
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000)
      
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registrationData),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)

      if (!response.ok) {
        const data = await response.json()
        
        if (response.status === 429) {
          setError('Too many signup attempts. Please wait a minute and try again.')
          return
        }
        
        // Handle structured error response
        let errorMessage = 'Failed to create account'
        if (data.detail) {
          errorMessage = data.detail
        } else if (data.error && data.error.details) {
          const details = data.error.details
          if (Array.isArray(details) && details.length > 0) {
            errorMessage = details[0].message || errorMessage
          }
        } else if (data.message) {
          errorMessage = data.message
        }
        
        setError(errorMessage)
        return
      }

      const responseData = await response.json()
      setSuccess(true)
      
      // Show appropriate success message based on role
      if (role === 'practitioner') {
        showToast('Practitioner account created! Your account is pending verification. You can login and complete your profile.', 'success')
      } else {
        showToast('Account created successfully! You can now login.', 'success')
      }
      
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        setError('Request timed out. Please check your connection and try again.')
      } else {
        setError('Signup failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const toggleSpecialization = (spec: string) => {
    setSpecializations(prev => 
      prev.includes(spec) 
        ? prev.filter(s => s !== spec)
        : [...prev, spec]
    )
  }

  const toggleLanguage = (lang: string) => {
    setLanguages(prev => 
      prev.includes(lang) 
        ? prev.filter(l => l !== lang)
        : [...prev, lang]
    )
  }

  const renderRoleSelection = () => (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-white mb-4">Choose Your Account Type</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          type="button"
          onClick={() => setRole('user')}
          className={`p-6 rounded-lg border-2 transition-all ${
            role === 'user'
              ? 'border-purple-500 bg-purple-500/10'
              : 'border-slate-600 bg-slate-800/50 hover:border-slate-500'
          }`}
        >
          <User className="w-8 h-8 mx-auto mb-3 text-purple-400" />
          <h3 className="font-semibold text-white mb-2">Regular User</h3>
          <p className="text-sm text-slate-400">
            Get personalized astrology readings and consultations
          </p>
        </button>
        
        <button
          type="button"
          onClick={() => setRole('practitioner')}
          className={`p-6 rounded-lg border-2 transition-all ${
            role === 'practitioner'
              ? 'border-purple-500 bg-purple-500/10'
              : 'border-slate-600 bg-slate-800/50 hover:border-slate-500'
          }`}
        >
          <UserCheck className="w-8 h-8 mx-auto mb-3 text-purple-400" />
          <h3 className="font-semibold text-white mb-2">Practitioner</h3>
          <p className="text-sm text-slate-400">
            Offer astrology services and consultations to users
          </p>
        </button>
      </div>
    </div>
  )

  const renderBasicInfo = () => (
    <div className="space-y-5">
      <h2 className="text-xl font-semibold text-white mb-4">Basic Information</h2>
      
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-slate-300 mb-2">
          Full Name *
        </label>
        <div className="relative">
          <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
            placeholder="John Doe"
            disabled={loading || success}
            autoComplete="name"
          />
        </div>
      </div>

      <div>
        <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
          Email Address *
        </label>
        <div className="relative">
          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
            placeholder="you@example.com"
            disabled={loading || success}
            autoComplete="email"
          />
        </div>
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
          Password *
        </label>
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            id="password"
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            maxLength={71}
            className="w-full pl-11 pr-11 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
            placeholder="••••••••"
            disabled={loading || success}
            autoComplete="new-password"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300 transition focus:outline-none"
            tabIndex={-1}
          >
            {showPassword ? (
              <EyeOff className="h-5 w-5" />
            ) : (
              <Eye className="h-5 w-5" />
            )}
          </button>
        </div>
        <p className="mt-1 text-xs text-slate-500">8-72 characters, must include uppercase, lowercase, and number</p>
      </div>

      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-300 mb-2">
          Confirm Password *
        </label>
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            id="confirmPassword"
            type={showConfirmPassword ? "text" : "password"}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            className="w-full pl-11 pr-11 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
            placeholder="••••••••"
            disabled={loading || success}
            autoComplete="new-password"
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300 transition focus:outline-none"
            tabIndex={-1}
          >
            {showConfirmPassword ? (
              <EyeOff className="h-5 w-5" />
            ) : (
              <Eye className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  )

  const renderPractitionerInfo = () => (
    <div className="space-y-5">
      <h2 className="text-xl font-semibold text-white mb-4">Professional Information</h2>
      
      <div>
        <label htmlFor="professionalTitle" className="block text-sm font-medium text-slate-300 mb-2">
          Professional Title *
        </label>
        <div className="relative">
          <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            id="professionalTitle"
            type="text"
            value={professionalTitle}
            onChange={(e) => setProfessionalTitle(e.target.value)}
            required
            className="w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
            placeholder="e.g., Vedic Astrologer, Tarot Reader"
            disabled={loading || success}
          />
        </div>
      </div>

      <div>
        <label htmlFor="bio" className="block text-sm font-medium text-slate-300 mb-2">
          Professional Bio * (minimum 50 characters)
        </label>
        <div className="relative">
          <FileText className="absolute left-3 top-3 h-5 w-5 text-slate-400" />
          <textarea
            id="bio"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            required
            minLength={50}
            rows={4}
            className="w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition resize-none"
            placeholder="Describe your experience, expertise, and approach to astrology..."
            disabled={loading || success}
          />
        </div>
        <p className="mt-1 text-xs text-slate-500">{bio.length}/50 characters minimum</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Specializations * (select at least one)
        </label>
        <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
          {SPECIALIZATIONS.map((spec) => (
            <button
              key={spec.value}
              type="button"
              onClick={() => toggleSpecialization(spec.value)}
              className={`p-2 text-sm rounded-lg border transition-all ${
                specializations.includes(spec.value)
                  ? 'border-purple-500 bg-purple-500/10 text-purple-300'
                  : 'border-slate-600 bg-slate-800/50 text-slate-300 hover:border-slate-500'
              }`}
            >
              {spec.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="experienceYears" className="block text-sm font-medium text-slate-300 mb-2">
            Experience (years) *
          </label>
          <div className="relative">
            <Clock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <input
              id="experienceYears"
              type="number"
              min="0"
              max="50"
              value={experienceYears}
              onChange={(e) => setExperienceYears(parseInt(e.target.value) || 0)}
              required
              className="w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              placeholder="5"
              disabled={loading || success}
            />
          </div>
        </div>

        <div>
          <label htmlFor="pricePerHour" className="block text-sm font-medium text-slate-300 mb-2">
            Price per Hour (₹)
          </label>
          <div className="relative">
            <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <input
              id="pricePerHour"
              type="number"
              min="0"
              step="100"
              value={pricePerHour}
              onChange={(e) => setPricePerHour(parseInt(e.target.value) || 0)}
              className="w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              placeholder="1000"
              disabled={loading || success}
            />
          </div>
        </div>
      </div>
    </div>
  )

  const renderCertificationInfo = () => (
    <div className="space-y-5">
      <h2 className="text-xl font-semibold text-white mb-4">Certification & Languages</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="certificationType" className="block text-sm font-medium text-slate-300 mb-2">
            Certification Type *
          </label>
          <div className="relative">
            <Award className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <select
              id="certificationType"
              value={certificationType}
              onChange={(e) => setCertificationType(e.target.value)}
              required
              className="w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              disabled={loading || success}
            >
              <option value="">Select certification type</option>
              {CERTIFICATION_TYPES.map((cert) => (
                <option key={cert.value} value={cert.value}>
                  {cert.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label htmlFor="issuingAuthority" className="block text-sm font-medium text-slate-300 mb-2">
            Issuing Authority *
          </label>
          <input
            id="issuingAuthority"
            type="text"
            value={issuingAuthority}
            onChange={(e) => setIssuingAuthority(e.target.value)}
            required
            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
            placeholder="e.g., Indian Astrology Institute"
            disabled={loading || success}
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Languages * (select at least one)
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-32 overflow-y-auto">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.value}
              type="button"
              onClick={() => toggleLanguage(lang.value)}
              className={`p-2 text-sm rounded-lg border transition-all ${
                languages.includes(lang.value)
                  ? 'border-purple-500 bg-purple-500/10 text-purple-300'
                  : 'border-slate-600 bg-slate-800/50 text-slate-300 hover:border-slate-500'
              }`}
            >
              <Globe className="w-4 h-4 inline mr-1" />
              {lang.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )

  const getStepContent = () => {
    if (currentStep === 1) {
      return (
        <>
          {renderRoleSelection()}
          {renderBasicInfo()}
        </>
      )
    } else if (currentStep === 2 && role === 'practitioner') {
      return renderPractitionerInfo()
    } else if (currentStep === 3 && role === 'practitioner') {
      return renderCertificationInfo()
    }
    return null
  }

  const isLastStep = () => {
    if (role === 'user') return currentStep === 1
    return currentStep === 3
  }

  const canProceed = () => {
    if (currentStep === 1) {
      return name && email && password && confirmPassword && role
    } else if (currentStep === 2 && role === 'practitioner') {
      return professionalTitle && bio.length >= 50 && specializations.length > 0 && experienceYears >= 0
    } else if (currentStep === 3 && role === 'practitioner') {
      return certificationType && issuingAuthority && languages.length > 0
    }
    return false
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 relative bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Community.gif as animated background */}
      <div className="fixed inset-0 z-0">
        <Image
          src="/Community.gif"
          alt="Background"
          fill={true}
          className="object-cover opacity-20"
          priority={true}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900/85 via-slate-800/90 to-slate-900/85"></div>
      </div>

      <div className="w-full max-w-2xl relative z-10">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <Link href="/login" className="inline-flex items-center justify-center space-x-2 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center shadow-lg shadow-yellow-500/50">
              <Star className="w-7 h-7 text-white" />
            </div>
            <span className="text-3xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
              YatinVeda
            </span>
          </Link>
          <h1 className="text-3xl font-bold text-white mb-2">✨ Create Your Account</h1>
          <p className="text-slate-400">
            {role === 'practitioner' 
              ? 'Join as a practitioner and share your expertise' 
              : 'Join YatinVeda and start your astrology journey'
            }
          </p>
        </div>

        {/* Progress indicator for practitioners */}
        {role === 'practitioner' && (
          <div className="mb-8">
            <div className="flex items-center justify-center space-x-4">
              {[1, 2, 3].map((step) => (
                <div key={step} className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    step <= currentStep 
                      ? 'bg-purple-500 text-white' 
                      : 'bg-slate-600 text-slate-400'
                  }`}>
                    {step}
                  </div>
                  {step < 3 && (
                    <div className={`w-12 h-0.5 ${
                      step < currentStep ? 'bg-purple-500' : 'bg-slate-600'
                    }`} />
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-center mt-2">
              <span className="text-sm text-slate-400">
                Step {currentStep} of 3
              </span>
            </div>
          </div>
        )}

        {/* Signup Form */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-8 shadow-2xl backdrop-blur-sm">
          {error && (
            <div className="mb-6 flex items-start space-x-3 rounded-lg bg-red-500/10 border border-red-500/30 p-4 animate-in fade-in slide-in-from-top-3 duration-300">
              <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-200">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-6 flex items-start space-x-3 rounded-lg bg-green-500/10 border border-green-500/30 p-4 animate-in fade-in slide-in-from-top-3 duration-300">
              <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-200">
                {role === 'practitioner' 
                  ? 'Practitioner account created! Your account is pending verification. Redirecting to login...'
                  : 'Account created! Redirecting to login...'
                }
              </p>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {getStepContent()}

            <div className="mt-8 flex justify-between">
              {currentStep > 1 && (
                <button
                  type="button"
                  onClick={handlePrevStep}
                  disabled={loading || success}
                  className="px-6 py-3 bg-slate-600 hover:bg-slate-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-slate-500"
                >
                  Previous
                </button>
              )}

              <div className="ml-auto">
                {!isLastStep() ? (
                  <button
                    type="button"
                    onClick={handleNextStep}
                    disabled={!canProceed() || loading || success}
                    className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-slate-600 disabled:to-slate-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-slate-900 shadow-lg shadow-purple-500/30 hover:shadow-purple-500/50 hover:scale-[1.02]"
                  >
                    Next
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={!canProceed() || loading || success}
                    className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-slate-600 disabled:to-slate-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-slate-900 shadow-lg shadow-purple-500/30 hover:shadow-purple-500/50 hover:scale-[1.02]"
                  >
                    {loading ? (
                      <span className="flex items-center justify-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Creating account...
                      </span>
                    ) : success ? (
                      '✓ Account Created!'
                    ) : (
                      '🚀 Create Account'
                    )}
                  </button>
                )}
              </div>
            </div>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-400 text-sm">
              Already have an account?{' '}
              <Link
                href="/login"
                className="text-purple-400 hover:text-purple-300 font-medium transition hover:underline"
              >
                Sign In
              </Link>
            </p>
          </div>
        </div>

        <div className="mt-8 text-center">
          <p className="text-slate-500 text-sm">
            By creating an account, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  )
}
