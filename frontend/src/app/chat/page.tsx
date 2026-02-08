'use client'

import React, { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/lib/auth-context'
import { apiClient } from '@/lib/api-client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  BookOpen, 
  Star, 
  Heart,
  Home,
  Users,
  Calendar,
  Lightbulb
} from 'lucide-react'
import { toast } from 'sonner'

interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  suggestions?: string[]
  related_topics?: string[]
}

interface ChatTopic {
  name: string
  description: string
  questions: string[]
}

interface ChatTopics {
  [key: string]: ChatTopic
}

export default function ChatPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [topics, setTopics] = useState<ChatTopics>({})
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadInitialData()
    // Add welcome message
    setMessages([{
      id: '1',
      type: 'assistant',
      content: `🌟 Namaste! I'm Yatin, your Vedic astrology AI assistant. I'm here to help you understand the ancient wisdom of Jyotish and guide you on your spiritual journey.

I can help you with:
• Personal birth chart analysis
• Understanding planetary influences
• Compatibility and relationships
• Career and life guidance
• Spiritual practices and remedies
• Timing of important events

What would you like to explore today?`,
      timestamp: new Date(),
      suggestions: [
        "What does my Sun sign mean?",
        "Tell me about career in astrology",
        "What is Guna Milan?",
        "Explain Dasha periods"
      ]
    }])
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadInitialData = async () => {
    try {
      // Load suggestions
      const suggestionsResponse = await apiClient.get<{ suggestions: string[] }>('/api/v1/chat/suggestions')
      setSuggestions(suggestionsResponse.suggestions)

      // Load topics
      const topicsResponse = await apiClient.get<{ topics: ChatTopics }>('/api/v1/chat/topics')
      setTopics(topicsResponse.topics)
    } catch (error) {
      console.error('Error loading chat data:', error)
    }
  }

  const sendMessage = async (messageText?: string) => {
    const text = messageText || inputMessage.trim()
    if (!text) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: text,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await apiClient.post<{
        response: string
        suggestions?: string[]
        related_topics?: string[]
      }>('/api/v1/chat/message', {
        message: text,
        context: {}
      })

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.response,
        timestamp: new Date(),
        suggestions: response.suggestions,
        related_topics: response.related_topics
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      toast.error('Failed to send message. Please try again.')
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'I apologize, but I encountered an error. Please try asking your question again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const getTopicIcon = (topicKey: string) => {
    switch (topicKey) {
      case 'basics': return <BookOpen className="h-5 w-5" />
      case 'planets': return <Star className="h-5 w-5" />
      case 'houses': return <Home className="h-5 w-5" />
      case 'compatibility': return <Heart className="h-5 w-5" />
      case 'transits': return <Calendar className="h-5 w-5" />
      default: return <Sparkles className="h-5 w-5" />
    }
  }

  if (!user) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="text-center py-8">
            <Bot className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
            <h2 className="text-2xl font-bold mb-4">Meet Yatin, Your AI Astrology Guide</h2>
            <p className="text-muted-foreground mb-4">
              Get personalized insights and guidance from our advanced Vedic astrology AI assistant.
            </p>
            <Button onClick={() => window.location.href = '/login'}>
              Sign In to Start Chatting
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Lightbulb className="h-5 w-5 mr-2" />
                Quick Topics
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {Object.entries(topics).map(([key, topic]) => (
                <Button
                  key={key}
                  variant={selectedTopic === key ? "default" : "ghost"}
                  className="w-full justify-start"
                  onClick={() => setSelectedTopic(selectedTopic === key ? null : key)}
                >
                  {getTopicIcon(key)}
                  <span className="ml-2">{topic.name}</span>
                </Button>
              ))}
            </CardContent>
          </Card>

          {selectedTopic && topics[selectedTopic] && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">{topics[selectedTopic].name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-3">
                  {topics[selectedTopic].description}
                </p>
                <div className="space-y-2">
                  {topics[selectedTopic].questions.map((question, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      className="w-full text-left justify-start text-xs"
                      onClick={() => sendMessage(question)}
                    >
                      {question}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Main Chat */}
        <div className="lg:col-span-3">
          <Card className="h-[600px] flex flex-col">
            <CardHeader className="border-b">
              <CardTitle className="flex items-center">
                <Bot className="h-6 w-6 mr-2 text-purple-600" />
                Chat with Yatin
                <Badge variant="secondary" className="ml-2">AI Assistant</Badge>
              </CardTitle>
            </CardHeader>

            {/* Messages */}
            <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex max-w-[80%] ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`flex-shrink-0 ${message.type === 'user' ? 'ml-3' : 'mr-3'}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        message.type === 'user' 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-purple-500 text-white'
                      }`}>
                        {message.type === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                      </div>
                    </div>
                    
                    <div className={`rounded-lg p-3 ${
                      message.type === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}>
                      <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                      
                      {message.suggestions && message.suggestions.length > 0 && (
                        <div className="mt-3 space-y-2">
                          <div className="text-xs opacity-75">Suggested questions:</div>
                          {message.suggestions.map((suggestion, index) => (
                            <Button
                              key={index}
                              variant="outline"
                              size="sm"
                              className="mr-2 mb-2 text-xs"
                              onClick={() => sendMessage(suggestion)}
                            >
                              {suggestion}
                            </Button>
                          ))}
                        </div>
                      )}
                      
                      {message.related_topics && message.related_topics.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {message.related_topics.map((topic, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {topic}
                            </Badge>
                          ))}
                        </div>
                      )}
                      
                      <div className="text-xs opacity-50 mt-2">
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex mr-3">
                    <div className="w-8 h-8 rounded-full bg-purple-500 text-white flex items-center justify-center">
                      <Bot className="h-4 w-4" />
                    </div>
                  </div>
                  <div className="bg-gray-100 rounded-lg p-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </CardContent>

            {/* Input */}
            <div className="border-t p-4">
              <div className="flex space-x-2">
                <Textarea
                  placeholder="Ask me anything about Vedic astrology..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="min-h-[60px] resize-none"
                  disabled={isLoading}
                />
                <Button 
                  onClick={() => sendMessage()}
                  disabled={!inputMessage.trim() || isLoading}
                  size="lg"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              
              {/* Quick Suggestions */}
              {suggestions.length > 0 && messages.length <= 1 && (
                <div className="mt-3">
                  <div className="text-xs text-muted-foreground mb-2">Try asking:</div>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.slice(0, 4).map((suggestion, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        className="text-xs"
                        onClick={() => sendMessage(suggestion)}
                      >
                        {suggestion}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}