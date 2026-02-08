'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'
import { 
  Menu, X, LogOut, Settings, LayoutDashboard, MessageSquare, Users, 
  Book, Calendar, Wallet, User, Shield
} from 'lucide-react'

export default function Navbar() {
  const router = useRouter()
  const { user, logout, isAuthenticated } = useAuth()
  const { addToast } = useToast()
  const [isOpen, setIsOpen] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)

  const handleLogout = async () => {
    try {
      await logout()
      addToast('Logged out successfully', 'success', 3000)
      router.push('/login')
    } catch (err) {
      addToast('Failed to logout', 'error', 3000)
    }
  }

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/chat', label: 'AI Assistant', icon: MessageSquare },
    { href: '/community', label: 'Community', icon: Users },
    { href: '/book-appointment', label: 'Book Session', icon: Calendar },
    { href: '/prescriptions', label: 'Prescriptions', icon: Book },
    { href: '/profile', label: 'Profile', icon: User },
  ]

  if (!isAuthenticated) return null

  return (
    <nav className="sticky top-0 z-40 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-b border-slate-700/50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/dashboard" className="flex items-center space-x-2 group">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-400 to-pink-500 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
              <span className="text-lg">✨</span>
            </div>
            <span className="font-bold text-white hidden sm:inline">YatinVeda</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-700/50 rounded-lg transition-all"
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden xl:inline">{item.label}</span>
                </Link>
              )
            })}
          </div>

          {/* User Menu */}
          <div className="flex items-center gap-4">
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-slate-700/50 transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-400 to-pink-500 flex items-center justify-center text-white text-sm font-bold">
                  {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
                </div>
                <span className="hidden sm:inline text-sm text-slate-300">{user?.full_name || 'User'}</span>
              </button>

              {/* Dropdown Menu */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-lg overflow-hidden z-50">
                  <div className="px-4 py-3 border-b border-slate-700">
                    <p className="text-sm font-semibold text-white">{user?.full_name || 'User'}</p>
                    <p className="text-xs text-slate-400">{user?.email}</p>
                  </div>

                  <Link
                    href="/profile"
                    className="flex items-center gap-3 px-4 py-3 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <User className="w-4 h-4" />
                    Profile Settings
                  </Link>

                  {user?.is_admin && (
                    <Link
                      href="/admin"
                      className="flex items-center gap-3 px-4 py-3 text-sm text-amber-400 hover:bg-slate-700 transition-colors"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <Shield className="w-4 h-4" />
                      Admin Panel
                    </Link>
                  )}

                  <button
                    onClick={() => {
                      setShowUserMenu(false)
                      handleLogout()
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-400 hover:bg-slate-700 transition-colors border-t border-slate-700"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign Out
                  </button>
                </div>
              )}
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="lg:hidden p-2 rounded-lg hover:bg-slate-700/50 transition-colors"
            >
              {isOpen ? (
                <X className="w-5 h-5 text-slate-300" />
              ) : (
                <Menu className="w-5 h-5 text-slate-300" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="lg:hidden border-t border-slate-700 py-4 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 px-4 py-3 text-sm text-slate-300 hover:text-white hover:bg-slate-700/50 rounded-lg transition-all"
                  onClick={() => setIsOpen(false)}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              )
            })}
          </div>
        )}
      </div>
    </nav>
  )
}
