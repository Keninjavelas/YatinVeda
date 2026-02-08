"use client";

import { useCallback, useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AuthGuard } from '@/components/auth-guard'
import { useAuth } from '@/lib/auth-context'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/lib/toast-context'
import { BookOpen, Play, Search, ShoppingCart, Star } from 'lucide-react'

interface EBook {
  id: number
  title: string
  author: string
  description: string
  category: string
  language: string
  content_type: string
  price: number
  cover_image_url?: string
  average_rating: number
  total_ratings: number
  is_free: boolean
}

interface UserLibraryEntry {
  id: number
  ebook: EBook
  reading_progress: number
  last_read_at?: string
}

interface CatalogResponse {
  items: EBook[]
}

interface MyLibraryResponse {
  items: UserLibraryEntry[]
}

function LibraryContent() {
  const { accessToken, csrfToken } = useAuth()
  const { addToast } = useToast()
  const [books, setBooks] = useState<EBook[]>([])
  const [myLibrary, setMyLibrary] = useState<UserLibraryEntry[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [loading, setLoading] = useState(false)

  const fetchCatalog = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (selectedCategory !== 'all') params.append('category', selectedCategory)
      if (searchQuery) params.append('search', searchQuery)
      const data = await apiClient.get<CatalogResponse>(`/api/v1/library/catalog?${params}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })
      setBooks(data.items || [])
    } catch (error) {
      addToast('Error fetching catalog', 'error')
      console.error('Error fetching catalog:', error)
    } finally {
      setLoading(false)
    }
  }, [selectedCategory, searchQuery, accessToken, addToast])

  const fetchMyLibrary = useCallback(async () => {
    try {
      const data = await apiClient.get<MyLibraryResponse>('/api/v1/library/my-library', {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })
      setMyLibrary(data.items || [])
    } catch (error) {
      addToast('Error fetching my library', 'error')
      console.error('Error fetching my library:', error)
    }
  }, [accessToken, addToast])

  useEffect(() => {
    fetchCatalog()
    fetchMyLibrary()
  }, [fetchCatalog, fetchMyLibrary])

  const purchaseBook = async (bookId: number) => {
    try {
      await apiClient.post('/api/v1/library/purchase', { ebook_id: bookId }, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'x-csrf-token': csrfToken || '',
        },
      })
      addToast('Book purchased successfully!', 'success')
      fetchMyLibrary()
    } catch (error) {
      addToast('Purchase failed', 'error')
      console.error('Error purchasing book:', error)
    }
  }

  const getContentIcon = (type: string) => {
    switch (type) {
      case 'audiobook':
        return <Play className="h-4 w-4" />
      default:
        return <BookOpen className="h-4 w-4" />
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-2">
            📚 Vedic Library
          </h1>
          <p className="text-gray-600">Explore ancient wisdom in modern formats</p>
        </div>

        <Tabs defaultValue="catalog" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-8">
            <TabsTrigger value="catalog">Catalog</TabsTrigger>
            <TabsTrigger value="my-library">My Library</TabsTrigger>
          </TabsList>

          <TabsContent value="catalog">
            <div className="mb-6 space-y-4">
              <div className="flex gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search books, authors, topics..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && fetchCatalog()}
                    className="pl-10"
                  />
                </div>
                <Button onClick={fetchCatalog}>Search</Button>
              </div>

              <div className="flex gap-2 flex-wrap">
                {['all', 'vedic_astrology', 'palmistry', 'vastu', 'numerology', 'gemstones', 'remedies'].map((cat) => (
                  <Button
                    key={cat}
                    variant={selectedCategory === cat ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedCategory(cat)}
                  >
                    {cat.replace('_', ' ').toUpperCase()}
                  </Button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {books.map((book) => (
                <Card key={book.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div className="flex items-center gap-2">
                        {getContentIcon(book.content_type)}
                        <Badge variant="secondary">{book.content_type}</Badge>
                      </div>
                      <Badge variant="outline">{book.language}</Badge>
                    </div>
                    <CardTitle className="text-lg">{book.title}</CardTitle>
                    <CardDescription>by {book.author}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 line-clamp-3 mb-4">{book.description}</p>
                    <div className="flex items-center gap-2 mb-2">
                      <div className="flex items-center">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            className={`h-4 w-4 ${i < Math.floor(book.average_rating) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
                          />
                        ))}
                      </div>
                      <span className="text-sm text-gray-600">({book.total_ratings})</span>
                    </div>
                    <Badge>{book.category}</Badge>
                  </CardContent>
                  <CardFooter className="flex justify-between items-center">
                    <div className="text-xl font-bold text-purple-600">{book.is_free ? 'FREE' : `₹${book.price}`}</div>
                    <Button onClick={() => purchaseBook(book.id)} size="sm">
                      <ShoppingCart className="h-4 w-4 mr-2" />
                      {book.is_free ? 'Add' : 'Buy'}
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>

            {loading && (
              <div className="text-center py-12">
                <p className="text-gray-600">Loading books...</p>
              </div>
            )}

            {!loading && books.length === 0 && (
              <div className="text-center py-12">
                <BookOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No books found</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="my-library">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {myLibrary.map((item) => (
                <Card key={item.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <Badge variant="secondary">{item.ebook.content_type}</Badge>
                      <Badge variant="outline">{item.ebook.language}</Badge>
                    </div>
                    <CardTitle className="text-lg">{item.ebook.title}</CardTitle>
                    <CardDescription>by {item.ebook.author}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="mb-4">
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-gray-600">Progress</span>
                        <span className="font-semibold">{item.reading_progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-purple-600 h-2 rounded-full transition-all" style={{ width: `${item.reading_progress}%` }} />
                      </div>
                    </div>
                    {item.last_read_at && <p className="text-xs text-gray-500">Last read: {new Date(item.last_read_at).toLocaleDateString()}</p>}
                  </CardContent>
                  <CardFooter>
                    <Button className="w-full" variant="default">
                      <BookOpen className="h-4 w-4 mr-2" />
                      Continue Reading
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>

            {myLibrary.length === 0 && (
              <div className="text-center py-12">
                <BookOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">Your library is empty</p>
                <Button onClick={() => document.querySelector<HTMLElement>('[value="catalog"]')?.click()}>
                  Browse Catalog
                </Button>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default function LibraryPage() {
  return (
    <AuthGuard requiredRole="user">
      <LibraryContent />
    </AuthGuard>
  )
}
