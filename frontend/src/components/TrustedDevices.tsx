/**
 * Trusted Devices Component
 * Manage devices that have MFA trust enabled
 */

'use client';

import React, { useState, useEffect } from 'react';
import { AlertCircle, Loader2, Smartphone, Monitor, Trash2, RefreshCw } from 'lucide-react';

interface TrustedDevice {
  id: number;
  device_name: string;
  trusted_at: string;
  expires_at: string;
  last_used_at: string;
  ip_address?: string;
}

interface TrustedDevicesProps {
  onRefresh?: () => void;
}

const TrustedDevices: React.FC<TrustedDevicesProps> = ({ onRefresh }) => {
  const [devices, setDevices] = useState<TrustedDevice[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/mfa/devices', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch devices');
      }

      const data: TrustedDevice[] = await response.json();
      setDevices(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load devices');
    } finally {
      setLoading(false);
    }
  };

  const revokeDevice = async (deviceId: number) => {
    setDeleting(deviceId);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/mfa/devices/${deviceId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to revoke device');
      }

      setDevices(devices.filter(d => d.id !== deviceId));
      setSuccess('Device trust revoked successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke device');
    } finally {
      setDeleting(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getDaysRemaining = (expiresAt: string) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const daysLeft = Math.ceil((expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return daysLeft > 0 ? daysLeft : 0;
  };

  const getDeviceIcon = (deviceName: string) => {
    const name = deviceName.toLowerCase();
    if (name.includes('iphone') || name.includes('ipad') || name.includes('mobile')) {
      return <Smartphone size={20} className="text-blue-500" />;
    }
    return <Monitor size={20} className="text-slate-500" />;
  };

  return (
    <div className="w-full">
      <div className="bg-white rounded-lg shadow-md">
        {/* Header */}
        <div className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Trusted Devices</h2>
              <p className="text-sm text-gray-500 mt-1">
                Devices where you won't need to enter MFA for 30 days
              </p>
            </div>
            <button
              onClick={fetchDevices}
              disabled={loading}
              className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100 disabled:opacity-50"
              title="Refresh"
            >
              <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex gap-3">
            <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {/* Success Alert */}
        {success && (
          <div className="mx-6 mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-700 text-sm">✓ {success}</p>
          </div>
        )}

        {/* Content */}
        <div className="px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="animate-spin text-gray-400" size={24} />
              <span className="ml-2 text-gray-500">Loading devices...</span>
            </div>
          ) : devices.length === 0 ? (
            <div className="text-center py-8">
              <Monitor size={48} className="mx-auto text-gray-300 mb-3" />
              <p className="text-gray-500">No trusted devices yet</p>
              <p className="text-sm text-gray-400 mt-1">
                You'll see devices here after marking them as trusted during login
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {devices.map((device) => {
                const daysRemaining = getDaysRemaining(device.expires_at);
                const isActive = daysRemaining > 0;

                return (
                  <div
                    key={device.id}
                    className={`flex items-start justify-between p-4 rounded-lg border ${
                      isActive ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex gap-3 flex-1">
                      <div className="mt-1">{getDeviceIcon(device.device_name)}</div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">
                          {device.device_name}
                        </h3>
                        <div className="space-y-1 mt-1 text-sm text-gray-600">
                          <p>
                            <span className="text-gray-500">Trusted:</span> {formatDate(device.trusted_at)}
                          </p>
                          <p>
                            <span className="text-gray-500">Last used:</span> {formatDate(device.last_used_at)}
                          </p>
                          {device.ip_address && (
                            <p>
                              <span className="text-gray-500">IP:</span> {device.ip_address}
                            </p>
                          )}
                        </div>
                        {isActive && (
                          <div className="mt-2">
                            <span className="inline-block px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded">
                              ✓ Active ({daysRemaining} days remaining)
                            </span>
                          </div>
                        )}
                        {!isActive && (
                          <div className="mt-2">
                            <span className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded">
                              Expired
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Revoke Button */}
                    <button
                      onClick={() => revokeDevice(device.id)}
                      disabled={deleting === device.id}
                      className="ml-4 p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-50 transition"
                      title="Revoke trust for this device"
                    >
                      {deleting === device.id ? (
                        <Loader2 size={18} className="animate-spin" />
                      ) : (
                        <Trash2 size={18} />
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Info Box */}
        {devices.length > 0 && (
          <div className="px-6 py-4 bg-blue-50 border-t border-blue-200 rounded-b-lg">
            <p className="text-sm text-blue-800">
              <strong>💡 Tip:</strong> You can revoke trust for any device at any time. 
              After revocation, you'll need to enter MFA on that device again.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrustedDevices;
