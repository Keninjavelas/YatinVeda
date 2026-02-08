"use client";

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Star, Languages, Award, Calendar, IndianRupee } from 'lucide-react';
import { AuthGuard } from '@/components/auth-guard';
import { useAuth } from '@/lib/auth-context';
import { useToast } from '@/lib/toast-context';
import { apiClient } from '@/lib/api-client';

interface ConsultantProfile {
  id: number;
  guru_id: number;
  display_name: string;
  bio: string;
  astrology_systems: string[];
  languages: string[];
  experience_years: number;
  verification_tier: string;
  verification_status: string;
  consultation_price: number;
  availability_status: string;
  average_rating: number;
  completed_sessions: number;
}

function ConsultantsPage() {
  const { accessToken, csrfToken } = useAuth();
  const { showToast } = useToast();
  const [consultants, setConsultants] = useState<ConsultantProfile[]>([]);
  const [filters, setFilters] = useState({
    astrology_system: '',
    language: '',
    tier: '',
    min_price: '',
    max_price: ''
  });
  const [loading, setLoading] = useState(false);

  const fetchConsultants = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const data = await apiClient.get<{ items: ConsultantProfile[] }>(
        `/api/v1/consultant/directory?${params}`
      );
      setConsultants(data.items || []);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to load consultants';
      showToast(errorMsg, 'error');
      console.error('Error fetching consultants:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, showToast]);

  useEffect(() => {
    fetchConsultants();
  }, [fetchConsultants]);

  const getTierBadge = (tier: string) => {
    const colors = {
      basic: 'bg-gray-100 text-gray-800',
      professional: 'bg-blue-100 text-blue-800',
      expert: 'bg-purple-100 text-purple-800'
    };
    return colors[tier as keyof typeof colors] || colors.basic;
  };

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'expert':
        return '⭐⭐⭐';
      case 'professional':
        return '⭐⭐';
      default:
        return '⭐';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-amber-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-orange-600 to-amber-600 bg-clip-text text-transparent mb-2">
            🔮 Verified Consultants
          </h1>
          <p className="text-gray-600">Connect with expert Vedic astrology consultants</p>
        </div>

        {/* Filters */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Find Your Perfect Consultant</CardTitle>
            <CardDescription>Use filters to narrow down your search</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <select
                className="border rounded-md p-2"
                value={filters.astrology_system}
                onChange={(e) => setFilters({ ...filters, astrology_system: e.target.value })}
              >
                <option value="">All Systems</option>
                <option value="vedic">Vedic</option>
                <option value="western">Western</option>
                <option value="kp">KP System</option>
                <option value="nadi">Nadi</option>
              </select>

              <select
                className="border rounded-md p-2"
                value={filters.language}
                onChange={(e) => setFilters({ ...filters, language: e.target.value })}
              >
                <option value="">All Languages</option>
                <option value="english">English</option>
                <option value="hindi">Hindi</option>
                <option value="tamil">Tamil</option>
                <option value="bengali">Bengali</option>
                <option value="telugu">Telugu</option>
              </select>

              <select
                className="border rounded-md p-2"
                value={filters.tier}
                onChange={(e) => setFilters({ ...filters, tier: e.target.value })}
              >
                <option value="">All Tiers</option>
                <option value="basic">Basic</option>
                <option value="professional">Professional</option>
                <option value="expert">Expert</option>
              </select>

              <Input
                type="number"
                placeholder="Min Price"
                value={filters.min_price}
                onChange={(e) => setFilters({ ...filters, min_price: e.target.value })}
              />

              <Input
                type="number"
                placeholder="Max Price"
                value={filters.max_price}
                onChange={(e) => setFilters({ ...filters, max_price: e.target.value })}
              />
            </div>
            <Button onClick={fetchConsultants} className="mt-4 w-full">
              Apply Filters
            </Button>
          </CardContent>
        </Card>

        {/* Consultants Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {consultants.map((consultant) => (
            <Card key={consultant.id} className="hover:shadow-xl transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <CardTitle className="text-xl">{consultant.display_name}</CardTitle>
                    <div className="flex items-center gap-1 mt-1">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`h-4 w-4 ${
                            i < Math.floor(consultant.average_rating)
                              ? 'fill-yellow-400 text-yellow-400'
                              : 'text-gray-300'
                          }`}
                        />
                      ))}
                      <span className="text-sm text-gray-600 ml-1">
                        ({consultant.completed_sessions})
                      </span>
                    </div>
                  </div>
                  <Badge className={getTierBadge(consultant.verification_tier)}>
                    {getTierIcon(consultant.verification_tier)} {consultant.verification_tier.toUpperCase()}
                  </Badge>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <p className="text-sm text-gray-700 line-clamp-3">{consultant.bio}</p>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2 text-gray-600">
                    <Award className="h-4 w-4" />
                    <span>{consultant.experience_years} years experience</span>
                  </div>

                  <div className="flex items-center gap-2 text-gray-600">
                    <Languages className="h-4 w-4" />
                    <span>{consultant.languages.join(', ')}</span>
                  </div>

                  <div className="flex flex-wrap gap-1">
                    {consultant.astrology_systems.map((system, idx) => (
                      <Badge key={idx} variant="outline" className="text-xs">
                        {system}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="pt-4 border-t flex justify-between items-center">
                  <div>
                    <p className="text-xs text-gray-500">Consultation Fee</p>
                    <p className="text-2xl font-bold text-orange-600 flex items-center gap-1">
                      <IndianRupee className="h-5 w-5" />
                      {consultant.consultation_price}
                    </p>
                  </div>
                  <Badge
                    variant={consultant.availability_status === 'available' ? 'default' : 'secondary'}
                  >
                    {consultant.availability_status}
                  </Badge>
                </div>

                <Button className="w-full" size="lg">
                  <Calendar className="h-4 w-4 mr-2" />
                  Book Consultation
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {loading && (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading consultants...</p>
          </div>
        )}

        {!loading && consultants.length === 0 && (
          <div className="text-center py-12">
            <Award className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No consultants found</p>
            <p className="text-sm text-gray-500 mt-2">Try adjusting your filters</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ConsultantsPageWrapper() {
  return (
    <AuthGuard requiredRole="user">
      <ConsultantsPage />
    </AuthGuard>
  )
}
