'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import Image from 'next/image'
import { 
  Heart, MessageCircle, Share2, Send, Users, Calendar, 
  TrendingUp, Sparkles, Image as ImageIcon, X
} from 'lucide-react'
import { AuthGuard } from '@/components/auth-guard'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'
import { apiClient } from '@/lib/api-client'
import BackButton from '@/components/BackButton'

interface Post {
  id: number
  user_id: number
  username: string
  full_name: string | null
  avatar_url: string | null
  content: string
  post_type: string
  media_url: string | null
  tags: string[] | null
  likes_count: number
  comments_count: number
  shares_count: number
  is_liked_by_user: boolean
  is_own_post: boolean
  created_at: string
}

interface Comment {
  id: number
  user_id: number
  username: string
  full_name: string | null
  avatar_url: string | null
  content: string
  likes_count: number
  is_liked_by_user: boolean
  created_at: string
  replies_count: number
}

// Removed legacy AccessSession

// Seed posts that appear for everyone, simulating public tweets about YatinVeda
const seedPosts: Post[] = [
  {
    id: -1,
    user_id: -101,
    username: 'astro_updates',
    full_name: 'YatinVeda Announcements',
    avatar_url: null,
    content:
      '🌌 We just opened up YatinVeda for early access! Book a 1:1 session with our vetted Gurus, pay securely via Razorpay, and track your Vedic learning progress in one place.',
    post_type: 'text',
    media_url: null,
    tags: ['YatinVeda', 'Launch', 'VedicAstrology'],
    likes_count: 128,
    comments_count: 14,
    shares_count: 32,
    is_liked_by_user: false,
    is_own_post: false,
    created_at: '2025-01-10T08:00:00Z',
  },
  {
    id: -2,
    user_id: -102,
    username: 'jyotish_journey',
    full_name: 'Ananya • Vedic Student',
    avatar_url: null,
    content:
      'Just booked my first astrology session on YatinVeda ✨ The quiz-based guru matching plus the upcoming sessions dashboard makes it feel like Netflix, but for Jyotish.',
    post_type: 'text',
    media_url: null,
    tags: ['GuruBooking', 'StudentLife'],
    likes_count: 89,
    comments_count: 9,
    shares_count: 18,
    is_liked_by_user: false,
    is_own_post: false,
    created_at: '2025-01-11T06:30:00Z',
  },
  {
    id: -3,
    user_id: -103,
    username: 'razorpay_dev',
    full_name: 'Dev • Payments Nerd',
    avatar_url: null,
    content:
      'Respect to the YatinVeda team for the smooth Razorpay integration. Booking → order creation → payment verification → dashboard update… all in one clean flow. 💳',
    post_type: 'text',
    media_url: null,
    tags: ['Razorpay', 'DX', 'YatinVeda'],
    likes_count: 56,
    comments_count: 4,
    shares_count: 11,
    is_liked_by_user: false,
    is_own_post: false,
    created_at: '2025-01-12T12:15:00Z',
  },
  {
    id: -4,
    user_id: -104,
    username: 'admin_yatin',
    full_name: 'Yatin • Admin',
    avatar_url: null,
    content:
      'Sneak peek: the new Admin Dashboard on YatinVeda shows live stats for users, completed lessons, chat engagement, and more. One click to promote community mentors to admin. 👑',
    post_type: 'text',
    media_url: null,
    tags: ['AdminDashboard', 'ProductUpdate'],
    likes_count: 73,
    comments_count: 7,
    shares_count: 19,
    is_liked_by_user: false,
    is_own_post: false,
    created_at: '2025-01-13T09:45:00Z',
  },
  {
    id: -5,
    user_id: -105,
    username: 'chart_crafter',
    full_name: 'Rohit • Chart Enthusiast',
    avatar_url: null,
    content:
      'The community feed on YatinVeda is 🔥 Seeing people share their charts, notes from gurus, and progress through lessons makes it feel like a focused Jyotish Twitter.',
    post_type: 'text',
    media_url: null,
    tags: ['Community', 'Charts', 'Learning'],
    likes_count: 64,
    comments_count: 6,
    shares_count: 13,
    is_liked_by_user: false,
    is_own_post: false,
    created_at: '2025-01-14T17:20:00Z',
  },
]

function CommunityFeedContent() {
  const { showToast } = useToast()
  const [posts, setPosts] = useState<Post[]>(seedPosts)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [page, setPage] = useState(0)
  const [newPostContent, setNewPostContent] = useState('')
  const [newPostImage, setNewPostImage] = useState<string | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [selectedPost, setSelectedPost] = useState<Post | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [newComment, setNewComment] = useState('')
  const [feedType, setFeedType] = useState<'public' | 'following'>('public')
  const [showNewPostModal, setShowNewPostModal] = useState(false)
  const [creatingPost, setCreatingPost] = useState(false)
  const [loadingComments, setLoadingComments] = useState(false)
  const observerTarget = useRef<HTMLDivElement>(null)

  const fetchPosts = useCallback(async (reset = false) => {
    const currentPage = reset ? 0 : page
    const currentPosts = reset ? [] : posts.filter(p => p.id > 0) // Remove seed posts temporarily
    
    try {
      if (reset) {
        setLoading(true)
      } else {
        setLoadingMore(true)
      }

      const skip = currentPage * 20
      const response = await apiClient.get<Post[]>(
        `/api/v1/community/posts?feed_type=${feedType}&skip=${skip}&limit=20`
      )

      if (response.length < 20) {
        setHasMore(false)
      }

      if (reset) {
        // On reset, prepend seed posts
        setPosts([...seedPosts, ...response])
        setPage(1)
      } else {
        // On load more, append to existing posts (which already have seed posts at the top)
        setPosts([...seedPosts, ...currentPosts, ...response])
        setPage(currentPage + 1)
      }
    } catch (error) {
      console.error('Error fetching posts:', error)
      showToast('Failed to load posts. Please try again.', 'error')
      if (reset) {
        setPosts(seedPosts)
      }
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [feedType, page, posts, showToast])

  useEffect(() => {
    fetchPosts(true)
  }, [feedType, fetchPosts]) // Re-fetch when feed type changes

  // Infinite scroll observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loadingMore && hasMore && !loading) {
          fetchPosts(false)
        }
      },
      { threshold: 0.1 }
    )

    const currentTarget = observerTarget.current
    if (currentTarget) {
      observer.observe(currentTarget)
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget)
      }
    }
  }, [loadingMore, hasMore, loading, fetchPosts])

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        const base64String = reader.result as string
        setNewPostImage(base64String)
        setImagePreview(base64String)
      }
      reader.readAsDataURL(file)
    }
  }

  const removeImage = () => {
    setNewPostImage(null)
    setImagePreview(null)
  }

  const { accessToken, csrfToken, user } = useAuth()
  const createPost = async () => {
    if (!newPostContent.trim()) {
      showToast('Please enter some content for your post', 'error')
      return
    }

    try {
      setCreatingPost(true)
      const response = await apiClient.post<Post>('/api/v1/community/posts', {
        content: newPostContent,
        post_type: newPostImage ? 'image' : 'text',
        media_url: newPostImage,
        visibility: 'public'
      })

      // Insert after seed posts
      const seedCount = seedPosts.length
      const newPosts = [...posts]
      newPosts.splice(seedCount, 0, response)
      setPosts(newPosts)
      
      setNewPostContent('')
      setNewPostImage(null)
      setImagePreview(null)
      setShowNewPostModal(false)
      showToast('Post created successfully!', 'success')
    } catch (error) {
      console.error('Error creating post:', error)
      showToast('Failed to create post. Please try again.', 'error')
    } finally {
      setCreatingPost(false)
    }
  }

  const likePost = async (postId: number) => {
    const post = posts.find(p => p.id === postId)
    // Skip likes for seed posts that don't exist in the backend database
    if (!post || post.id < 0) return

    const wasLiked = post.is_liked_by_user
    
    // Optimistic update
    setPosts(posts.map(p => 
      p.id === postId 
        ? { 
            ...p, 
            is_liked_by_user: !p.is_liked_by_user,
            likes_count: p.is_liked_by_user ? p.likes_count - 1 : p.likes_count + 1
          }
        : p
    ))
    
    try {
      if (wasLiked) {
        await apiClient.delete(`/api/v1/community/posts/${postId}/like`)
      } else {
        await apiClient.post(`/api/v1/community/posts/${postId}/like`, {})
      }
    } catch (error) {
      console.error('Error liking post:', error)
      // Revert optimistic update
      setPosts(posts.map(p => 
        p.id === postId 
          ? { 
              ...p, 
              is_liked_by_user: wasLiked,
              likes_count: wasLiked ? p.likes_count + 1 : p.likes_count - 1
            }
          : p
      ))
      showToast('Failed to update like. Please try again.', 'error')
    }
  }

  const loadComments = async (postId: number) => {
    // Seed posts are static and not backed by the API
    if (postId < 0) {
      setComments([])
      return
    }
    
    try {
      setLoadingComments(true)
      const response = await apiClient.get<Comment[]>(`/api/v1/community/posts/${postId}/comments`)
      setComments(response)
    } catch (error) {
      console.error('Error loading comments:', error)
      showToast('Failed to load comments. Please try again.', 'error')
      setComments([])
    } finally {
      setLoadingComments(false)
    }
  }

  const addComment = async (postId: number) => {
    if (!newComment.trim()) {
      showToast('Please enter a comment', 'error')
      return
    }
    // Seed posts are static and not backed by the API
    if (postId < 0) return

    try {
      const response = await apiClient.post<Comment>(
        `/api/v1/community/posts/${postId}/comments`,
        { content: newComment }
      )

      setComments([...comments, response])
      setNewComment('')
      
      // Update comment count
      setPosts(posts.map(p => 
        p.id === postId ? { ...p, comments_count: p.comments_count + 1 } : p
      ))
      showToast('Comment added successfully!', 'success')
    } catch (error) {
      console.error('Error adding comment:', error)
      showToast('Failed to add comment. Please try again.', 'error')
    }
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 60) return 'just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8 flex items-center justify-between">
          <BackButton />
          <a
            href="/community"
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-emerald-500/50 transition-all duration-300 hover:from-emerald-600 hover:to-teal-600 hover:shadow-emerald-500/70 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
          >
            <Sparkles className="h-4 w-4" />
            Community Info
            <span className="transition-transform duration-300 group-hover:translate-x-1">→</span>
          </a>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-3 space-y-4">
            {/* Profile Card */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-6">
              <div className="flex flex-col items-center text-center">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-2xl font-bold mb-4">
                  {user?.full_name?.[0]?.toUpperCase() || 'U'}
                </div>
                <h3 className="text-white font-bold text-lg">{user?.full_name || 'User'}</h3>
                <p className="text-slate-400 text-sm mt-1">@{user?.email?.split('@')[0]}</p>
              </div>
              
              <button
                onClick={() => setShowNewPostModal(true)}
                className="w-full mt-6 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold py-3 rounded-xl hover:from-blue-600 hover:to-purple-600 transition-all duration-300 shadow-lg shadow-blue-500/30"
              >
                Create Post
              </button>
            </div>

            {/* Navigation */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-4">
              <nav className="space-y-2">
                <button
                  onClick={() => setFeedType('public')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                    feedType === 'public' 
                      ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' 
                      : 'text-slate-300 hover:bg-slate-700/50'
                  }`}
                >
                  <TrendingUp className="w-5 h-5" />
                  <span className="font-medium">Public Feed</span>
                </button>
                <button
                  onClick={() => setFeedType('following')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                    feedType === 'following' 
                      ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' 
                      : 'text-slate-300 hover:bg-slate-700/50'
                  }`}
                >
                  <Users className="w-5 h-5" />
                  <span className="font-medium">Following</span>
                </button>
                <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-slate-300 hover:bg-slate-700/50 transition-all">
                  <Calendar className="w-5 h-5" />
                  <span className="font-medium">Events</span>
                </button>
              </nav>
            </div>
          </div>

          {/* Main Feed */}
          <div className="lg:col-span-6 space-y-6">
            {loading ? (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
              </div>
            ) : posts.length === 0 ? (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-12 text-center">
                <Sparkles className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">No posts yet</h3>
                <p className="text-slate-400">Be the first to share something with the community!</p>
              </div>
            ) : (
              posts.map(post => (
                <div key={post.id} className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-6 hover:border-slate-600/60 transition-all">
                  {/* Post Header */}
                  <div className="flex items-start gap-3 mb-4">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold overflow-hidden relative">
                      {post.avatar_url ? (
                        <Image src={post.avatar_url} alt={post.username} fill className="object-cover" />
                      ) : (
                        post.username[0].toUpperCase()
                      )}
                    </div>
                    <div className="flex-1">
                      <h4 className="text-white font-semibold">{post.full_name || post.username}</h4>
                      <p className="text-slate-400 text-sm">@{post.username} · {formatTimeAgo(post.created_at)}</p>
                    </div>
                  </div>

                  {/* Post Content */}
                  <div className="mb-4">
                    <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">{post.content}</p>
                    {post.media_url && (
                      <div className="mt-4 rounded-xl w-full overflow-hidden relative" style={{maxHeight: '384px', minHeight: '200px'}}>
                        <Image src={post.media_url} alt="Post media" fill className="object-cover" />
                      </div>
                    )}
                    {post.tags && post.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {post.tags.map(tag => (
                          <span key={tag} className="text-blue-400 text-sm">#{tag}</span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Post Actions */}
                  <div className="flex items-center gap-6 pt-4 border-t border-slate-700/50">
                    <button
                      onClick={() => likePost(post.id)}
                      className={`flex items-center gap-2 transition-colors ${
                        post.is_liked_by_user ? 'text-red-400' : 'text-slate-400 hover:text-red-400'
                      }`}
                    >
                      <Heart className={`w-5 h-5 ${post.is_liked_by_user ? 'fill-red-400' : ''}`} />
                      <span className="text-sm font-medium">{post.likes_count}</span>
                    </button>
                    <button
                      onClick={() => {
                        setSelectedPost(post)
                        loadComments(post.id)
                      }}
                      className="flex items-center gap-2 text-slate-400 hover:text-blue-400 transition-colors"
                    >
                      <MessageCircle className="w-5 h-5" />
                      <span className="text-sm font-medium">{post.comments_count}</span>
                    </button>
                    <button className="flex items-center gap-2 text-slate-400 hover:text-green-400 transition-colors">
                      <Share2 className="w-5 h-5" />
                      <span className="text-sm font-medium">{post.shares_count}</span>
                    </button>
                  </div>
                </div>
              ))
            )}

            {/* Infinite Scroll Observer Target */}
            {!loading && hasMore && (
              <div ref={observerTarget} className="py-8 flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            )}

            {!loading && !hasMore && posts.length > seedPosts.length && (
              <div className="py-8 text-center text-slate-400">
                You've reached the end of the feed
              </div>
            )}
          </div>

          {/* Right Sidebar */}
          <div className="lg:col-span-3 space-y-4">
            {/* Trending Topics */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-6">
              <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-400" />
                Trending Topics
              </h3>
              <div className="space-y-3">
                {[
                  { tag: '#VedicAstrology', count: 487 },
                  { tag: '#Nakshatra', count: 342 },
                  { tag: '#FullMoon', count: 256 },
                  { tag: '#JyotishTips', count: 421 },
                  { tag: '#CosmicWisdom', count: 189 }
                ].map(({ tag, count }) => (
                  <div key={tag} className="pb-3 border-b border-slate-700/50 last:border-0">
                    <p className="text-blue-400 font-medium">{tag}</p>
                    <p className="text-slate-500 text-sm mt-1">{count} posts</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Upcoming Events */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-6">
              <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-purple-400" />
                Upcoming Events
              </h3>
              <div className="space-y-3">
                <div className="p-3 bg-slate-700/30 rounded-xl">
                  <p className="text-white font-medium text-sm">New Moon Ritual</p>
                  <p className="text-slate-400 text-xs mt-1">Tonight at 8 PM</p>
                </div>
                <div className="p-3 bg-slate-700/30 rounded-xl">
                  <p className="text-white font-medium text-sm">Study Circle</p>
                  <p className="text-slate-400 text-xs mt-1">Tomorrow at 6 PM</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* New Post Modal */}
      {showNewPostModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-2xl border border-slate-700 max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-white">Create Post</h2>
              <button
                onClick={() => setShowNewPostModal(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <textarea
              value={newPostContent}
              onChange={(e) => setNewPostContent(e.target.value)}
              placeholder="Share your thoughts with the community..."
              className="w-full bg-slate-900/50 border border-slate-700 rounded-xl p-4 text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none resize-none"
              rows={6}
            />
            
            {/* Image Preview */}
            {imagePreview && (
              <div className="mt-4 relative rounded-xl overflow-hidden border border-slate-700" style={{maxHeight: '256px', minHeight: '100px'}}>
                <Image 
                  src={imagePreview} 
                  alt="Preview" 
                  fill
                  className="object-cover"
                />
                <button
                  onClick={removeImage}
                  className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white p-2 rounded-lg transition-colors z-10"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
            
            <div className="flex items-center justify-between mt-4">
              <div className="flex gap-2">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageSelect}
                  className="hidden"
                  id="image-upload"
                />
                <label
                  htmlFor="image-upload"
                  className="p-2 text-slate-400 hover:text-blue-400 hover:bg-slate-700/50 rounded-lg transition-colors cursor-pointer"
                >
                  <ImageIcon className="w-5 h-5" />
                </label>
              </div>
              <button
                onClick={createPost}
                disabled={!newPostContent.trim() || creatingPost}
                className="bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold px-6 py-2 rounded-xl hover:from-blue-600 hover:to-purple-600 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creatingPost ? 'Posting...' : 'Post'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Comments Modal */}
      {selectedPost && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-2xl border border-slate-700 max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-6 border-b border-slate-700">
              <h2 className="text-2xl font-bold text-white">Comments</h2>
              <button
                onClick={() => setSelectedPost(null)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {loadingComments ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
              ) : comments.length === 0 ? (
                <p className="text-slate-400 text-center py-8">No comments yet. Be the first!</p>
              ) : (
                comments.map(comment => (
                  <div key={comment.id} className="flex gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                      {comment.username[0].toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <div className="bg-slate-900/50 rounded-xl p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-white font-semibold text-sm">{comment.username}</span>
                          <span className="text-slate-500 text-xs">{formatTimeAgo(comment.created_at)}</span>
                        </div>
                        <p className="text-slate-200 text-sm">{comment.content}</p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="p-6 border-t border-slate-700">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Write a comment..."
                  className="flex-1 bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                  onKeyPress={(e) => e.key === 'Enter' && addComment(selectedPost.id)}
                />
                <button
                  onClick={() => addComment(selectedPost.id)}
                  disabled={!newComment.trim()}
                  className="bg-gradient-to-r from-blue-500 to-purple-500 text-white p-3 rounded-xl hover:from-blue-600 hover:to-purple-600 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function CommunityFeedPage() {
  return (
    <AuthGuard requiredRole="user">
      <CommunityFeedContent />
    </AuthGuard>
  )
}
