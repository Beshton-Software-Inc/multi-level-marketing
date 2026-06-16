import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { CreditCard } from 'lucide-react'
import { affiliateApi } from '../lib/api'

export function Payouts() {
  const { data, isLoading } = useQuery({ queryKey: ['payouts'], queryFn: affiliateApi.getPayouts })
  const payouts = data?.payouts || []

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-500/20 text-yellow-400',
      approved: 'bg-green-500/20 text-green-400',
      rejected: 'bg-red-500/20 text-red-400',
    }
    return (
      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[status] || 'bg-slate-700 text-slate-400'}`}>
        {status}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Payouts</h1>
        <p className="text-slate-400 mt-1">Your payout request history</p>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-slate-500">Loading…</div>
        ) : payouts.length === 0 ? (
          <div className="p-12 text-center">
            <CreditCard size={40} className="text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">No payout requests yet.</p>
            <p className="text-slate-500 text-sm mt-1">
              Go to <span className="text-amber-400">Earnings</span> to request a payout.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-500 text-xs border-b border-slate-700 bg-slate-700/30">
                  <th className="text-left px-6 py-3">Date</th>
                  <th className="text-left px-6 py-3">Amount</th>
                  <th className="text-left px-6 py-3">Method</th>
                  <th className="text-left px-6 py-3">Details</th>
                  <th className="text-right px-6 py-3">Status</th>
                  <th className="text-right px-6 py-3">Processed</th>
                </tr>
              </thead>
              <tbody>
                {payouts.map((p) => (
                  <tr key={p.id} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                    <td className="px-6 py-3 text-slate-400">{new Date(p.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-3 text-amber-400 font-semibold">${parseFloat(p.amount).toFixed(2)}</td>
                    <td className="px-6 py-3 text-white">{p.payment_method}</td>
                    <td className="px-6 py-3 text-slate-400 max-w-xs truncate">{p.payment_details}</td>
                    <td className="px-6 py-3 text-right">{statusBadge(p.status)}</td>
                    <td className="px-6 py-3 text-right text-slate-500">
                      {p.processed_at ? new Date(p.processed_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
