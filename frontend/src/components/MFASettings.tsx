/**
 * MFA Settings Component
 * Manage MFA status, regenerate backup codes, and view trusted devices
 */

'use client';

import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Loader2, Shield, Key, Download, Trash2 } from 'lucide-react';
import MFASetup from './MFASetup';
import TrustedDevices from './TrustedDevices';

interface MFAStatus {
  mfa_enabled: boolean;
  setup_date: string | null;
  backup_codes_count: number;
  trusted_devices_count: number;
}

interface BackupCode {
  code: string;
  used: boolean;
}

interface MFASettingsProps {
  onMFAStatusChange?: (enabled: boolean) => void;
}

const MFASettings: React.FC<MFASettingsProps> = ({ onMFAStatusChange }) => {
  const [mfaStatus, setMfaStatus] = useState<MFAStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [disabling, setDisabling] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showSetupWizard, setShowSetupWizard] = useState(false);
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [backupCodes, setBackupCodes] = useState<BackupCode[]>([]);

  useEffect(() => {
    fetchMFAStatus();
  }, []);

  const fetchMFAStatus = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/mfa/status', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch MFA status');
      }

      const data: MFAStatus = await response.json();
      setMfaStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load MFA status');
    } finally {
      setLoading(false);
    }
  };

  const handleSetupComplete = () => {
    setShowSetupWizard(false);
    fetchMFAStatus();
    onMFAStatusChange?.(true);
  };

  const disableMFA = async () => {
    if (!confirm('Are you sure you want to disable MFA? This will remove 2-factor authentication from your account.')) {
      return;
    }

    setDisabling(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/mfa/disable', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to disable MFA');
      }

      setMfaStatus(prev => prev ? { ...prev, mfa_enabled: false } : null);
      setSuccess('MFA has been disabled');
      onMFAStatusChange?.(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disable MFA');
    } finally {
      setDisabling(false);
    }
  };

  const regenerateBackupCodes = async () => {
    if (!confirm('Regenerating backup codes will invalidate all existing codes. Continue?')) {
      return;
    }

    setRegenerating(true);
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/mfa/backup-codes/regenerate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to regenerate backup codes');
      }

      const data = await response.json();
      setBackupCodes(data.backup_codes);
      setShowBackupCodes(true);
      fetchMFAStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate backup codes');
    } finally {
      setRegenerating(false);
    }
  };

  const downloadBackupCodes = () => {
    const codesText = backupCodes
      .map(bc => `${bc.code}${bc.used ? ' (used)' : ''}`)
      .join('\n');

    const element = document.createElement('a');
    element.setAttribute('href', `data:text/plain;charset=utf-8,${encodeURIComponent(codesText)}`);
    element.setAttribute('download', `backup-codes-${new Date().toISOString().split('T')[0]}.txt`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const copyAllCodes = () => {
    const codesText = backupCodes.map(bc => bc.code).join('\n');
    navigator.clipboard.writeText(codesText);
    alert('All codes copied to clipboard');
  };

  if (showSetupWizard && !mfaStatus?.mfa_enabled) {
    return <MFASetup onSetupComplete={handleSetupComplete} />;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-gray-400" size={24} />
        <span className="ml-2 text-gray-500">Loading MFA settings...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* MFA Status Card */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <Shield size={24} className={mfaStatus?.mfa_enabled ? 'text-green-600' : 'text-gray-400'} />
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-gray-900">Two-Factor Authentication</h2>
              <p className="text-sm text-gray-500 mt-1">
                Protect your account with an additional security layer
              </p>
            </div>
            <div className="text-right">
              {mfaStatus?.mfa_enabled ? (
                <div className="flex items-center gap-2 text-green-600">
                  <CheckCircle size={20} />
                  <span className="font-semibold">Enabled</span>
                </div>
              ) : (
                <span className="text-gray-500 font-semibold">Disabled</span>
              )}
            </div>
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

        {/* Status Info */}
        <div className="px-6 py-4 bg-gray-50 space-y-3">
          {mfaStatus?.mfa_enabled && (
            <>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Setup Date:</span>
                <span className="font-semibold text-gray-900">
                  {new Date(mfaStatus.setup_date!).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Active Backup Codes:</span>
                <span className="font-semibold text-gray-900">{mfaStatus.backup_codes_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Trusted Devices:</span>
                <span className="font-semibold text-gray-900">{mfaStatus.trusted_devices_count}</span>
              </div>
            </>
          )}
        </div>

        {/* Actions */}
        <div className="px-6 py-4 space-y-3">
          {!mfaStatus?.mfa_enabled ? (
            <button
              onClick={() => setShowSetupWizard(true)}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-lg transition flex items-center justify-center gap-2"
            >
              <Shield size={18} />
              Enable Two-Factor Authentication
            </button>
          ) : (
            <>
              <button
                onClick={regenerateBackupCodes}
                disabled={regenerating}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {regenerating ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Regenerating...
                  </>
                ) : (
                  <>
                    <Key size={18} />
                    Regenerate Backup Codes
                  </>
                )}
              </button>
              <button
                onClick={disableMFA}
                disabled={disabling}
                className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {disabling ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Disabling...
                  </>
                ) : (
                  <>
                    <Trash2 size={18} />
                    Disable Two-Factor Authentication
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Backup Codes Modal */}
      {showBackupCodes && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-bold text-gray-900">New Backup Codes</h3>
            </div>
            <div className="px-6 py-4">
              <p className="text-sm text-gray-600 mb-4">
                Save these codes in a safe place. You can use them to access your account if you lose access to your authenticator app.
              </p>
              <div className="bg-gray-50 p-3 rounded-lg max-h-64 overflow-y-auto">
                <div className="space-y-2 font-mono text-sm">
                  {backupCodes.map((bc, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center justify-between p-2 rounded ${
                        bc.used ? 'bg-gray-200 text-gray-500 line-through' : 'bg-white text-gray-900'
                      }`}
                    >
                      <span>{bc.code}</span>
                      {bc.used && <span className="text-xs ml-2">used</span>}
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-4 space-y-2">
                <button
                  onClick={copyAllCodes}
                  className="w-full bg-blue-100 hover:bg-blue-200 text-blue-700 font-semibold py-2 rounded-lg transition text-sm"
                >
                  Copy All Codes
                </button>
                <button
                  onClick={downloadBackupCodes}
                  className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-2 rounded-lg transition flex items-center justify-center gap-2 text-sm"
                >
                  <Download size={16} />
                  Download as File
                </button>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
              <button
                onClick={() => setShowBackupCodes(false)}
                className="w-full bg-gray-700 hover:bg-gray-800 text-white font-semibold py-2 rounded-lg transition"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Trusted Devices Section */}
      {mfaStatus?.mfa_enabled && (
        <TrustedDevices onRefresh={fetchMFAStatus} />
      )}

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>🔒 Security Tip:</strong> Enable MFA to protect your account from unauthorized access. 
          You'll need your authenticator app or a backup code to log in.
        </p>
      </div>
    </div>
  );
};

export default MFASettings;
