/**
 * MFA Verification Component
 * Used during login to verify two-factor authentication
 */

'use client';

import React, { useState } from 'react';
import { AlertCircle, Loader2, TabsContent, TabsList, Tabs } from 'lucide-react';

interface MFAVerifyProps {
  onSuccess: (trustDevice: boolean) => void;
  onCancel?: () => void;
  userEmail?: string;
}

const MFAVerify: React.FC<MFAVerifyProps> = ({ onSuccess, onCancel, userEmail }) => {
  const [verificationMethod, setVerificationMethod] = useState<'totp' | 'backup'>('totp');
  const [code, setCode] = useState('');
  const [trustDevice, setTrustDevice] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleVerify = async () => {
    if (!code.trim()) {
      setError('Please enter a code');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/v1/auth/verify-mfa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          code: code.replace(/\s/g, ''),
          trust_device: trustDevice
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Verification failed');
      }

      const data = await response.json();
      // Store tokens if returned
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
      }
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }

      onSuccess(trustDevice);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && code.length >= 6) {
      handleVerify();
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6">
          <h1 className="text-2xl font-bold">🔐 Two-Factor Authentication</h1>
          <p className="text-indigo-100 mt-1">Enter your verification code</p>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex gap-3">
              <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
              <div>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            </div>
          )}

          {userEmail && (
            <p className="text-sm text-gray-500 mb-6">
              Account: <span className="font-medium text-gray-700">{userEmail}</span>
            </p>
          )}

          {/* Verification Method Tabs */}
          <div className="space-y-6">
            <div className="border-b">
              <div className="flex gap-4 -mb-px">
                <button
                  onClick={() => {
                    setVerificationMethod('totp');
                    setCode('');
                    setError('');
                  }}
                  className={`px-4 py-2 font-medium text-sm border-b-2 transition ${
                    verificationMethod === 'totp'
                      ? 'border-indigo-600 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Authenticator App
                </button>
                <button
                  onClick={() => {
                    setVerificationMethod('backup');
                    setCode('');
                    setError('');
                  }}
                  className={`px-4 py-2 font-medium text-sm border-b-2 transition ${
                    verificationMethod === 'backup'
                      ? 'border-indigo-600 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Backup Code
                </button>
              </div>
            </div>

            {/* TOTP Input */}
            {verificationMethod === 'totp' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  6-digit code from your authenticator app
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="000000"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  onKeyPress={handleKeyPress}
                  className="w-full text-center text-3xl tracking-widest font-mono border-2 border-gray-300 rounded-lg p-4 focus:border-indigo-600 focus:outline-none"
                  autoComplete="one-time-code"
                />
                <p className="text-center text-gray-500 text-xs mt-2">
                  {code.length}/6 digits
                </p>
              </div>
            )}

            {/* Backup Code Input */}
            {verificationMethod === 'backup' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  10-character backup code
                </label>
                <input
                  type="text"
                  maxLength={10}
                  placeholder="XXXX-XXXX-XX"
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase().slice(0, 10))}
                  onKeyPress={handleKeyPress}
                  className="w-full text-center text-lg tracking-widest font-mono border-2 border-gray-300 rounded-lg p-4 focus:border-indigo-600 focus:outline-none"
                />
                <p className="text-center text-gray-500 text-xs mt-2">
                  Use a code from your saved backup codes
                </p>
              </div>
            )}

            {/* Trust Device Checkbox */}
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={trustDevice}
                onChange={(e) => setTrustDevice(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-indigo-600 cursor-pointer"
              />
              <span className="text-sm text-gray-600">
                Trust this device for 30 days
              </span>
            </label>

            {trustDevice && (
              <p className="text-xs text-gray-500 bg-blue-50 p-3 rounded">
                ℹ️ You won't need to enter a code on this device for the next 30 days.
              </p>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3 mt-8">
            {onCancel && (
              <button
                onClick={onCancel}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium"
              >
                Cancel
              </button>
            )}
            <button
              onClick={handleVerify}
              disabled={loading || code.length < (verificationMethod === 'totp' ? 6 : 10)}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium flex items-center justify-center gap-2"
            >
              {loading && <Loader2 size={16} className="animate-spin" />}
              Verify
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MFAVerify;
