"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Wallet, Plus, ArrowUpRight, ArrowDownRight, IndianRupee } from 'lucide-react';
import { AuthGuard } from '@/components/auth-guard';
import { useAuth } from '@/lib/auth-context';
import { apiClient } from '@/lib/api-client';
import { useToast } from '@/lib/toast-context';

type RazorpayOptions = {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description: string;
  order_id: string;
  handler: (response: unknown) => void;
  prefill: { name: string; email: string; contact: string };
  theme: { color: string };
};

interface WalletData {
  balance: number;
  currency: string;
}

interface Transaction {
  id: number;
  amount: number;
  transaction_type: string;
  description: string;
  created_at: string;
  balance_after: number;
}

interface TransactionsResponse {
  items: Transaction[]
}

interface LoadResponse {
  razorpay_key_id: string
  order: { amount: number; currency: string; id: string }
}

function WalletContent() {
  const { accessToken, csrfToken } = useAuth();
  const { addToast } = useToast();
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loadAmount, setLoadAmount] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchWalletBalance();
    fetchTransactions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  const fetchWalletBalance = async () => {
    try {
      const data = await apiClient.get<WalletData>('/api/v1/payments/wallet/balance', {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      setWallet(data);
    } catch (error) {
      addToast('Error fetching wallet balance', 'error');
      console.error('Error fetching wallet balance:', error);
    }
  };

  const fetchTransactions = async () => {
    try {
      const data = await apiClient.get<TransactionsResponse>('/api/v1/payments/wallet/transactions', {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      setTransactions(data.items || []);
    } catch (error) {
      addToast('Error fetching transactions', 'error');
      console.error('Error fetching transactions:', error);
    }
  };

  const loadWallet = async () => {
    if (!loadAmount || parseFloat(loadAmount) <= 0) {
      addToast('Please enter a valid amount', 'warning');
      return;
    }

    setLoading(true);
    try {
      const data = await apiClient.post<LoadResponse>('/api/v1/payments/wallet/load', { amount: parseFloat(loadAmount) }, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'x-csrf-token': csrfToken || ''
        }
      });

      if (data && data.razorpay_key_id && data.order) {
        // Open Razorpay checkout
        const options: RazorpayOptions = {
          key: data.razorpay_key_id,
          amount: data.order.amount,
          currency: data.order.currency,
          name: 'YatinVeda',
          description: 'Wallet Top-up',
          order_id: data.order.id,
          handler: async function (response: unknown) {
            // Verify payment
            await verifyPayment(response as Record<string, unknown>);
          },
          prefill: {
            name: '',
            email: '',
            contact: ''
          },
          theme: {
            color: '#9333ea'
          }
        };
        const rzp = new window.Razorpay(options);
        rzp.open();
      } else {
        addToast('Failed to initiate payment', 'error');
      }
    } catch (error) {
      addToast('Failed to initiate payment', 'error');
      console.error('Error loading wallet:', error);
    } finally {
      setLoading(false);
    }
  };

  const verifyPayment = async (paymentData: Record<string, unknown>) => {
    try {
      await apiClient.post('/api/v1/payments/verify-payment', paymentData, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      addToast('Wallet loaded successfully!', 'success');
      setLoadAmount('');
      fetchWalletBalance();
      fetchTransactions();
    } catch (error) {
      addToast('Failed to verify payment', 'error');
      console.error('Error verifying payment:', error);
    }
  };

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'load':
      case 'refund':
      case 'bonus':
        return <ArrowDownRight className="h-5 w-5 text-green-600" />;
      case 'payment':
        return <ArrowUpRight className="h-5 w-5 text-red-600" />;
      default:
        return <IndianRupee className="h-5 w-5 text-gray-600" />;
    }
  };

  const formatAmount = (amount: number) => {
    return (amount / 100).toFixed(2);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent mb-2">
            💰 My Wallet
          </h1>
          <p className="text-gray-600">Manage your YatinVeda wallet</p>
        </div>

        {/* Wallet Balance Card */}
        <Card className="mb-8 bg-gradient-to-br from-purple-600 to-blue-600 text-white">
          <CardHeader>
            <CardDescription className="text-purple-100">Available Balance</CardDescription>
            <CardTitle className="text-5xl font-bold">
              ₹{wallet ? formatAmount(wallet.balance) : '0.00'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 mt-4">
              <div className="flex-1">
                <Input
                  type="number"
                  placeholder="Enter amount"
                  value={loadAmount}
                  onChange={(e) => setLoadAmount(e.target.value)}
                  className="bg-white/20 border-white/30 text-white placeholder:text-white/60"
                />
              </div>
              <Button
                onClick={loadWallet}
                disabled={loading}
                className="bg-white text-purple-600 hover:bg-gray-100"
              >
                <Plus className="h-4 w-4 mr-2" />
                {loading ? 'Processing...' : 'Add Money'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Transactions */}
        <Card>
          <CardHeader>
            <CardTitle>Transaction History</CardTitle>
            <CardDescription>Your recent wallet transactions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {transactions.map((txn) => (
                <div key={txn.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="p-2 bg-gray-100 rounded-full">
                      {getTransactionIcon(txn.transaction_type)}
                    </div>
                    <div>
                      <p className="font-semibold">{txn.description}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(txn.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-lg font-bold ${
                      ['load', 'refund', 'bonus'].includes(txn.transaction_type)
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}>
                      {['load', 'refund', 'bonus'].includes(txn.transaction_type) ? '+' : '-'}
                      ₹{formatAmount(Math.abs(txn.amount))}
                    </p>
                    <p className="text-sm text-gray-500">
                      Balance: ₹{formatAmount(txn.balance_after)}
                    </p>
                  </div>
                </div>
              ))}

              {transactions.length === 0 && (
                <div className="text-center py-12">
                  <Wallet className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No transactions yet</p>
                  <p className="text-sm text-gray-500 mt-2">
                    Start by adding money to your wallet
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Quick Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-gray-600">Instant Payments</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-gray-500">Pay for consultations instantly with wallet balance</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-gray-600">Secure</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-gray-500">Protected by Razorpay with 256-bit encryption</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-gray-600">Refunds</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-gray-500">Instant refunds credited back to your wallet</p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Add Razorpay Script */}
      {/* Razorpay checkout script is included globally in layout */}
    </div>
  );
}

export default function WalletPage() {
  return (
    <AuthGuard requiredRole="user">
      <WalletContent />
    </AuthGuard>
  )
}
