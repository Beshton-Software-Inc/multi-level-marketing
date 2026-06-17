import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { DollarSign, Clock, X } from 'lucide-react'
import { affiliateApi } from '../lib/api'
import { StatCard } from '../components/StatCard'

const TIER_COLORS: Record<number, string> = {
  1: 'bg-amber-500/20 text-amber-400',
  2: 'bg-blue-500/20 text-blue-400',
  3: 'bg-purple-500/20 text-purple-400',
  4: 'bg-green-500/20 text-green-400',
  5: 'bg-pink-500/20 text-pink-400',
  6: 'bg-cyan-500/20 text-cyan-400',
  7: 'bg-orange-500/20 text-orange-400',
}

const tierLabel = (tier: number) => {
  const color = TIER_COLORS[tier] || 'bg-slate-700 text-slate-400'
  return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${color}`}>Level {tier}</span>
}

const statusBadge = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'bg-yellow-500/20 text-yellow-400',
    paid: 'bg-green-500/20 text-green-400',
    approved: 'bg-green-500/20 text-green-400',
    rejected: 'bg-red-500/20 text-red-400',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[status] || 'bg-slate-700 text-slate-400'}`}>
      {status}
    </span>
  )
}

export function Earnings() {
  const [showPayoutModal, setShowPayoutModal] = useState(false)
  const [amount, setAmount] = useState('')
  const [method, setMethod] = useState('Bank Transfer')
  const [details, setDetails] = useState('')
  const [payoutError, setPayoutError] = useState('')

  const qc = useQueryClient()

  const { data: statsData } = useQuery({ queryKey: ['affiliate-stats'], queryFn: affiliateApi.getStats })
  const { data: earningsData, isLoading } = useQuery({ queryKey: ['earnings'], queryFn: affiliateApi.getEarnings })
  const { data: payoutsData } = useQuery({ queryKey: ['payouts'], queryFn: affiliateApi.getPayouts })

  const payoutMutation = useMutation({
    mutationFn: affiliateApi.requestPayout,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['payouts'] })
      qc.invalidateQueries({ queryKey: ['affiliate-stats'] })
      setShowPayoutModal(false)
      setAmount('')
      setDetails('')
      setPayoutError('')
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setPayoutError(msg || 'Request failed. Try again.')
    },
  })

  const handlePayoutSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setPayoutError('')
    payoutMutation.mutate({ amount: parseFloat(amount), payment_method: method, payment_details: details })
  }

  const earnings = earningsData?.earnings || []
  const payouts = payoutsData?.payouts || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Earnings</h1>
          <p className="text-slate-400 mt-1">Your commission history and payouts</p>
        </div>
        <button
          onClick={() => setShowPayoutModal(true)}
          className="bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-4 py-2 rounded-lg transition-colors text-sm"
        >
          Request Payout
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4">
        <StatCard
          icon={<DollarSign size={20} />}
          label="Total Earnings"
          value={`$${parseFloat(statsData?.total_earnings || '0').toFixed(2)}`}
          accent
        />
        <StatCard
          icon={<Clock size={20} />}
          label="Pending Earnings"
          value={`$${parseFloat(statsData?.pending_earnings || '0').toFixed(2)}`}
          subtitle="Awaiting payout"
        />
      </div>

      {/* Commission history */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700">
          <h2 className="font-semibold text-white">Commission History</h2>
        </div>
        {isLoading ? (
          <div className="p-8 text-center text-slate-500">Loading…</div>
        ) : earnings.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">No commissions yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-500 text-xs border-b border-slate-700">
                  <th className="text-left px-6 py-3">Date</th>
                  <th className="text-left px-6 py-3">From</th>
                  <th className="text-left px-6 py-3">Tier</th>
                  <th className="text-left px-6 py-3">Description</th>
                  <th className="text-right px-6 py-3">Amount</th>
                  <th className="text-right px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {earnings.map((e) => (
                  <tr key={e.id} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                    <td className="px-6 py-3 text-slate-400 whitespace-nowrap">
                      {new Date(e.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-3 text-white">{e.source_name || '—'}</td>
                    <td className="px-6 py-3">{tierLabel(e.tier)}</td>
                    <td className="px-6 py-3 text-slate-400 max-w-xs truncate">{e.description || '—'}</td>
                    <td className="px-6 py-3 text-right text-amber-400 font-semibold whitespace-nowrap">
                      ${parseFloat(e.amount).toFixed(2)}
                    </td>
                    <td className="px-6 py-3 text-right">{statusBadge(e.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Payout requests */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700">
          <h2 className="font-semibold text-white">Payout Requests</h2>
        </div>
        {payouts.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">No payout requests yet.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-500 text-xs border-b border-slate-700">
                <th className="text-left px-6 py-3">Date</th>
                <th className="text-left px-6 py-3">Amount</th>
                <th className="text-left px-6 py-3">Method</th>
                <th className="text-right px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {payouts.map((p) => (
                <tr key={p.id} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="px-6 py-3 text-slate-400">{new Date(p.created_at).toLocaleDateString()}</td>
                  <td className="px-6 py-3 text-white font-semibold">${parseFloat(p.amount).toFixed(2)}</td>
                  <td className="px-6 py-3 text-slate-400">{p.payment_method}</td>
                  <td className="px-6 py-3 text-right">{statusBadge(p.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Payout modal */}
      {showPayoutModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          <div className="absolute inset-0 bg-black/70" onClick={() => setShowPayoutModal(false)} />
          <div className="relative bg-slate-800 border border-slate-700 rounded-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-white">Request Payout</h2>
              <button onClick={() => setShowPayoutModal(false)} className="text-slate-500 hover:text-white">
                <X size={20} />
              </button>
            </div>

            {payoutError && (
              <div className="mb-4 bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
                {payoutError}
              </div>
            )}

            <form onSubmit={handlePayoutSubmit} className="space-y-4">
              <div className="bg-slate-700/50 rounded-lg px-4 py-3 text-sm flex items-center justify-between">
                <span className="text-slate-400">Available balance</span>
                <span className="text-amber-400 font-semibold">
                  ${parseFloat(statsData?.total_earnings || '0').toFixed(2)}
                </span>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1.5">Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="1"
                  max={parseFloat(statsData?.total_earnings || '0')}
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  required
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-amber-500"
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-1.5">Payment Method</label>
                <select
                  value={method}
                  onChange={(e) => setMethod(e.target.value)}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-amber-500"
                >
                  <option>Bank Transfer</option>
                  <option>PayPal</option>
                  <option>Crypto</option>
                  <option>Zelle</option>
                  <option>Venmo</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-1.5">Payment Details</label>
                <textarea
                  value={details}
                  onChange={(e) => setDetails(e.target.value)}
                  required
                  rows={3}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-amber-500 resize-none"
                  placeholder="Bank routing/account number, PayPal email, wallet address, etc."
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowPayoutModal(false)}
                  className="flex-1 border border-slate-600 hover:border-slate-500 text-slate-300 py-2.5 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={payoutMutation.isPending}
                  className="flex-1 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-900 font-semibold py-2.5 rounded-lg transition-colors"
                >
                  {payoutMutation.isPending ? 'Submitting…' : 'Submit Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
