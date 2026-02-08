'use client'

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'
import { apiClient } from '@/lib/api-client'
import { useRouter } from 'next/navigation'
import { AuthGuard } from '@/components/auth-guard'
import Script from 'next/script'
import {
  Star, Clock, Video, Phone, MessageSquare,
  ChevronRight, CheckCircle2, ArrowLeft, MessageCircle
} from 'lucide-react'
import BackButton from '@/components/BackButton'

interface Guru {
  id: number
  name: string
  title: string
  bio: string
  avatar_url: string
  specializations: string[]
  languages: string[]
  experience_years: number
  rating: number
  total_sessions: number
  price_per_hour: number
  match_score?: number
}

interface QuizQuestion {
  id: number
  question: string
  options: { value: string; label: string }[]
  category: string
}

interface TimeSlot {
  time: string
  available: boolean
}

interface Availability {
  date: string
  day: string
  slots: TimeSlot[]
}

interface PreviousBooking {
  id: number
  guru_id: number
  guru_name: string
  booking_date: string
  time_slot: string
  duration: number
  session_type: string
  status: string
}

interface BookingResponseApi {
  id: number
  guru_id: number
  guru_name: string
  booking_date: string
  time_slot: string
  duration_minutes: number
  session_type: string
  status: string
  payment_status: string
  payment_amount: number
  meeting_link: string | null
  created_at: string
}

function BookAppointmentContent() {
  const { accessToken, csrfToken } = useAuth()
  const { showToast } = useToast()
  const router = useRouter()
  
  // State management
  const [step, setStep] = useState<'quiz' | 'results' | 'booking'>('quiz')
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestion[]>([])
  const [quizResponses, setQuizResponses] = useState<Record<number, string>>({})
  const [matchedGurus, setMatchedGurus] = useState<Guru[]>([])
  const [selectedGuru, setSelectedGuru] = useState<Guru | null>(null)
  const [availability, setAvailability] = useState<Availability[]>([])
  const [selectedDate, setSelectedDate] = useState<string>('')
  const [selectedSlot, setSelectedSlot] = useState<string>('')
  const [duration, setDuration] = useState<number>(60)
  const [sessionType, setSessionType] = useState<'video_call' | 'audio_call' | 'chat'>('video_call')
  const [bookingNotes, setBookingNotes] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [previousBookings, setPreviousBookings] = useState<PreviousBooking[]>([])

  const fetchQuiz = useCallback(async () => {
    try {
      const data = await apiClient.get<{ questions: QuizQuestion[] }>('/api/v1/guru-booking/quiz')
      setQuizQuestions(data.questions)
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to load quiz'
      showToast(errorMsg, 'error')
      console.error('Error fetching quiz:', error)
    }
  }, [showToast])

  const fetchPreviousBookings = useCallback(async () => {
    if (!accessToken) return
    try {
      const data = await apiClient.get<PreviousBooking[]>('/api/v1/guru-booking/bookings')
      setPreviousBookings(data)
    } catch (error) {
      console.error('Error fetching bookings:', error)
    }
  }, [accessToken, showToast])

  // Fetch quiz questions on mount
  useEffect(() => {
    fetchQuiz()
    if (accessToken) {
      fetchPreviousBookings()
    }
  }, [accessToken, fetchQuiz, fetchPreviousBookings])

  const handleQuizSubmit = async () => {
    if (Object.keys(quizResponses).length < quizQuestions.length) {
      showToast('Please answer all questions', 'error')
      return
    }

    setLoading(true)
    try {
      const responses = Object.entries(quizResponses).map(([questionId, answer]) => ({
        question_id: parseInt(questionId),
        answer
      }))

      const data = await apiClient.post<Guru[]>('/api/v1/guru-booking/match', { responses })
      setMatchedGurus(data)
      setStep('results')
      showToast('Found matching gurus!', 'success')
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to find matches'
      showToast(errorMsg, 'error')
      console.error('Error submitting quiz:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectGuru = async (guru: Guru) => {
    setSelectedGuru(guru)
    setLoading(true)
    
    try {
      const data = await apiClient.get<{ availability: Availability[] }>(
        `/api/v1/guru-booking/gurus/${guru.id}/availability`
      )
      setAvailability(data.availability)
      setStep('booking')
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to load availability'
      showToast(errorMsg, 'error')
      console.error('Error fetching availability:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleBooking = async () => {
    if (!selectedDate || !selectedSlot || !accessToken) {
      showToast('Please select a date and time slot', 'error')
      return
    }

    setLoading(true)
    try {
      const responses = Object.entries(quizResponses).map(([questionId, answer]) => ({
        question_id: parseInt(questionId),
        answer
      }))

      const bookingData = {
        guru_id: selectedGuru?.id,
        booking_date: selectedDate,
        time_slot: selectedSlot,
        duration_minutes: duration,
        session_type: sessionType,
        quiz_responses: responses,
        notes: bookingNotes
      }

      const booking = await apiClient.post<BookingResponseApi>(
        '/api/v1/guru-booking/bookings',
        bookingData
      )

      await handlePaymentFlow(booking)
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to create booking'
      showToast(errorMsg, 'error')
      console.error('Error creating booking:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePaymentFlow = async (booking: BookingResponseApi) => {
    if (!accessToken) {
      showToast(`Booking created (ID: ${booking.id}) but payment could not start. Please log in again.`, 'error')
      router.push('/dashboard')
      return
    }

    try {
      const orderData = await apiClient.post<{
        order_id: string
        amount: number
        currency: string
        key_id: string
      }>('/api/v1/payments/create-order', {
        booking_id: booking.id,
        amount: booking.payment_amount,
        notes: {
          source: 'booking-page',
          guru_id: booking.guru_id,
          guru_name: booking.guru_name,
        }
      })

      if (typeof window === 'undefined' || !window.Razorpay) {
        showToast('Payment gateway unavailable. Please refresh or try later.', 'error')
        router.push('/dashboard')
        return
      }

      type RazorpayHandlerResponse = {
        razorpay_payment_id: string
        razorpay_order_id: string
        razorpay_signature: string
      }

      const options: RazorpayOptions = {
        key: orderData.key_id,
        amount: orderData.amount,
        currency: orderData.currency,
        name: 'YatinVeda',
        description: `Consultation booking #${booking.id}`,
        order_id: orderData.order_id,
        handler: async (response: unknown) => {
          const r = response as RazorpayHandlerResponse
          try {
            await apiClient.post('/api/v1/payments/verify-payment', {
              order_id: r.razorpay_order_id,
              payment_id: r.razorpay_payment_id,
              signature: r.razorpay_signature,
              booking_id: booking.id,
            })

            showToast('Payment successful! Your session is confirmed.', 'success')
          } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Payment verification failed'
            showToast(`${errorMsg}. If amount was deducted, contact support.`, 'error')
            console.error('Payment verification failed:', err)
          } finally {
            router.push('/dashboard')
          }
        },
        prefill: {
          name: 'YatinVeda User',
          email: '',
          contact: '',
        },
        theme: {
          color: '#4f46e5',
        },
      }

      const rzp = new window.Razorpay(options)
      rzp.open()
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to initiate payment'
      showToast(`${errorMsg}. Please complete payment from your dashboard.`, 'error')
      console.error('Unexpected error during payment flow:', error)
      router.push('/dashboard')
    }
  }

  if (!accessToken) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-purple-900 to-slate-900 flex items-center justify-center p-4">
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-12 text-center max-w-md">
          <MessageCircle className="w-16 h-16 text-blue-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Please Login</h2>
          <p className="text-slate-400 mb-6">You need to be logged in to book an appointment</p>
          <a href="/login" className="inline-block bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold px-6 py-3 rounded-xl hover:shadow-lg transition">
            Go to Login
          </a>
        </div>
      </div>
    )
  }

  return (
    <>
      <Script src="https://checkout.razorpay.com/v1/checkout.js" strategy="afterInteractive" />
      <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-purple-900 to-slate-900 p-4 md:p-8">
        <div className="max-w-6xl mx-auto">
          <BackButton />
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Book a Session with Our Expert Gurus
          </h1>
          <p className="text-slate-300 text-lg">
            Take a quick quiz to find the perfect guru for your needs
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="flex justify-center items-center mb-8 gap-4">
          <div className={`flex items-center gap-2 ${step === 'quiz' ? 'text-blue-400' : 'text-green-400'}`}>
            {step !== 'quiz' ? <CheckCircle2 className="w-6 h-6" /> : <div className="w-6 h-6 rounded-full border-2 border-current" />}
            <span className="font-medium">Quiz</span>
          </div>
          <ChevronRight className="w-5 h-5 text-slate-500" />
          <div className={`flex items-center gap-2 ${step === 'results' ? 'text-blue-400' : step === 'booking' ? 'text-green-400' : 'text-slate-500'}`}>
            {step === 'booking' ? <CheckCircle2 className="w-6 h-6" /> : <div className="w-6 h-6 rounded-full border-2 border-current" />}
            <span className="font-medium">Match Results</span>
          </div>
          <ChevronRight className="w-5 h-5 text-slate-500" />
          <div className={`flex items-center gap-2 ${step === 'booking' ? 'text-blue-400' : 'text-slate-500'}`}>
            <div className="w-6 h-6 rounded-full border-2 border-current" />
            <span className="font-medium">Book Appointment</span>
          </div>
        </div>

        {/* Quiz Step */}
        {step === 'quiz' && (
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-8">
            <h2 className="text-2xl font-bold text-white mb-6">Find Your Perfect Guru</h2>
            
            <div className="space-y-6">
              {quizQuestions.map((question, index) => (
                <div key={question.id} className="bg-slate-900/50 rounded-xl p-6 border border-slate-700/30">
                  <p className="text-lg font-semibold text-white mb-4">
                    {index + 1}. {question.question}
                  </p>
                  <div className="space-y-3">
                    {question.options.map((option) => (
                      <label
                        key={option.value}
                        className={`flex items-center gap-3 p-4 rounded-lg border-2 cursor-pointer transition ${
                          quizResponses[question.id] === option.value
                            ? 'border-blue-500 bg-blue-500/10'
                            : 'border-slate-700/50 hover:border-slate-600 bg-slate-800/30'
                        }`}
                      >
                        <input
                          type="radio"
                          name={`question-${question.id}`}
                          value={option.value}
                          checked={quizResponses[question.id] === option.value}
                          onChange={(e) => setQuizResponses({ ...quizResponses, [question.id]: e.target.value })}
                          className="w-4 h-4"
                        />
                        <span className="text-slate-200">{option.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={handleQuizSubmit}
              disabled={loading || Object.keys(quizResponses).length < quizQuestions.length}
              className="mt-8 w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold py-4 rounded-xl hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Finding Your Match...' : 'Find My Perfect Guru'}
            </button>
          </div>
        )}

        {/* Results Step */}
        {step === 'results' && (
          <div>
            <button
              onClick={() => setStep('quiz')}
              className="mb-6 flex items-center gap-2 text-slate-400 hover:text-white transition"
            >
              <ArrowLeft className="w-5 h-5" />
              Retake Quiz
            </button>

            <h2 className="text-3xl font-bold text-white mb-2">Your Best Matches</h2>
            <p className="text-slate-400 mb-6">Based on your responses, here are the gurus best suited for you</p>

            <div className="grid md:grid-cols-2 gap-6">
              {matchedGurus.map((guru) => (
                <div
                  key={guru.id}
                  className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-6 hover:border-blue-500/50 transition"
                >
                  {/* Match Score Badge */}
                  {guru.match_score && (
                    <div className="inline-block bg-green-500/20 border border-green-500/50 text-green-400 px-3 py-1 rounded-full text-sm font-semibold mb-4">
                      {guru.match_score}% Match
                    </div>
                  )}

                  <div className="flex items-start gap-4 mb-4">
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-2xl font-bold">
                      {guru.name.charAt(0)}
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-white">{guru.name}</h3>
                      <p className="text-slate-400 text-sm">{guru.title}</p>
                    </div>
                  </div>

                  <p className="text-slate-300 text-sm mb-4 line-clamp-2">{guru.bio}</p>

                  <div className="flex flex-wrap gap-2 mb-4">
                    {guru.specializations.slice(0, 3).map((spec) => (
                      <span key={spec} className="bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full text-xs">
                        {spec}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                      <span className="text-white font-semibold">{guru.rating}</span>
                      <span className="text-slate-400 text-sm">({guru.total_sessions} sessions)</span>
                    </div>
                    <div className="text-right">
                      <div className="text-slate-400 text-xs">Starting at</div>
                      <div className="text-white font-bold text-lg">₹{guru.price_per_hour}/hr</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-slate-400 text-sm mb-4">
                    <Clock className="w-4 h-4" />
                    <span>{guru.experience_years} years experience</span>
                  </div>

                  <button
                    onClick={() => handleSelectGuru(guru)}
                    className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold py-3 rounded-xl hover:shadow-lg transition"
                  >
                    Book Appointment
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Booking Step */}
        {step === 'booking' && selectedGuru && (
          <div>
            <button
              onClick={() => setStep('results')}
              className="mb-6 flex items-center gap-2 text-slate-400 hover:text-white transition"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Results
            </button>

            <div className="grid lg:grid-cols-3 gap-6">
              {/* Left: Guru Info */}
              <div className="lg:col-span-1">
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-6 sticky top-4">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-2xl font-bold">
                      {selectedGuru.name.charAt(0)}
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-white">{selectedGuru.name}</h3>
                      <p className="text-slate-400 text-sm">{selectedGuru.title}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 mb-4">
                    <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                    <span className="text-white">{selectedGuru.rating}</span>
                    <span className="text-slate-400 text-sm">• {selectedGuru.total_sessions} sessions</span>
                  </div>

                  <div className="mb-4">
                    <div className="text-slate-400 text-sm mb-1">Rate</div>
                    <div className="text-2xl font-bold text-white">₹{selectedGuru.price_per_hour}/hr</div>
                  </div>

                  {duration && (
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
                      <div className="text-slate-300 text-sm mb-1">Estimated Cost</div>
                      <div className="text-2xl font-bold text-white">₹{Math.round((selectedGuru.price_per_hour / 60) * duration)}</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Right: Booking Form */}
              <div className="lg:col-span-2">
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-6">
                  <h3 className="text-2xl font-bold text-white mb-6">Select Date & Time</h3>

                  {/* Calendar */}
                  <div className="mb-6">
                    <label className="text-slate-300 font-medium mb-3 block">Available Dates</label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {availability.map((dayAvail) => (
                        <button
                          key={dayAvail.date}
                          onClick={() => setSelectedDate(dayAvail.date)}
                          className={`p-4 rounded-xl border-2 transition text-center ${
                            selectedDate === dayAvail.date
                              ? 'border-blue-500 bg-blue-500/10'
                              : 'border-slate-700/50 hover:border-slate-600 bg-slate-900/30'
                          }`}
                        >
                          <div className="text-white font-semibold">{new Date(dayAvail.date).getDate()}</div>
                          <div className="text-slate-400 text-xs">{dayAvail.day.slice(0, 3)}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Time Slots */}
                  {selectedDate && (
                    <div className="mb-6">
                      <label className="text-slate-300 font-medium mb-3 block">Available Time Slots</label>
                      <div className="grid grid-cols-3 md:grid-cols-4 gap-3">
                        {availability
                          .find((d) => d.date === selectedDate)
                          ?.slots.filter((s) => s.available)
                          .map((slot) => (
                            <button
                              key={slot.time}
                              onClick={() => setSelectedSlot(slot.time)}
                              className={`p-3 rounded-xl border-2 transition text-center ${
                                selectedSlot === slot.time
                                  ? 'border-blue-500 bg-blue-500/10 text-white'
                                  : 'border-slate-700/50 hover:border-slate-600 bg-slate-900/30 text-slate-300'
                              }`}
                            >
                              <div className="text-sm font-medium">{slot.time.split('-')[0]}</div>
                            </button>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Duration */}
                  <div className="mb-6">
                    <label className="text-slate-300 font-medium mb-3 block">Session Duration</label>
                    <div className="grid grid-cols-3 gap-3">
                      {[30, 60, 90].map((dur) => (
                        <button
                          key={dur}
                          onClick={() => setDuration(dur)}
                          className={`p-4 rounded-xl border-2 transition ${
                            duration === dur
                              ? 'border-blue-500 bg-blue-500/10 text-white'
                              : 'border-slate-700/50 hover:border-slate-600 bg-slate-900/30 text-slate-300'
                          }`}
                        >
                          {dur} min
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Session Type */}
                  <div className="mb-6">
                    <label className="text-slate-300 font-medium mb-3 block">Session Type</label>
                    <div className="grid grid-cols-3 gap-3">
                      <button
                        onClick={() => setSessionType('video_call')}
                        className={`p-4 rounded-xl border-2 transition flex flex-col items-center gap-2 ${
                          sessionType === 'video_call'
                            ? 'border-blue-500 bg-blue-500/10'
                            : 'border-slate-700/50 hover:border-slate-600 bg-slate-900/30'
                        }`}
                      >
                        <Video className="w-6 h-6" />
                        <span className="text-sm">Video Call</span>
                      </button>
                      <button
                        onClick={() => setSessionType('audio_call')}
                        className={`p-4 rounded-xl border-2 transition flex flex-col items-center gap-2 ${
                          sessionType === 'audio_call'
                            ? 'border-blue-500 bg-blue-500/10'
                            : 'border-slate-700/50 hover:border-slate-600 bg-slate-900/30'
                        }`}
                      >
                        <Phone className="w-6 h-6" />
                        <span className="text-sm">Audio Call</span>
                      </button>
                      <button
                        onClick={() => setSessionType('chat')}
                        className={`p-4 rounded-xl border-2 transition flex flex-col items-center gap-2 ${
                          sessionType === 'chat'
                            ? 'border-blue-500 bg-blue-500/10'
                            : 'border-slate-700/50 hover:border-slate-600 bg-slate-900/30'
                        }`}
                      >
                        <MessageSquare className="w-6 h-6" />
                        <span className="text-sm">Chat</span>
                      </button>
                    </div>
                  </div>

                  {/* Notes */}
                  <div className="mb-6">
                    <label className="text-slate-300 font-medium mb-3 block">Additional Notes (Optional)</label>
                    <textarea
                      value={bookingNotes}
                      onChange={(e) => setBookingNotes(e.target.value)}
                      placeholder="Share any specific concerns or questions..."
                      className="w-full bg-slate-900/50 border border-slate-700/50 rounded-xl p-4 text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                      rows={4}
                    />
                  </div>

                  {/* Book Button */}
                  <button
                    onClick={handleBooking}
                    disabled={loading || !selectedDate || !selectedSlot}
                    className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold py-4 rounded-xl hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Processing...' : 'Confirm Booking & Pay'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Previous Bookings */}
        {previousBookings.length > 0 && step === 'quiz' && (
          <div className="mt-12 bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-8">
            <h2 className="text-2xl font-bold text-white mb-6">Your Previous Bookings</h2>
            <div className="space-y-4">
              {previousBookings.slice(0, 3).map((booking) => (
                <div key={booking.id} className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/30 flex items-center justify-between">
                  <div>
                    <h3 className="text-white font-semibold">{booking.guru_name}</h3>
                    <p className="text-slate-400 text-sm">
                      {new Date(booking.booking_date).toLocaleDateString()} • {booking.time_slot}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm ${
                    booking.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                    booking.status === 'confirmed' ? 'bg-blue-500/20 text-blue-400' :
                    'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {booking.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
        </div>
      </div>
    </>
  )
}

export default function BookAppointmentPage() {
  return (
    <AuthGuard>
      <BookAppointmentContent />
    </AuthGuard>
  )
}
