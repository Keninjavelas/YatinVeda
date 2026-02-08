'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { apiClient } from '@/lib/api-client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  FileText, 
  Download, 
  QrCode, 
  Calendar, 
  User, 
  Clock,
  CheckCircle,
  AlertCircle,
  Eye,
  Bell
} from 'lucide-react'
import { toast } from 'sonner'

interface Prescription {
  id: number
  booking_id: number
  title: string
  diagnosis?: string
  remedies: RemedyItem[]
  follow_up_date?: string
  notes?: string
  pdf_url?: string
  qr_code_url?: string
  verification_code: string
  is_active: boolean
  created_at: string
  guru?: {
    name: string
    specialization?: string
  }
  guru_name?: string
}

interface RemedyItem {
  category: string
  description: string
  duration?: string
  frequency?: string
  product_url?: string
}

interface Reminder {
  id: number
  prescription_id: number
  prescription_title: string
  reminder_type: string
  reminder_text: string
  scheduled_at: string
  status: string
}

export default function PrescriptionsPage() {
  const { user } = useAuth()
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([])
  const [reminders, setReminders] = useState<Reminder[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPrescription, setSelectedPrescription] = useState<Prescription | null>(null)
  const [activeTab, setActiveTab] = useState<'my-prescriptions' | 'reminders'>('my-prescriptions')

  useEffect(() => {
    if (user) {
      loadPrescriptions()
      loadReminders()
    }
  }, [user])

  const loadPrescriptions = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get<{
        prescriptions: Prescription[]
        total: number
      }>('/api/v1/prescriptions/user/my-prescriptions')
      setPrescriptions(response.prescriptions)
    } catch (error) {
      console.error('Error loading prescriptions:', error)
      toast.error('Failed to load prescriptions')
    } finally {
      setLoading(false)
    }
  }

  const loadReminders = async () => {
    try {
      const response = await apiClient.get<{
        reminders: Reminder[]
        total: number
      }>('/api/v1/prescriptions/reminders/upcoming')
      setReminders(response.reminders)
    } catch (error) {
      console.error('Error loading reminders:', error)
    }
  }

  const loadPrescriptionDetails = async (prescriptionId: number) => {
    try {
      const response = await apiClient.get<Prescription>(`/api/v1/prescriptions/${prescriptionId}`)
      setSelectedPrescription(response)
    } catch (error) {
      console.error('Error loading prescription details:', error)
      toast.error('Failed to load prescription details')
    }
  }

  const downloadPrescription = async (prescription: Prescription) => {
    if (!prescription.pdf_url) {
      toast.error('PDF not available for this prescription')
      return
    }

    try {
      await apiClient.download(prescription.pdf_url, `prescription_${prescription.id}.pdf`)
      toast.success('Prescription downloaded successfully')
    } catch (error) {
      console.error('Error downloading prescription:', error)
      toast.error('Failed to download prescription')
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'gemstones': return 'bg-purple-100 text-purple-800'
      case 'mantras': return 'bg-blue-100 text-blue-800'
      case 'rituals': return 'bg-orange-100 text-orange-800'
      case 'lifestyle': return 'bg-green-100 text-green-800'
      case 'dietary': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const PrescriptionCard = ({ prescription }: { prescription: Prescription }) => (
    <Card className="mb-4 hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg mb-2">{prescription.title}</CardTitle>
            <div className="flex items-center space-x-4 text-sm text-muted-foreground">
              <div className="flex items-center">
                <User className="h-4 w-4 mr-1" />
                {prescription.guru_name || prescription.guru?.name || 'Unknown Practitioner'}
              </div>
              <div className="flex items-center">
                <Calendar className="h-4 w-4 mr-1" />
                {formatDate(prescription.created_at)}
              </div>
            </div>
          </div>
          <Badge variant={prescription.is_active ? 'default' : 'secondary'}>
            {prescription.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {prescription.diagnosis && (
          <div className="mb-4">
            <h4 className="font-semibold text-sm mb-2">Diagnosis</h4>
            <p className="text-sm text-muted-foreground">{prescription.diagnosis}</p>
          </div>
        )}
        
        {prescription.follow_up_date && (
          <div className="mb-4 p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center">
              <Clock className="h-4 w-4 mr-2 text-blue-600" />
              <span className="text-sm font-medium">Follow-up scheduled for {formatDate(prescription.follow_up_date)}</span>
            </div>
          </div>
        )}
        
        <div className="flex items-center justify-between pt-3 border-t">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadPrescriptionDetails(prescription.id)}
            >
              <Eye className="h-4 w-4 mr-1" />
              View Details
            </Button>
            
            {prescription.pdf_url && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => downloadPrescription(prescription)}
              >
                <Download className="h-4 w-4 mr-1" />
                Download PDF
              </Button>
            )}
          </div>
          
          <div className="text-xs text-muted-foreground">
            ID: {prescription.verification_code.slice(0, 8)}...
          </div>
        </div>
      </CardContent>
    </Card>
  )

  const ReminderCard = ({ reminder }: { reminder: Reminder }) => (
    <Card className="mb-3">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <Badge variant="outline" className="text-xs">
                {reminder.reminder_type.replace('_', ' ')}
              </Badge>
              <span className="text-sm font-medium">{reminder.prescription_title}</span>
            </div>
            <p className="text-sm text-muted-foreground mb-2">{reminder.reminder_text}</p>
            <div className="flex items-center text-xs text-muted-foreground">
              <Clock className="h-3 w-3 mr-1" />
              {formatDateTime(reminder.scheduled_at)}
            </div>
          </div>
          <div className="flex items-center">
            {reminder.status === 'pending' ? (
              <AlertCircle className="h-5 w-5 text-orange-500" />
            ) : (
              <CheckCircle className="h-5 w-5 text-green-500" />
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )

  if (!user) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="text-center py-8">
            <FileText className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
            <h2 className="text-2xl font-bold mb-4">Your Prescription Center</h2>
            <p className="text-muted-foreground mb-4">
              Access your personalized remedies and prescriptions from certified practitioners.
            </p>
            <Button onClick={() => window.location.href = '/login'}>
              Sign In to View Prescriptions
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">My Prescriptions</h1>
        <p className="text-muted-foreground">
          Manage your personalized remedies and follow-up schedules
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as typeof activeTab)}>
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="my-prescriptions">
            <FileText className="h-4 w-4 mr-2" />
            My Prescriptions ({prescriptions.length})
          </TabsTrigger>
          <TabsTrigger value="reminders">
            <Bell className="h-4 w-4 mr-2" />
            Reminders ({reminders.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="my-prescriptions">
          {loading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className="p-6">
                    <div className="space-y-3">
                      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                      <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : prescriptions.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No prescriptions yet</h3>
                <p className="text-muted-foreground mb-4">
                  Book a consultation with a certified practitioner to receive personalized remedies.
                </p>
                <Button onClick={() => window.location.href = '/gurus'}>
                  Find a Practitioner
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {prescriptions.map((prescription) => (
                <PrescriptionCard key={prescription.id} prescription={prescription} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="reminders">
          {reminders.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <Bell className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No upcoming reminders</h3>
                <p className="text-muted-foreground">
                  Your prescription reminders will appear here when scheduled.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {reminders.map((reminder) => (
                <ReminderCard key={reminder.id} reminder={reminder} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Prescription Details Modal */}
      {selectedPrescription && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-3xl max-h-[90vh] overflow-hidden">
            <CardHeader className="border-b">
              <div className="flex items-center justify-between">
                <CardTitle>{selectedPrescription.title}</CardTitle>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setSelectedPrescription(null)}
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="max-h-[70vh] overflow-y-auto p-6">
                <div className="space-y-6">
                  {/* Prescription Info */}
                  <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                    <div>
                      <span className="text-sm font-medium">Practitioner:</span>
                      <p className="text-sm">{selectedPrescription.guru?.name || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium">Specialization:</span>
                      <p className="text-sm">{selectedPrescription.guru?.specialization || 'Vedic Astrology'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium">Created:</span>
                      <p className="text-sm">{formatDate(selectedPrescription.created_at)}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium">Verification Code:</span>
                      <p className="text-sm font-mono">{selectedPrescription.verification_code}</p>
                    </div>
                  </div>

                  {/* Diagnosis */}
                  {selectedPrescription.diagnosis && (
                    <div>
                      <h3 className="font-semibold mb-2">Astrological Analysis</h3>
                      <p className="text-sm text-muted-foreground p-3 bg-blue-50 rounded-lg">
                        {selectedPrescription.diagnosis}
                      </p>
                    </div>
                  )}

                  {/* Remedies */}
                  <div>
                    <h3 className="font-semibold mb-3">Prescribed Remedies</h3>
                    <div className="space-y-3">
                      {selectedPrescription.remedies.map((remedy, index) => (
                        <Card key={index} className="p-4">
                          <div className="flex items-start justify-between mb-2">
                            <Badge className={getCategoryColor(remedy.category)}>
                              {remedy.category}
                            </Badge>
                            {remedy.product_url && (
                              <Button variant="outline" size="sm" asChild>
                                <a href={remedy.product_url} target="_blank" rel="noopener noreferrer">
                                  Get Product
                                </a>
                              </Button>
                            )}
                          </div>
                          <p className="text-sm mb-2">{remedy.description}</p>
                          <div className="flex space-x-4 text-xs text-muted-foreground">
                            {remedy.duration && (
                              <span><strong>Duration:</strong> {remedy.duration}</span>
                            )}
                            {remedy.frequency && (
                              <span><strong>Frequency:</strong> {remedy.frequency}</span>
                            )}
                          </div>
                        </Card>
                      ))}
                    </div>
                  </div>

                  {/* Notes */}
                  {selectedPrescription.notes && (
                    <div>
                      <h3 className="font-semibold mb-2">Additional Instructions</h3>
                      <p className="text-sm text-muted-foreground p-3 bg-yellow-50 rounded-lg">
                        {selectedPrescription.notes}
                      </p>
                    </div>
                  )}

                  {/* Follow-up */}
                  {selectedPrescription.follow_up_date && (
                    <div className="p-4 bg-green-50 rounded-lg">
                      <div className="flex items-center">
                        <Calendar className="h-5 w-5 mr-2 text-green-600" />
                        <div>
                          <span className="font-medium">Follow-up Consultation</span>
                          <p className="text-sm text-muted-foreground">
                            Scheduled for {formatDate(selectedPrescription.follow_up_date)}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="border-t p-4 flex justify-between">
                <div className="flex space-x-2">
                  {selectedPrescription.pdf_url && (
                    <Button onClick={() => downloadPrescription(selectedPrescription)}>
                      <Download className="h-4 w-4 mr-2" />
                      Download PDF
                    </Button>
                  )}
                  {selectedPrescription.qr_code_url && (
                    <Button variant="outline">
                      <QrCode className="h-4 w-4 mr-2" />
                      View QR Code
                    </Button>
                  )}
                </div>
                <Button variant="outline" onClick={() => setSelectedPrescription(null)}>
                  Close
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}