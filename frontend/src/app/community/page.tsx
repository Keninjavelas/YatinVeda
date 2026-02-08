'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { apiClient } from '@/lib/api-client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Heart, MessageCircle, Share2, Users, Calendar, Plus, Send } from 'lucide-react'
import { toast } from 'sonner'

interface Post {
  id: number
  user_id: number
  username: string
  full_name?: string
  avatar_url?: string
  content: string
  post_type: string
  media_url?: string
  chart_id?: number
  tags?: string[]
  visibility: string
  likes_count: number
  comments_count: number
  shares_count: number
  is_pinned: boolean
  is_edited: boolean
  edited_at?: string
  created_at: string
  is_liked_by_user: boolean
  is_own_post: boolean
}

interface Comment {
  id: number
  post_id: number
  user_id: number
  username: string
  full_name?: string
  avatar_url?: string
  parent_comment_id?: number
  content: string
  likes_count: number
  is_edited: boolean
  edited_at?: string
  created_at: string
  is_liked_by_user: boolean
  replies_count: number
}

interface UserProfile {
  user_id: number
  username: string
  full_name?: string
  bio?: string
  avatar_url?: string
  cover_image_url?: string
  location?: string
  website?: string
  interests?: string[]
  expertise_areas?: string[]
  is_verified: boolean
  followers_count: number
  following_count: number
  posts_count: number
  is_following: boolean
  is_followed_by: boolean
  is_own_profile: boolean
}

export default function CommunityPage() {
  const { user } = useAuth()
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)
  const [newPostContent, setNewPostContent] = useState('')
  const [feedType, setFeedType] = useState<'public' | 'following'>('public')
  const [selectedPost, setSelectedPost] = useState<Post | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [newComment, setNewComment] = useState('')

  useEffect(() => {
    loadFeed()
  }, [feedType])

  const loadFeed = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get<Post[]>(`/api/v1/community/posts?feed_type=${feedType}&limit=20`)
      setPosts(response)
    } catch (error) {
      console.error('Error loading feed:', error)
      toast.error('Failed to load community feed')
    } finally {
      setLoading(false)
    }
  }

  const createPost = async () => {
    if (!newPostContent.trim()) return

    try {
      const response = await apiClient.post<Post>('/api/v1/community/posts', {
        content: newPostContent,
        post_type: 'text',
        visibility: 'public'
      })
      
      setPosts([response, ...posts])
      setNewPostContent('')
      toast.success('Post created successfully!')
    } catch (error) {
      console.error('Error creating post:', error)
      toast.error('Failed to create post')
    }
  }

  const toggleLike = async (postId: number) => {
    try {
      const post = posts.find(p => p.id === postId)
      if (!post) return

      if (post.is_liked_by_user) {
        await apiClient.delete(`/api/v1/community/posts/${postId}/like`)
      } else {
        await apiClient.post(`/api/v1/community/posts/${postId}/like`)
      }

      // Update local state
      setPosts(posts.map(p => 
        p.id === postId 
          ? { 
              ...p, 
              is_liked_by_user: !p.is_liked_by_user,
              likes_count: p.is_liked_by_user ? p.likes_count - 1 : p.likes_count + 1
            }
          : p
      ))
    } catch (error) {
      console.error('Error toggling like:', error)
      toast.error('Failed to update like')
    }
  }

  const loadComments = async (postId: number) => {
    try {
      const response = await apiClient.get<Comment[]>(`/api/v1/community/posts/${postId}/comments`)
      setComments(response)
    } catch (error) {
      console.error('Error loading comments:', error)
      toast.error('Failed to load comments')
    }
  }

  const addComment = async (postId: number) => {
    if (!newComment.trim()) return

    try {
      const response = await apiClient.post<Comment>(`/api/v1/community/posts/${postId}/comments`, {
        content: newComment
      })
      
      setComments([...comments, response])
      setNewComment('')
      
      // Update post comment count
      setPosts(posts.map(p => 
        p.id === postId 
          ? { ...p, comments_count: p.comments_count + 1 }
          : p
      ))
      
      toast.success('Comment added!')
    } catch (error) {
      console.error('Error adding comment:', error)
      toast.error('Failed to add comment')
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (diffInHours < 1) {
      return 'Just now'
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`
    } else if (diffInHours < 168) {
      return `${Math.floor(diffInHours / 24)}d ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  const PostCard = ({ post }: { post: Post }) => (
    <Card className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex items-start space-x-3">
          <Avatar>
            <AvatarImage src={post.avatar_url} />
            <AvatarFallback>
              {post.full_name?.charAt(0) || post.username.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h4 className="font-semibold">{post.full_name || post.username}</h4>
              <span className="text-sm text-muted-foreground">@{post.username}</span>
              {post.is_edited && (
                <Badge variant="secondary" className="text-xs">Edited</Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">{formatDate(post.created_at)}</p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="mb-4 whitespace-pre-wrap">{post.content}</p>
        
        {post.media_url && (
          <div className="mb-4">
            <img 
              src={post.media_url} 
              alt="Post media" 
              className="rounded-lg max-w-full h-auto"
            />
          </div>
        )}
        
        {post.tags && post.tags.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-2">
            {post.tags.map((tag, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                #{tag}
              </Badge>
            ))}
          </div>
        )}
        
        <div className="flex items-center justify-between pt-3 border-t">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toggleLike(post.id)}
              className={post.is_liked_by_user ? 'text-red-500' : ''}
            >
              <Heart className={`h-4 w-4 mr-1 ${post.is_liked_by_user ? 'fill-current' : ''}`} />
              {post.likes_count}
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSelectedPost(post)
                loadComments(post.id)
              }}
            >
              <MessageCircle className="h-4 w-4 mr-1" />
              {post.comments_count}
            </Button>
            
            <Button variant="ghost" size="sm">
              <Share2 className="h-4 w-4 mr-1" />
              {post.shares_count}
            </Button>
          </div>
          
          <Badge variant={post.visibility === 'public' ? 'default' : 'secondary'}>
            {post.visibility}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )

  if (!user) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="text-center py-8">
            <h2 className="text-2xl font-bold mb-4">Join the YatinVeda Community</h2>
            <p className="text-muted-foreground mb-4">
              Connect with fellow astrology enthusiasts, share insights, and learn together.
            </p>
            <Button onClick={() => window.location.href = '/login'}>
              Sign In to Continue
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Community</h1>
        <p className="text-muted-foreground">
          Connect with fellow astrology enthusiasts and share your journey
        </p>
      </div>

      <Tabs value={feedType} onValueChange={(value) => setFeedType(value as 'public' | 'following')}>
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="public">
            <Users className="h-4 w-4 mr-2" />
            Public Feed
          </TabsTrigger>
          <TabsTrigger value="following">
            <Heart className="h-4 w-4 mr-2" />
            Following
          </TabsTrigger>
        </TabsList>

        <TabsContent value={feedType}>
          {/* Create Post */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Plus className="h-5 w-5 mr-2" />
                Share Your Thoughts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Textarea
                  placeholder="What's on your mind? Share your astrological insights, experiences, or questions..."
                  value={newPostContent}
                  onChange={(e) => setNewPostContent(e.target.value)}
                  className="min-h-[100px]"
                />
                <div className="flex justify-between items-center">
                  <div className="text-sm text-muted-foreground">
                    {newPostContent.length}/5000 characters
                  </div>
                  <Button 
                    onClick={createPost}
                    disabled={!newPostContent.trim()}
                  >
                    <Send className="h-4 w-4 mr-2" />
                    Post
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Posts Feed */}
          {loading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className="p-6">
                    <div className="flex space-x-3">
                      <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : posts.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <Users className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No posts yet</h3>
                <p className="text-muted-foreground">
                  {feedType === 'following' 
                    ? "Follow some users to see their posts here"
                    : "Be the first to share something with the community!"
                  }
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {posts.map((post) => (
                <PostCard key={post.id} post={post} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Comments Modal */}
      {selectedPost && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <CardHeader className="border-b">
              <div className="flex items-center justify-between">
                <CardTitle>Comments</CardTitle>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setSelectedPost(null)}
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="max-h-[50vh] overflow-y-auto p-6">
                {comments.length === 0 ? (
                  <p className="text-center text-muted-foreground py-8">
                    No comments yet. Be the first to comment!
                  </p>
                ) : (
                  <div className="space-y-4">
                    {comments.map((comment) => (
                      <div key={comment.id} className="flex space-x-3">
                        <Avatar className="h-8 w-8">
                          <AvatarImage src={comment.avatar_url} />
                          <AvatarFallback>
                            {comment.full_name?.charAt(0) || comment.username.charAt(0).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="font-semibold text-sm">
                              {comment.full_name || comment.username}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {formatDate(comment.created_at)}
                            </span>
                          </div>
                          <p className="text-sm">{comment.content}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="border-t p-4">
                <div className="flex space-x-3">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback>
                      {user.full_name?.charAt(0) || user.username?.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 flex space-x-2">
                    <Textarea
                      placeholder="Write a comment..."
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      className="min-h-[60px] resize-none"
                    />
                    <Button 
                      onClick={() => addComment(selectedPost.id)}
                      disabled={!newComment.trim()}
                      size="sm"
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}