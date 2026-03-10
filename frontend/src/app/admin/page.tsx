'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Shield, Users, BookOpen, MessageSquare, BarChart3, Eye, UserCog, AlertTriangle, UserCheck, Clock, CheckCircle, XCircle, FileText, Award } from 'lucide-react'
import { AuthGuard } from '@/components/auth-guard'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'
import { useI18n } from '@/lib/i18n'
import { apiClient } from '@/lib/api-client'

interface PendingPractitioner {
  guru_id: number
  user_id: number
  username: string
  email: string
  full_name: string | null
  professional_title: string
  bio: string
  specializations: string[]
  experience_years: number
  certification_details: {
    certification_type: string
    issuing_authority: string
  }
  languages: string[] | null
  price_per_hour: number | null
  created_at: string
  verification_status: string
  is_ready_for_verification: boolean
}

interface VerificationStats {
  total_practitioners: number
  pending_verification: number
  verified: number
  rejected: number
  recent_verifications_30_days: number
  verification_rate: number
}

interface UserDetail {
  id: number
  username: string
  email: string
  full_name: string | null
  is_active: boolean
  is_admin: boolean
  created_at: string
  updated_at: string | null
  last_login: string | null
  total_charts: number
  total_learning_progress: number
  total_chat_messages: number
  completed_lessons: number
  // Optional extra fields returned by backend for detailed view (use optional to be safe)
  password_hash?: string
}

interface SystemStats {
  total_users: number
  active_users: number
  admin_users: number
  total_charts: number
  total_learning_records: number
  completed_lessons: number
  total_chat_messages: number
  completion_rate: number
}

function AdminContent() {
  const router = useRouter()
  const { accessToken } = useAuth()
  const { showToast } = useToast()
  const [users, setUsers] = useState<UserDetail[]>([])
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [pendingPractitioners, setPendingPractitioners] = useState<PendingPractitioner[]>([])
  const [verificationStats, setVerificationStats] = useState<VerificationStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedUser, setSelectedUser] = useState<number | null>(null)
  const [selectedPractitioner, setSelectedPractitioner] = useState<PendingPractitioner | null>(null)
  const [activeTab, setActiveTab] = useState<'users' | 'verification'>('users')
  // More detailed info for a single user (extend later if backend returns extra fields)
  const [userDetails, setUserDetails] = useState<UserDetail | null>(null)
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null)
  const [adminActionError, setAdminActionError] = useState('')
  const { t } = useI18n()

  const fetchData = useCallback(async () => {
    try {
      if (!accessToken) {
        setError('No access token available')
        setLoading(false)
        return
      }

      // First verify admin status via profile endpoint
      const profile = await apiClient.get<{ is_admin: boolean }>('/api/v1/auth/profile')
      
      if (!profile.is_admin) {
        setIsAdmin(false)
        setError('You are signed in, but this account is not an administrator.')
        setLoading(false)
        return
      }
      setIsAdmin(true)

      // Fetch system stats
      const statsData = await apiClient.get<SystemStats>('/api/v1/admin/stats')
      setStats(statsData)

      // Fetch all users
      const usersData = await apiClient.get<UserDetail[]>('/api/v1/admin/users')
      setUsers(usersData)

      // Fetch verification data
      const pendingData = await apiClient.get<PendingPractitioner[]>('/api/v1/admin/pending-verifications')
      setPendingPractitioners(pendingData)

      const verificationStatsData = await apiClient.get<VerificationStats>('/api/v1/admin/verification-stats')
      setVerificationStats(verificationStatsData)

      setLoading(false)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch admin data'
      setError(errorMsg)
      showToast(errorMsg, 'error')
      setLoading(false)
    }
  }, [accessToken, showToast])

  useEffect(() => {
    if (accessToken) {
      fetchData()
    }
  }, [accessToken, fetchData])

  const viewUserDetails = async (userId: number) => {
    try {
      const data = await apiClient.get<UserDetail>(`/api/v1/admin/users/${userId}`)
      setUserDetails(data)
      setSelectedUser(userId)
      setAdminActionError('')
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch user details'
      showToast(errorMsg, 'error')
      console.error('Failed to fetch user details', err)
    }
  }

  const handleToggleAdmin = async (userId: number, makeAdmin: boolean) => {
    try {
      setAdminActionError('')
      
      await apiClient.patch(`/api/v1/admin/users/${userId}/admin-status?make_admin=${makeAdmin}`, {})
      
      // Update local state for list and details
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_admin: makeAdmin } : u))
      setUserDetails(prev => prev ? { ...prev, is_admin: makeAdmin } : prev)
      showToast('Admin status updated successfully', 'success')
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to update admin status'
      setAdminActionError(errorMsg)
      showToast(errorMsg, 'error')
    }
  }

  const handleVerifyPractitioner = async (guruId: number, notes?: string) => {
    try {
      await apiClient.post(`/api/v1/admin/verify/${guruId}`, { notes })
      
      // Remove from pending list
      setPendingPractitioners(prev => prev.filter(p => p.guru_id !== guruId))
      
      // Update verification stats
      if (verificationStats) {
        setVerificationStats(prev => prev ? {
          ...prev,
          pending_verification: prev.pending_verification - 1,
          verified: prev.verified + 1,
          verification_rate: ((prev.verified + 1) / prev.total_practitioners) * 100
        } : null)
      }
      
      showToast('Practitioner verified successfully', 'success')
      setSelectedPractitioner(null)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to verify practitioner'
      showToast(errorMsg, 'error')
    }
  }

  const handleRejectPractitioner = async (guruId: number, reason: string, notes?: string) => {
    try {
      await apiClient.post(`/api/v1/admin/reject/${guruId}`, { reason, notes })
      
      // Remove from pending list
      setPendingPractitioners(prev => prev.filter(p => p.guru_id !== guruId))
      
      // Update verification stats
      if (verificationStats) {
        setVerificationStats(prev => prev ? {
          ...prev,
          pending_verification: prev.pending_verification - 1,
          rejected: prev.rejected + 1
        } : null)
      }
      
      showToast('Practitioner rejected', 'success')
      setSelectedPractitioner(null)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to reject practitioner'
      showToast(errorMsg, 'error')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading admin dashboard...</div>
      </div>
    )
  }

  if (error && isAdmin === false) {
    // Authenticated but not an admin: show a friendly upsell to use the master admin account
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center px-4">
        <div className="bg-slate-900/80 border border-slate-700/70 rounded-2xl p-8 max-w-lg w-full shadow-2xl">
          <div className="flex items-center mb-4">
            <AlertTriangle className="w-6 h-6 text-yellow-400 mr-2" />
            <h2 className="text-yellow-300 text-2xl font-bold">Admin Access Restricted</h2>
          </div>
          <p className="text-slate-200 mb-4">
            {error}
          </p>
          <p className="text-slate-400 text-sm mb-6">
            To access the Admin Dashboard, please sign in using the dedicated administrator account:
          </p>
          <div className="bg-slate-800/70 border border-slate-700 rounded-lg p-4 mb-6 text-sm text-slate-200">
            <p><span className="font-semibold">Username:</span> Yatin</p>
            <p><span className="font-semibold">Email:</span> marcsnuffy@gmail.com</p>
            <p><span className="font-semibold">Password:</span> LeoPolly</p>
          </div>
          <button
            onClick={() => router.push('/login?callbackUrl=/admin')}
            className="w-full py-3 px-4 bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white font-semibold rounded-lg transition-all duration-200 shadow-lg hover:scale-[1.02]"
          >
            Go to Admin Login
          </button>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 max-w-md">
          <h2 className="text-red-400 text-xl font-bold mb-2">Access Denied</h2>
          <p className="text-red-200">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-8 px-4">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-3">
            <Shield className="w-10 h-10 text-yellow-400" />
            <h1 className="text-4xl font-bold text-white">Admin Dashboard</h1>
          </div>

          <Link
            href="/admin/certificate-alerts"
            className="hidden md:inline-block rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 hover:bg-slate-700"
          >
            {t('admin_certificate_alerts', 'Certificate Alerts')}
          </Link>
          <Link
            href="/admin/analytics"
            className="hidden md:inline-block rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 hover:bg-slate-700"
          >
            {t('admin_advanced_analytics', 'Advanced Analytics')}
          </Link>
          
          {/* Tab Navigation */}
          <div className="flex space-x-2 bg-slate-800/50 border border-slate-700 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('users')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'users'
                  ? 'bg-purple-500 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Users className="w-4 h-4 inline mr-2" />
              Users
            </button>
            <button
              onClick={() => setActiveTab('verification')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'verification'
                  ? 'bg-purple-500 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <UserCheck className="w-4 h-4 inline mr-2" />
              Verification
              {pendingPractitioners.length > 0 && (
                <span className="ml-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                  {pendingPractitioners.length}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* System Stats */}
        {stats && activeTab === 'users' && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6" title="Total registered accounts in YatinVeda.">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm">Total Users</p>
                    <p className="text-white text-3xl font-bold">{stats.total_users}</p>
                    <p className="text-xs text-slate-400 mt-1">Active: {stats.active_users} • Admins: {stats.admin_users}</p>
                    <p className="text-[11px] text-slate-500 mt-1">Active users are currently marked as active in the system; admin users can access this dashboard.</p>
                  </div>
                  <Users className="w-10 h-10 text-blue-400" />
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6" title="All charts created across all users.">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm">Total Charts</p>
                    <p className="text-white text-3xl font-bold">{stats.total_charts}</p>
                    <p className="text-[11px] text-slate-500 mt-1">Includes birth charts and other saved chart configurations.</p>
                  </div>
                  <BarChart3 className="w-10 h-10 text-green-400" />
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6" title="Learning progress across all users.">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm">Lessons Completed</p>
                    <p className="text-white text-3xl font-bold">{stats.completed_lessons}</p>
                    <p className="text-xs text-slate-400 mt-1">Records: {stats.total_learning_records}</p>
                    <p className="text-[11px] text-slate-500 mt-1">Each record represents a lesson attempt or progress entry for a user.</p>
                  </div>
                  <BookOpen className="w-10 h-10 text-purple-400" />
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6" title="Total messages exchanged with assistants or chat features.">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm">Chat Messages</p>
                    <p className="text-white text-3xl font-bold">{stats.total_chat_messages}</p>
                    <p className="text-[11px] text-slate-500 mt-1">Helps you see overall conversational engagement.</p>
                  </div>
                  <MessageSquare className="w-10 h-10 text-orange-400" />
                </div>
              </div>
            </div>

            <div className="mb-8 flex items-center justify-between bg-slate-800/60 border border-slate-700 rounded-lg p-4" title="Percentage of completed lessons out of all learning records.">
              <div>
                <p className="text-slate-400 text-sm">Overall Completion Rate</p>
                <p className="text-white text-2xl font-bold">{stats.completion_rate.toFixed(1)}%</p>
                <p className="text-[11px] text-slate-500 mt-1">Good for tracking how effectively users complete the learning content.</p>
              </div>
              <div className="w-full max-w-xs bg-slate-900/70 rounded-full h-3 overflow-hidden border border-slate-700 ml-4">
                <div
                  className="h-full bg-gradient-to-r from-green-400 to-emerald-500"
                  style={{ width: `${Math.min(100, Math.max(0, stats.completion_rate))}%` }}
                />
              </div>
            </div>
          </>
        )}

        {/* Verification Stats */}
        {verificationStats && activeTab === 'verification' && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm">Total Practitioners</p>
                    <p className="text-white text-3xl font-bold">{verificationStats.total_practitioners}</p>
                  </div>
                  <UserCheck className="w-10 h-10 text-blue-400" />
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm">Pending Verification</p>
                    <p className="text-white text-3xl font-bold">{verificationStats.pending_verification}</p>
                  </div>
                  <Clock className="w-10 h-10 text-yellow-400" />
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm">Verified</p>
                    <p className="text-white text-3xl font-bold">{verificationStats.verified}</p>
                  </div>
                  <CheckCircle className="w-10 h-10 text-green-400" />
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm">Rejected</p>
                    <p className="text-white text-3xl font-bold">{verificationStats.rejected}</p>
                  </div>
                  <XCircle className="w-10 h-10 text-red-400" />
                </div>
              </div>
            </div>

            <div className="mb-8 flex items-center justify-between bg-slate-800/60 border border-slate-700 rounded-lg p-4">
              <div>
                <p className="text-slate-400 text-sm">Verification Rate</p>
                <p className="text-white text-2xl font-bold">{verificationStats.verification_rate.toFixed(1)}%</p>
                <p className="text-xs text-slate-400 mt-1">Recent: {verificationStats.recent_verifications_30_days} in last 30 days</p>
              </div>
              <div className="w-full max-w-xs bg-slate-900/70 rounded-full h-3 overflow-hidden border border-slate-700 ml-4">
                <div
                  className="h-full bg-gradient-to-r from-blue-400 to-purple-500"
                  style={{ width: `${Math.min(100, Math.max(0, verificationStats.verification_rate))}%` }}
                />
              </div>
            </div>
          </>
        )}

        {/* Users Table */}
        {activeTab === 'users' && (
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
            <div className="p-6 border-b border-slate-700">
              <h2 className="text-2xl font-bold text-white flex items-center">
                <Users className="w-6 h-6 mr-2" />
                All Users
              </h2>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-900/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Username</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Email</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Full Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Charts</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Lessons</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-slate-700/30 transition">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{user.id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                        {user.username}
                        {user.is_admin && <span className="ml-2 text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">ADMIN</span>}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">{user.email}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">{user.full_name || '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">{user.total_charts}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                        {user.completed_lessons}/{user.total_learning_progress}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {user.is_active ? (
                          <span className="text-green-400">Active</span>
                        ) : (
                          <span className="text-red-400">Inactive</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => viewUserDetails(user.id)}
                          className="text-blue-400 hover:text-blue-300 transition flex items-center space-x-1"
                        >
                          <Eye className="w-4 h-4" />
                          <span>View</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Practitioner Verification Queue */}
        {activeTab === 'verification' && (
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
            <div className="p-6 border-b border-slate-700">
              <h2 className="text-2xl font-bold text-white flex items-center">
                <UserCheck className="w-6 h-6 mr-2" />
                Practitioner Verification Queue
                {pendingPractitioners.length > 0 && (
                  <span className="ml-3 bg-red-500 text-white text-sm px-3 py-1 rounded-full">
                    {pendingPractitioners.length} pending
                  </span>
                )}
              </h2>
            </div>

            {pendingPractitioners.length === 0 ? (
              <div className="p-8 text-center">
                <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">All caught up!</h3>
                <p className="text-slate-400">No practitioners pending verification at the moment.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-900/50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Practitioner</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Title</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Experience</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Specializations</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Ready</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Applied</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700">
                    {pendingPractitioners.map((practitioner) => (
                      <tr key={practitioner.guru_id} className="hover:bg-slate-700/30 transition">
                        <td className="px-6 py-4">
                          <div>
                            <div className="text-sm font-medium text-white">{practitioner.full_name || practitioner.username}</div>
                            <div className="text-sm text-slate-400">{practitioner.email}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">{practitioner.professional_title}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">{practitioner.experience_years} years</td>
                        <td className="px-6 py-4">
                          <div className="flex flex-wrap gap-1">
                            {practitioner.specializations.slice(0, 2).map((spec) => (
                              <span key={spec} className="text-xs bg-purple-500/20 text-purple-300 px-2 py-1 rounded">
                                {spec.replace('_', ' ')}
                              </span>
                            ))}
                            {practitioner.specializations.length > 2 && (
                              <span className="text-xs text-slate-400">+{practitioner.specializations.length - 2} more</span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {practitioner.is_ready_for_verification ? (
                            <span className="inline-flex items-center text-green-400">
                              <CheckCircle className="w-4 h-4 mr-1" />
                              Ready
                            </span>
                          ) : (
                            <span className="inline-flex items-center text-yellow-400">
                              <Clock className="w-4 h-4 mr-1" />
                              Incomplete
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
                          {new Date(practitioner.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() => setSelectedPractitioner(practitioner)}
                            className="text-blue-400 hover:text-blue-300 transition flex items-center space-x-1"
                          >
                            <Eye className="w-4 h-4" />
                            <span>Review</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Practitioner Verification Modal */}
        {selectedPractitioner && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-slate-700 flex items-center justify-between">
                <h3 className="text-2xl font-bold text-white flex items-center">
                  <UserCheck className="w-6 h-6 mr-2" />
                  Practitioner Verification
                </h3>
                <button
                  onClick={() => setSelectedPractitioner(null)}
                  className="text-slate-400 hover:text-white transition"
                >
                  ✕
                </button>
              </div>

              <div className="p-6 space-y-6">
                {/* Basic Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="text-lg font-semibold text-white">Basic Information</h4>
                    <div className="space-y-2">
                      <div>
                        <p className="text-slate-400 text-sm">Full Name</p>
                        <p className="text-white font-medium">{selectedPractitioner.full_name || selectedPractitioner.username}</p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-sm">Email</p>
                        <p className="text-white font-medium">{selectedPractitioner.email}</p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-sm">Professional Title</p>
                        <p className="text-white font-medium">{selectedPractitioner.professional_title}</p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-sm">Experience</p>
                        <p className="text-white font-medium">{selectedPractitioner.experience_years} years</p>
                      </div>
                      {selectedPractitioner.price_per_hour && (
                        <div>
                          <p className="text-slate-400 text-sm">Price per Hour</p>
                          <p className="text-white font-medium">₹{selectedPractitioner.price_per_hour}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="text-lg font-semibold text-white">Verification Status</h4>
                    <div className="space-y-2">
                      <div>
                        <p className="text-slate-400 text-sm">Current Status</p>
                        <p className="text-yellow-400 font-medium">{selectedPractitioner.verification_status}</p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-sm">Ready for Verification</p>
                        {selectedPractitioner.is_ready_for_verification ? (
                          <span className="inline-flex items-center text-green-400">
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Yes
                          </span>
                        ) : (
                          <span className="inline-flex items-center text-red-400">
                            <XCircle className="w-4 h-4 mr-1" />
                            No - Profile incomplete
                          </span>
                        )}
                      </div>
                      <div>
                        <p className="text-slate-400 text-sm">Applied On</p>
                        <p className="text-white font-medium">{new Date(selectedPractitioner.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Bio */}
                <div>
                  <h4 className="text-lg font-semibold text-white mb-2">Professional Bio</h4>
                  <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
                    <p className="text-slate-300 whitespace-pre-wrap">{selectedPractitioner.bio}</p>
                  </div>
                </div>

                {/* Specializations */}
                <div>
                  <h4 className="text-lg font-semibold text-white mb-2">Specializations</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedPractitioner.specializations.map((spec) => (
                      <span key={spec} className="bg-purple-500/20 text-purple-300 px-3 py-1 rounded-full text-sm">
                        {spec.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Languages */}
                {selectedPractitioner.languages && selectedPractitioner.languages.length > 0 && (
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-2">Languages</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedPractitioner.languages.map((lang) => (
                        <span key={lang} className="bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full text-sm">
                          {lang.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Certification */}
                <div>
                  <h4 className="text-lg font-semibold text-white mb-2">Certification Details</h4>
                  <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4 space-y-2">
                    <div>
                      <p className="text-slate-400 text-sm">Certification Type</p>
                      <p className="text-white font-medium">
                        {selectedPractitioner.certification_details.certification_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-sm">Issuing Authority</p>
                      <p className="text-white font-medium">{selectedPractitioner.certification_details.issuing_authority}</p>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                {selectedPractitioner.is_ready_for_verification && (
                  <div className="flex justify-end space-x-4 pt-6 border-t border-slate-700">
                    <button
                      onClick={() => {
                        const reason = prompt('Please provide a reason for rejection:')
                        if (reason && reason.trim()) {
                          const notes = prompt('Additional notes (optional):')
                          handleRejectPractitioner(selectedPractitioner.guru_id, reason.trim(), notes?.trim())
                        }
                      }}
                      className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
                    >
                      <XCircle className="w-4 h-4" />
                      <span>Reject</span>
                    </button>
                    <button
                      onClick={() => {
                        const notes = prompt('Approval notes (optional):')
                        handleVerifyPractitioner(selectedPractitioner.guru_id, notes?.trim())
                      }}
                      className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
                    >
                      <CheckCircle className="w-4 h-4" />
                      <span>Approve</span>
                    </button>
                  </div>
                )}

                {!selectedPractitioner.is_ready_for_verification && (
                  <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-yellow-200 font-medium">Profile Incomplete</p>
                        <p className="text-yellow-300 text-sm mt-1">
                          This practitioner's profile is not complete. They need to provide all required information before verification can proceed.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* User Details Modal */}
        {selectedUser && userDetails && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-slate-700 flex items-center justify-between">
                <h3 className="text-2xl font-bold text-white flex items-center">
                  <UserCog className="w-6 h-6 mr-2" />
                  User Details
                </h3>
                <button
                  onClick={() => {
                    setSelectedUser(null)
                    setUserDetails(null)
                  }}
                  className="text-slate-400 hover:text-white transition"
                >
                  ✕
                </button>
              </div>

              <div className="p-6 space-y-4">
                {adminActionError && (
                  <div className="mb-2 rounded-md bg-red-500/10 border border-red-500/40 px-3 py-2 text-sm text-red-200">
                    {adminActionError}
                  </div>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-slate-400 text-sm">ID</p>
                    <p className="text-white font-medium">{userDetails.id}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">Username</p>
                    <p className="text-white font-medium">{userDetails.username}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">Email</p>
                    <p className="text-white font-medium">{userDetails.email}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">Full Name</p>
                    <p className="text-white font-medium">{userDetails.full_name || '-'}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">Created At</p>
                    <p className="text-white font-medium">{new Date(userDetails.created_at).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">Last Login</p>
                    <p className="text-white font-medium">
                      {userDetails.last_login ? new Date(userDetails.last_login).toLocaleDateString() : 'Never'}
                    </p>
                  </div>
                </div>

                <div className="border-t border-slate-700 pt-4">
                  <h4 className="text-white font-bold mb-2">Password Hash</h4>
                  <p className="text-slate-300 text-xs font-mono bg-slate-900/50 p-3 rounded break-all">
                    {userDetails.password_hash}
                  </p>
                </div>

                <div className="border-t border-slate-700 pt-4">
                  <h4 className="text-white font-bold mb-2">Statistics</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-900/50 p-3 rounded">
                      <p className="text-slate-400 text-sm">Charts Created</p>
                      <p className="text-white text-2xl font-bold">{userDetails.total_charts}</p>
                    </div>
                    <div className="bg-slate-900/50 p-3 rounded">
                      <p className="text-slate-400 text-sm">Learning Progress</p>
                      <p className="text-white text-2xl font-bold">
                        {userDetails.completed_lessons}/{userDetails.total_learning_progress}
                      </p>
                    </div>
                    <div className="bg-slate-900/50 p-3 rounded">
                      <p className="text-slate-400 text-sm">Chat Messages</p>
                      <p className="text-white text-2xl font-bold">{userDetails.total_chat_messages}</p>
                    </div>
                    <div className="bg-slate-900/50 p-3 rounded">
                      <p className="text-slate-400 text-sm">Status</p>
                      <p className={`text-2xl font-bold ${userDetails.is_active ? 'text-green-400' : 'text-red-400'}`}>
                        {userDetails.is_active ? 'Active' : 'Inactive'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Admin controls */}
                <div className="border-t border-slate-700 pt-4 mt-4">
                  <h4 className="text-white font-bold mb-2">Admin Controls</h4>
                  <p className="text-slate-300 text-sm mb-2">
                    Current role:{' '}
                    <span className={userDetails.is_admin ? 'text-yellow-300 font-semibold' : 'text-slate-200'}>
                      {userDetails.is_admin ? 'Administrator' : 'Regular user'}
                    </span>
                  </p>
                  {userDetails.email === 'marcsnuffy@gmail.com' || userDetails.username === 'Yatin' ? (
                    <p className="text-xs text-slate-400">
                      This is the master administrator account and its admin status cannot be changed.
                    </p>
                  ) : (
                    <button
                      onClick={() => handleToggleAdmin(userDetails.id, !userDetails.is_admin)}
                      className={`mt-2 inline-flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors \
                        ${userDetails.is_admin
                          ? 'bg-red-600 hover:bg-red-700 text-white'
                          : 'bg-yellow-500 hover:bg-yellow-600 text-slate-900'}`}
                    >
                      {userDetails.is_admin ? 'Revoke Admin Access' : 'Make Admin'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function AdminPage() {
  return (
    <AuthGuard requiredRole="admin">
      <AdminContent />
    </AuthGuard>
  )
}
