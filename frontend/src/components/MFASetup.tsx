/**
 * MFA Setup Component
 * Guides users through two-factor authentication setup
 */

'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import { AlertCircle, CheckCircle2, Copy, Eye, EyeOff, Loader2 } from 'lucide-react';

interface MFASetupProps {
  onComplete: (success: boolean) => void;
  onCancel?: () => void;
}

interface SetupData {
  qr_code: string;
  secret_key: string;
  backup_codes: string[];
}

const MFASetup: React.FC<MFASetupProps> = ({ onComplete, onCancel }) => {
  const [step, setStep] = useState<'intro' | 'setup' | 'verify' | 'backup'>('intro');
  const [loading, setLoading] = useState(false);
  const [setupData, setSetupData] = useState<SetupData | null>(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [showSecret, setShowSecret] = useState(false);
  const [backupCodesCopied, setBackupCodesCopied] = useState(false);
  const [secretCopied, setSecretCopied] = useState(false);

  // Fetch setup data from backend
  const initializeSetup = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/mfa/setup', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to initialize MFA setup');
      }

      const data: SetupData = await response.json();
      setSetupData(data);
      setStep('setup');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Setup failed');
    } finally {
      setLoading(false);
    }
  };

  // Verify TOTP code and enable MFA
  const handleVerify = async () => {
    if (verificationCode.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/mfa/enable', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code: verificationCode })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Verification failed');
      }

      setStep('backup');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  // Copy to clipboard helper
  const copyToClipboard = (text: string, setIndicator: (v: boolean) => void) => {
    navigator.clipboard.writeText(text);
    setIndicator(true);
    setTimeout(() => setIndicator(false), 2000);
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6">
          <h1 className="text-2xl font-bold">🔐 Set Up Two-Factor Authentication</h1>
          <p className="text-indigo-100 mt-2">Secure your account with an additional layer of protection</p>
        </div>

        {/* Progress Steps */}
        <div className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            {['Step 1: Start', 'Step 2: Scan', 'Step 3: Verify', 'Step 4: Save'].map((label, idx) => (
              <div
                key={idx}
                className={`flex items-center ${idx < 3 ? 'flex-1' : ''}`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                    (step === ['intro', 'setup', 'verify', 'backup'][idx])
                      ? 'bg-indigo-600 text-white'
                      : ['setup', 'verify', 'backup'].includes(step)
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-300 text-gray-600'
                  }`}
                >
                  {idx + 1}
                </div>
                <span className="ml-2 text-sm font-medium text-gray-600">{label}</span>
                {idx < 3 && (
                  <div className={`flex-1 h-1 mx-2 ${
                    ['setup', 'verify', 'backup'].includes(step) && idx < (['intro', 'setup', 'verify', 'backup'].indexOf(step))
                      ? 'bg-green-500'
                      : 'bg-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex gap-3">
              <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
              <div>
                <h3 className="font-semibold text-red-800">Error</h3>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            </div>
          )}

          {/* Step 1: Introduction */}
          {step === 'intro' && (
            <div>
              <h2 className="text-xl font-bold mb-4">Welcome to Secure Authentication</h2>
              <p className="text-gray-600 mb-4">
                Two-Factor Authentication (2FA) adds an extra layer of security to your account. Even if someone 
                knows your password, they won't be able to access your account without the code from your authenticator app.
              </p>
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h3 className="font-semibold text-blue-900 mb-2">What you'll need:</h3>
                <ul className="text-blue-800 space-y-1 text-sm">
                  <li>✓ Your smartphone</li>
                  <li>✓ An authenticator app (Google Authenticator, Authy, Microsoft Authenticator, etc.)</li>
                  <li>✓ Secure storage for backup codes</li>
                </ul>
              </div>

              <div className="flex gap-3">
                {onCancel && (
                  <button
                    onClick={onCancel}
                    className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                )}
                <button
                  onClick={initializeSetup}
                  disabled={loading}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {loading && <Loader2 size={16} className="animate-spin" />}
                  Get Started
                </button>
              </div>
            </div>
          )}

          {/* Step 2: Setup & QR Code */}
          {step === 'setup' && setupData && (
            <div>
              <h2 className="text-xl font-bold mb-4">Step 1: Scan QR Code</h2>
              
              <div className="bg-gradient-to-b from-gray-50 to-white rounded-lg p-6 mb-6">
                <p className="text-center text-gray-600 mb-4">
                  Open your authenticator app and scan this QR code
                </p>
                
                {/* QR Code Display */}
                <div className="flex justify-center bg-white p-4 rounded border border-gray-200">
                  <Image
                    src={`data:image/png;base64,${setupData.qr_code}`}
                    alt="MFA QR Code"
                    width={200}
                    height={200}
                    unoptimized
                    className="border-4 border-gray-200"
                  />
                </div>
              </div>

              {/* Manual Entry Option */}
              <div className="border-t pt-6">
                <p className="text-sm text-gray-600 mb-3">
                  Can't scan? Enter this code manually in your authenticator app:
                </p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 bg-gray-100 p-3 rounded font-mono text-sm break-all border border-gray-200">
                    {showSecret ? setupData.secret_key : '•'.repeat(setupData.secret_key.length)}
                  </code>
                  <button
                    onClick={() => setShowSecret(!showSecret)}
                    className="p-2 text-gray-500 hover:text-gray-700"
                  >
                    {showSecret ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                  <button
                    onClick={() => copyToClipboard(setupData.secret_key, setSecretCopied)}
                    className="p-2 text-gray-500 hover:text-gray-700"
                  >
                    <Copy size={18} />
                  </button>
                </div>
                {secretCopied && <p className="text-green-600 text-xs mt-1">✓ Copied!</p>}
              </div>

              <button
                onClick={() => setStep('verify')}
                className="mt-6 w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Next: Verify Code
              </button>
            </div>
          )}

          {/* Step 3: Verification */}
          {step === 'verify' && (
            <div>
              <h2 className="text-xl font-bold mb-4">Step 2: Verify Your Code</h2>
              <p className="text-gray-600 mb-6">
                Enter the 6-digit code from your authenticator app to verify the setup:
              </p>

              <div className="mb-6">
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="000000"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="w-full text-center text-3xl tracking-widest font-mono border-2 border-gray-300 rounded-lg p-4 focus:border-indigo-600 focus:outline-none"
                />
                <p className="text-center text-gray-500 text-sm mt-2">
                  {verificationCode.length}/6 digits
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep('setup')}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Back
                </button>
                <button
                  onClick={handleVerify}
                  disabled={loading || verificationCode.length !== 6}
                  className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading && <Loader2 size={16} className="animate-spin" />}
                  Verify
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Backup Codes */}
          {step === 'backup' && setupData && (
            <div>
              <h2 className="text-xl font-bold mb-2">Step 3: Save Backup Codes</h2>
              <p className="text-gray-600 mb-6">
                Save these backup codes in a safe place. You can use them to access your account if you lose access to your authenticator app.
              </p>

              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
                <p className="text-yellow-800 text-sm">
                  ⚠️ <strong>Important:</strong> Each code can only be used once. Store these in a secure location like a password manager.
                </p>
              </div>

              {/* Backup Codes Grid */}
              <div className="grid grid-cols-2 gap-3 mb-6">
                {setupData.backup_codes.map((code, idx) => (
                  <div
                    key={idx}
                    className="bg-gray-50 p-3 rounded border border-gray-200 font-mono text-sm"
                  >
                    {code}
                  </div>
                ))}
              </div>

              {/* Copy All Button */}
              <button
                onClick={() => {
                  const allCodes = setupData.backup_codes.join('\n');
                  copyToClipboard(allCodes, setBackupCodesCopied);
                }}
                className="w-full mb-6 px-4 py-2 border-2 border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 flex items-center justify-center gap-2"
              >
                <Copy size={16} />
                {backupCodesCopied ? 'Copied!' : 'Copy All Codes'}
              </button>

              {/* Confirmation Checkbox */}
              <div className="mb-6">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    id="codes-saved"
                    className="mt-1"
                  />
                  <span className="text-sm text-gray-600">
                    I have saved my backup codes in a safe place and understand they are required to access my account if I lose my authenticator app.
                  </span>
                </label>
              </div>

              <button
                onClick={() => {
                  const checkbox = document.getElementById('codes-saved') as HTMLInputElement;
                  if (checkbox?.checked) {
                    onComplete(true);
                  } else {
                    setError('Please confirm you have saved your backup codes');
                  }
                }}
                className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
              >
                <CheckCircle2 size={18} />
                Complete Setup
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MFASetup;
