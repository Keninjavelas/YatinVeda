import Link from 'next/link'
import Image from 'next/image'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative">
      {/* Community.gif as animated background */}
      <div className="fixed inset-0 z-0">
        <Image
          src="/Community.gif"
          alt="Background"
          fill
          className="object-cover opacity-30"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900/70 via-slate-800/75 to-slate-900/70"></div>
      </div>

      <div className="container mx-auto px-4 py-8 pt-20 md:pt-8 relative z-10">
        <h1 className="text-4xl font-bold text-white text-center mb-8">
          🌌 YatinVeda - Vedic Astrology Platform
        </h1>
        <p className="text-slate-300 text-center text-lg mb-8">
          Welcome to the Vedic Astrology Intelligence Platform
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Link
            href="/chart"
            className="group bg-slate-800/50 rounded-lg p-6 text-center border border-transparent hover:border-blue-500/40 hover:bg-slate-800/80 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">Chart Generation</h2>
            <p className="text-slate-400">Generate your Vedic birth chart</p>
            <span className="mt-4 inline-block text-sm font-medium text-blue-400 group-hover:text-blue-300">
              Generate chart →
            </span>
          </Link>
          
          <Link
            href="/interpretation"
            className="group bg-slate-800/50 rounded-lg p-6 text-center border border-transparent hover:border-blue-500/40 hover:bg-slate-800/80 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">AI Interpretation</h2>
            <p className="text-slate-400">Get AI-powered chart analysis</p>
            <span className="mt-4 inline-block text-sm font-medium text-blue-400 group-hover:text-blue-300">
              Explore insights →
            </span>
          </Link>
          
          <Link
            href="/dasha"
            className="group bg-slate-800/50 rounded-lg p-6 text-center border border-transparent hover:border-blue-500/40 hover:bg-slate-800/80 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">Dasha & Transits</h2>
            <p className="text-slate-400">Explore planetary periods and movements</p>
            <span className="mt-4 inline-block text-sm font-medium text-blue-400 group-hover:text-blue-300">
              View timeline →
            </span>
          </Link>
          
          <Link
            href="/compatibility"
            className="group bg-slate-800/50 rounded-lg p-6 text-center border border-transparent hover:border-blue-500/40 hover:bg-slate-800/80 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">Compatibility</h2>
            <p className="text-slate-400">Analyze relationship synastry</p>
            <span className="mt-4 inline-block text-sm font-medium text-blue-400 group-hover:text-blue-300">
              Check match →
            </span>
          </Link>
          
          <Link
            href="/learn"
            className="group bg-slate-800/50 rounded-lg p-6 text-center border border-transparent hover:border-blue-500/40 hover:bg-slate-800/80 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">Learn Astrology</h2>
            <p className="text-slate-400">Educational content and lessons</p>
            <span className="mt-4 inline-block text-sm font-medium text-blue-400 group-hover:text-blue-300">
              Start learning →
            </span>
          </Link>
          
          <Link
            href="/community"
            className="group bg-slate-800/50 rounded-lg p-6 text-center border border-transparent hover:border-blue-500/40 hover:bg-slate-800/80 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">Community Info</h2>
            <p className="text-slate-400">Meet the Karma &amp; Ketu Krew</p>
            <span className="mt-4 inline-block text-sm font-medium text-blue-400 group-hover:text-blue-300">
              Learn more →
            </span>
          </Link>
          
          <Link
            href="/community-feed"
            className="group bg-slate-800/50 rounded-lg p-6 text-center border border-transparent hover:border-purple-500/40 hover:bg-slate-800/80 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">Community Feed 🌟</h2>
            <p className="text-slate-400">Share, connect, and engage</p>
            <span className="mt-4 inline-block text-sm font-medium text-purple-400 group-hover:text-purple-300">
              Join the conversation →
            </span>
          </Link>
          
          <Link
            href="/chat"
            className="group bg-slate-800/50 rounded-lg p-6 text-center border border-transparent hover:border-blue-500/40 hover:bg-slate-800/80 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">AI Chat</h2>
            <p className="text-slate-400">Chat with Vedic astrology assistant</p>
            <span className="mt-4 inline-block text-sm font-medium text-blue-400 group-hover:text-blue-300">
              Start chat →
            </span>
          </Link>
          
          <Link
            href="/book-appointment-new"
            className="group bg-slate-800/50 rounded-lg p-6 text-center border border-transparent hover:border-green-500/40 hover:bg-slate-800/80 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">Book Appointment 📅</h2>
            <p className="text-slate-400">Consult with expert Vedic astrologers</p>
            <span className="mt-4 inline-block text-sm font-medium text-green-400 group-hover:text-green-300">
              Find your guru →
            </span>
          </Link>
          
          <Link
            href="/consultants"
            className="group bg-gradient-to-br from-orange-600/20 to-amber-600/20 border-orange-500/30 rounded-lg p-6 text-center border hover:border-orange-500/50 hover:from-orange-600/30 hover:to-amber-600/30 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">🔮 Verified Consultants</h2>
            <p className="text-slate-300">Browse expert consultants</p>
            <span className="mt-4 inline-block text-sm font-medium text-orange-400 group-hover:text-orange-300">
              Explore directory →
            </span>
          </Link>
          
          <Link
            href="/ask-experts"
            className="group bg-gradient-to-br from-indigo-600/20 to-purple-600/20 border-indigo-500/30 rounded-lg p-6 text-center border hover:border-indigo-500/50 hover:from-indigo-600/30 hover:to-purple-600/30 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">💬 Ask the Experts</h2>
            <p className="text-slate-300">Community Q&A with karma points</p>
            <span className="mt-4 inline-block text-sm font-medium text-indigo-400 group-hover:text-indigo-300">
              Ask a question →
            </span>
          </Link>
          
          <Link
            href="/library"
            className="group bg-gradient-to-br from-purple-600/20 to-blue-600/20 border-purple-500/30 rounded-lg p-6 text-center border hover:border-purple-500/50 hover:from-purple-600/30 hover:to-blue-600/30 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">📚 Vedic Library</h2>
            <p className="text-slate-300">E-books, audiobooks & PDFs</p>
            <span className="mt-4 inline-block text-sm font-medium text-purple-400 group-hover:text-purple-300">
              Browse catalog →
            </span>
          </Link>
          
          <Link
            href="/wallet"
            className="group bg-gradient-to-br from-green-600/20 to-emerald-600/20 border-green-500/30 rounded-lg p-6 text-center border hover:border-green-500/50 hover:from-green-600/30 hover:to-emerald-600/30 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">💰 My Wallet</h2>
            <p className="text-slate-300">Fast & secure payments</p>
            <span className="mt-4 inline-block text-sm font-medium text-green-400 group-hover:text-green-300">
              Manage wallet →
            </span>
          </Link>
          
          <Link
            href="/profile"
            className="group bg-slate-800/50 rounded-lg p-6 text-center border border-transparent hover:border-blue-500/40 hover:bg-slate-800/80 transition-all duration-200"
          >
            <h2 className="text-xl font-semibold text-white mb-2">Profile</h2>
            <p className="text-slate-400">Manage your account and charts</p>
            <span className="mt-4 inline-block text-sm font-medium text-blue-400 group-hover:text-blue-300">
              View profile →
            </span>
          </Link>
        </div>
      </div>
    </div>
  )
}
