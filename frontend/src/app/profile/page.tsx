"use client"

import { AuthGuard } from '@/components/auth-guard'
import BackButton from '@/components/BackButton'
import { useAuth } from '@/lib/auth-context'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'
import { useState, useEffect } from 'react'
import { User, Mail, Calendar, BarChart3, MessageSquare, BookOpen, Save, X, Edit2, Shield, Trash2, Eye, EyeOff } from 'lucide-react'

interface ProfileStats {
  charts_saved: number
  chat_messages: number
  lessons_completed: number
  account_age_days: number
  member_since: string | null
}

function ProfileContent() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const [isEditing, setIsEditing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [statsLoading, setStatsLoading] = useState(true)
  const [stats, setStats] = useState<ProfileStats | null>(null)
  const [showPasswordChange, setShowPasswordChange] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  
  // Profile edit state
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [email, setEmail] = useState(user?.email || '')
  
  // Password change state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [changingPassword, setChangingPassword] = useState(false)
  
  // Delete account state
  const [deletePassword, setDeletePassword] = useState('')
  const [deleteConfirmText, setDeleteConfirmText] = useState('')
  const [deletingAccount, setDeletingAccount] = useState(false)

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '')
      setEmail(user.email || '')
      loadStats()
    }
  }, [user])

  const loadStats = async () => {
    try {
      setStatsLoading(true)
      const data = await apiClient.get<ProfileStats>('/api/v1/profile/stats')
      setStats(data)
    } catch (error) {
      console.error('Failed to load stats:', error)
      showToast('Failed to load profile statistics', 'error')
    } finally {
      setStatsLoading(false)
    }
  }

  const handleSaveProfile = async () => {
    if (!fullName.trim()) {
      showToast('Name cannot be empty', 'error')
      return
    }
    if (!email.trim() || !email.includes('@')) {
      showToast('Please enter a valid email', 'error')
      return
    }

    try {
      setLoading(true)
      await apiClient.put('/api/v1/auth/profile', {
        full_name: fullName,
        email: email
      })
      showToast('Profile updated successfully!', 'success')
      setIsEditing(false)
      // Refresh user data
      window.location.reload()
    } catch (error: unknown) {
      console.error('Failed to update profile:', error)
      showToast(error instanceof Error ? error.message : 'Failed to update profile', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleCancelEdit = () => {
    setFullName(user?.full_name || '')
    setEmail(user?.email || '')
    setIsEditing(false)
  }

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      showToast('Please fill in all password fields', 'error')
      return
    }
    if (newPassword.length < 8) {
      showToast('New password must be at least 8 characters', 'error')
      return
    }
    if (newPassword !== confirmPassword) {
      showToast('New passwords do not match', 'error')
      return
    }

    try {
      setChangingPassword(true)
      await apiClient.post('/api/v1/profile/password', {
        current_password: currentPassword,
        new_password: newPassword
      })
      showToast('Password changed successfully!', 'success')
      setShowPasswordChange(false)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (error: unknown) {
      console.error('Failed to change password:', error)
      showToast(error instanceof Error ? error.message : 'Failed to change password', 'error')
    } finally {
      setChangingPassword(false)
    }
  }

  const handleDeleteAccount = async () => {
    if (!deletePassword) {
      showToast('Please enter your password', 'error')
      return
    }
    if (deleteConfirmText !== 'DELETE') {
      showToast('Please type DELETE to confirm', 'error')
      return
    }

    try {
      setDeletingAccount(true)
      await apiClient.delete('/api/v1/profile/', {
        body: JSON.stringify({
          password: deletePassword,
          confirm: true
        })
      })
      showToast('Account deleted successfully', 'success')
      // Logout and redirect
      window.location.href = '/login'
    } catch (error: unknown) {
      console.error('Failed to delete account:', error)
      showToast(error instanceof Error ? error.message : 'Failed to delete account', 'error')
    } finally {
      setDeletingAccount(false)
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="mb-8">
          <BackButton />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Profile Card */}
          <div className="lg:col-span-2 space-y-6">
            {/* Profile Header */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-6">
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-3xl font-bold">
                    {user?.full_name?.[0]?.toUpperCase() || 'U'}
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold text-white">{user?.full_name || 'User'}</h1>
                    <p className="text-slate-400">@{user?.username}</p>
                    {user?.is_admin && (
                      <span className="inline-flex items-center gap-1 mt-2 px-2 py-1 bg-amber-500/20 text-amber-400 rounded-lg text-xs font-semibold">
                        <Shield className="w-3 h-3" />
                        Admin
                      </span>
                    )}
                  </div>
                </div>
                {!isEditing && (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 text-blue-400 rounded-xl hover:bg-blue-500/30 transition-all"
                  >
                    <Edit2 className="w-4 h-4" />
                    Edit Profile
                  </button>
                )}
              </div>

              {/* Profile Fields */}
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">Full Name</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                      placeholder="Enter your full name"
                    />
                  ) : (
                    <div className="flex items-center gap-2 text-white">
                      <User className="w-5 h-5 text-slate-500" />
                      <span className="text-lg">{user?.full_name || 'Not set'}</span>
                    </div>
                  )}
                </div>

                <div>
                  <label className="text-sm text-slate-400 mb-1 block">Email Address</label>
                  {isEditing ? (
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                      placeholder="Enter your email"
                    />
                  ) : (
                    <div className="flex items-center gap-2 text-white">
                      <Mail className="w-5 h-5 text-slate-500" />
                      <span className="text-lg">{user?.email || 'Not set'}</span>
                    </div>
                  )}
                </div>

                <div>
                  <label className="text-sm text-slate-400 mb-1 block">Username</label>
                  <div className="flex items-center gap-2 text-slate-400">
                    <User className="w-5 h-5 text-slate-500" />
                    <span className="text-lg">@{user?.username}</span>
                    <span className="text-xs text-slate-500">(cannot be changed)</span>
                  </div>
                </div>
              </div>

              {/* Edit Actions */}
              {isEditing && (
                <div className="flex gap-3 mt-6 pt-6 border-t border-slate-700">
                  <button
                    onClick={handleSaveProfile}
                    disabled={loading}
                    className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold py-3 rounded-xl hover:from-blue-600 hover:to-purple-600 transition-all disabled:opacity-50"
                  >
                    <Save className="w-5 h-5" />
                    {loading ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    disabled={loading}
                    className="flex-1 flex items-center justify-center gap-2 bg-slate-700 text-white font-semibold py-3 rounded-xl hover:bg-slate-600 transition-all disabled:opacity-50"
                  >
                    <X className="w-5 h-5" />
                    Cancel
                  </button>
                </div>
              )}
            </div>

            {/* Security Section */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-6">
              <h2 className="text-xl font-bold text-white mb-4">Security</h2>
              
              <button
                onClick={() => setShowPasswordChange(!showPasswordChange)}
                className="w-full flex items-center justify-between px-4 py-3 bg-slate-900/50 rounded-xl hover:bg-slate-900/70 transition-all text-white"
              >
                <span className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-blue-400" />
                  Change Password
                </span>
                <span className="text-slate-400">→</span>
              </button>

              {showPasswordChange && (
                <div className="mt-4 space-y-4 p-4 bg-slate-900/30 rounded-xl border border-slate-700">
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Current Password</label>
                    <div className="relative">
                      <input
                        type={showCurrentPassword ? "text" : "password"}
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 pr-12 text-white focus:border-blue-500 focus:outline-none"
                        placeholder="Enter current password"
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                      >
                        {showCurrentPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">New Password</label>
                    <div className="relative">
                      <input
                        type={showNewPassword ? "text" : "password"}
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 pr-12 text-white focus:border-blue-500 focus:outline-none"
                        placeholder="Enter new password (min 8 chars)"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                      >
                        {showNewPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Confirm New Password</label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                      placeholder="Confirm new password"
                    />
                  </div>

                  <button
                    onClick={handleChangePassword}
                    disabled={changingPassword}
                    className="w-full bg-blue-500 text-white font-semibold py-3 rounded-xl hover:bg-blue-600 transition-all disabled:opacity-50"
                  >
                    {changingPassword ? 'Changing...' : 'Change Password'}
                  </button>
                </div>
              )}
            </div>

            {/* Danger Zone */}
            <div className="bg-red-900/20 backdrop-blur-sm rounded-2xl border border-red-700/60 p-6">
              <h2 className="text-xl font-bold text-red-400 mb-4">Danger Zone</h2>
              
              <button
                onClick={() => setShowDeleteConfirm(!showDeleteConfirm)}
                className="w-full flex items-center justify-between px-4 py-3 bg-red-900/30 rounded-xl hover:bg-red-900/50 transition-all text-red-400"
              >
                <span className="flex items-center gap-2">
                  <Trash2 className="w-5 h-5" />
                  Delete Account
                </span>
                <span className="text-red-500">→</span>
              </button>

              {showDeleteConfirm && (
                <div className="mt-4 space-y-4 p-4 bg-red-900/20 rounded-xl border border-red-700">
                  <p className="text-red-400 text-sm">⚠️ This action is irreversible. All your data will be permanently deleted.</p>
                  
                  <div>
                    <label className="text-sm text-red-400 mb-1 block">Enter your password</label>
                    <input
                      type="password"
                      value={deletePassword}
                      onChange={(e) => setDeletePassword(e.target.value)}
                      className="w-full bg-slate-900/50 border border-red-700 rounded-xl px-4 py-3 text-white focus:border-red-500 focus:outline-none"
                      placeholder="Password"
                    />
                  </div>

                  <div>
                    <label className="text-sm text-red-400 mb-1 block">Type DELETE to confirm</label>
                    <input
                      type="text"
                      value={deleteConfirmText}
                      onChange={(e) => setDeleteConfirmText(e.target.value)}
                      className="w-full bg-slate-900/50 border border-red-700 rounded-xl px-4 py-3 text-white focus:border-red-500 focus:outline-none"
                      placeholder="DELETE"
                    />
                  </div>

                  <button
                    onClick={handleDeleteAccount}
                    disabled={deletingAccount || deleteConfirmText !== 'DELETE'}
                    className="w-full bg-red-600 text-white font-semibold py-3 rounded-xl hover:bg-red-700 transition-all disabled:opacity-50"
                  >
                    {deletingAccount ? 'Deleting...' : 'Permanently Delete Account'}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Account Info */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-6">
              <h3 className="text-lg font-bold text-white mb-4">Account Info</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-slate-300">
                  <Calendar className="w-4 h-4 text-slate-500" />
                  <div>
                    <p className="text-xs text-slate-500">Member since</p>
                    <p className="text-sm">{formatDate(stats?.member_since || null)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <Calendar className="w-4 h-4 text-slate-500" />
                  <div>
                    <p className="text-xs text-slate-500">Account age</p>
                    <p className="text-sm">{stats?.account_age_days || 0} days</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Statistics */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-6">
              <h3 className="text-lg font-bold text-white mb-4">Your Statistics</h3>
              {statsLoading ? (
                <div className="flex justify-center py-4">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-xl">
                    <div className="flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-blue-400" />
                      <span className="text-slate-300">Charts Saved</span>
                    </div>
                    <span className="text-white font-bold">{stats?.charts_saved || 0}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-xl">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="w-5 h-5 text-purple-400" />
                      <span className="text-slate-300">Chat Messages</span>
                    </div>
                    <span className="text-white font-bold">{stats?.chat_messages || 0}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-xl">
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-5 h-5 text-emerald-400" />
                      <span className="text-slate-300">Lessons Done</span>
                    </div>
                    <span className="text-white font-bold">{stats?.lessons_completed || 0}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ProfilePage() {
  return (
    <AuthGuard requiredRole="user">
      <ProfileContent />
    </AuthGuard>
  )
}
