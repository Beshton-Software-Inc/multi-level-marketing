import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, DollarSign, CreditCard, TrendingUp, Check, X } from 'lucide-react'
import { adminApi, SimulateSubscriptionResult } from '../lib/api'
import { StatCard } from '../components/StatCard'

type Tab = 'affiliates' | 'payouts' | 'commission' | 'simulate'

export function Admin() {
  const [tab, setTab] = useState<Tab>('affiliates')
  const [commEmail, setCommEmail] = useState('')
  const [commAmount, setCommAmount] = useState('')
  const [commDesc, setCommDesc] = useState('')
  const [commMsg, setCommMsg] = useState('')
  const [simEmail, setSimEmail] = useState('')
  const [simAmount, setSimAmount] = useState('100')
  const [simMsg, setSimMsg] = useState('')
  const [simError, setSimError] = useState('')
  const [simResult, setSimResult] = useState<SimulateSubscriptionResult | null>(null)

  const qc = useQueryClient()

  const { data: stats } = useQuery({ queryKey: ['admin-stats'], queryFn: adminApi.getStats })
  const { data: affiliatesData } = useQuery({ queryKey: ['admin-affiliates'], queryFn: adminApi.getAffiliates })
  const { data: payoutsData, isLoading: payoutsLoading } = useQuery({
    queryKey: ['admin-payouts'],
    queryFn: adminApi.getPayouts,
  })

  const updatePayout = useMutation({
    mutationFn: ({ id, status, notes }: { id: number; status: string; notes?: string }) =>
      adminApi.updatePayout(id, { status, admin_notes: notes }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-payouts'] }),
  })

  const addComm = useMutation({
    mutationFn: adminApi.addCommission,
    onSuccess: () => {
      setCommMsg('Commission added successfully!')
      setCommEmail('')
      setCommAmount('')
      setCommDesc('')
      setTimeout(() => setCommMsg(''), 3000)
    },
  })

  const simulateSub = useMutation({
    mutationFn: adminApi.simulateSubscription,
    onSuccess: (data) => {
      setSimError('')
      setSimResult(data)
      setSimMsg(data.message)
    },
    onError: (err: unknown) => {
      setSimMsg('')
      setSimResult(null)
      const detail =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
          : null
      if (typeof detail === 'string') {
        setSimError(detail)
      } else if (Array.isArray(detail) && detail.length > 0) {
        setSimError(detail.map((d) => (typeof d === 'object' && d && 'msg' in d ? String(d.msg) : String(d))).join(', '))
      } else {
        setSimError('Simulation failed — check that the backend is running and you are logged in as admin.')
      }
    },
  })

  const handleAddComm = (e: React.FormEvent) => {
    e.preventDefault()
    addComm.mutate({ affiliate_email: commEmail, amount: parseFloat(commAmount), description: commDesc })
  }

  const handleSimulate = (e: React.FormEvent) => {
    e.preventDefault()
    setSimError('')
    setSimMsg('')
    setSimResult(null)
    simulateSub.mutate({
      affiliate_email: simEmail,
      subscription_amount: parseFloat(simAmount),
    })
  }

  const affiliates = affiliatesData?.affiliates || []
  const payouts = payoutsData?.payouts || []

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      active: 'bg-green-500/20 text-green-400',
      suspended: 'bg-red-500/20 text-red-400',
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
        <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
        <p className="text-slate-400 mt-1">Manage affiliates, payouts, and commissions</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Users size={20} />}
          label="Total Affiliates"
          value={stats?.total_affiliates ?? '…'}
        />
        <StatCard
          icon={<TrendingUp size={20} />}
          label="Active Affiliates"
          value={stats?.active_affiliates ?? '…'}
        />
        <StatCard
          icon={<DollarSign size={20} />}
          label="Total Commissions Paid"
          value={stats ? `$${parseFloat(stats.total_commissions).toFixed(2)}` : '…'}
          accent
        />
        <StatCard
          icon={<CreditCard size={20} />}
          label="Pending Payouts"
          value={stats ? `$${parseFloat(stats.pending_payouts_amount).toFixed(2)}` : '…'}
          subtitle={stats ? `${stats.pending_payouts_count} request(s)` : ''}
        />
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-700">
        <div className="flex gap-6">
          {(['affiliates', 'payouts', 'commission', 'simulate'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`pb-3 text-sm font-medium capitalize transition-colors border-b-2 ${
                tab === t
                  ? 'text-amber-400 border-amber-400'
                  : 'text-slate-400 border-transparent hover:text-white'
              }`}
            >
              {t === 'commission'
                ? 'Add Commission'
                : t === 'simulate'
                  ? 'Simulate Subscription'
                  : t}
            </button>
          ))}
        </div>
      </div>

      {/* Affiliates tab */}
      {tab === 'affiliates' && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-500 text-xs border-b border-slate-700 bg-slate-700/30">
                  <th className="text-left px-6 py-3">Name</th>
                  <th className="text-left px-6 py-3">Email</th>
                  <th className="text-left px-6 py-3">Ref Code</th>
                  <th className="text-right px-6 py-3">Earnings</th>
                  <th className="text-right px-6 py-3">Status</th>
                  <th className="text-right px-6 py-3">Joined</th>
                </tr>
              </thead>
              <tbody>
                {affiliates.map((a) => (
                  <tr key={a.id} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                    <td className="px-6 py-3 text-white font-medium">
                      {a.name}
                      {a.is_admin && (
                        <span className="ml-2 text-xs bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded">admin</span>
                      )}
                    </td>
                    <td className="px-6 py-3 text-slate-400">{a.email}</td>
                    <td className="px-6 py-3 font-mono text-xs text-amber-400">{a.referral_code}</td>
                    <td className="px-6 py-3 text-right text-white">${parseFloat(a.total_earnings).toFixed(2)}</td>
                    <td className="px-6 py-3 text-right">{statusBadge(a.status)}</td>
                    <td className="px-6 py-3 text-right text-slate-500">
                      {new Date(a.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {affiliates.length === 0 && (
              <div className="p-8 text-center text-slate-500 text-sm">No affiliates yet.</div>
            )}
          </div>
        </div>
      )}

      {/* Payouts tab */}
      {tab === 'payouts' && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          {payoutsLoading ? (
            <div className="p-8 text-center text-slate-500">Loading…</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-500 text-xs border-b border-slate-700 bg-slate-700/30">
                    <th className="text-left px-6 py-3">Affiliate</th>
                    <th className="text-left px-6 py-3">Amount</th>
                    <th className="text-left px-6 py-3">Method</th>
                    <th className="text-left px-6 py-3">Date</th>
                    <th className="text-right px-6 py-3">Status</th>
                    <th className="text-right px-6 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {payouts.map((p) => (
                    <tr key={p.id} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                      <td className="px-6 py-3">
                        <p className="text-white font-medium">{p.affiliate_name}</p>
                        <p className="text-xs text-slate-500">{p.affiliate_email}</p>
                      </td>
                      <td className="px-6 py-3 text-amber-400 font-semibold">${parseFloat(p.amount).toFixed(2)}</td>
                      <td className="px-6 py-3 text-slate-400">{p.payment_method}</td>
                      <td className="px-6 py-3 text-slate-400">{new Date(p.created_at).toLocaleDateString()}</td>
                      <td className="px-6 py-3 text-right">{statusBadge(p.status)}</td>
                      <td className="px-6 py-3 text-right">
                        {p.status === 'pending' && (
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => updatePayout.mutate({ id: p.id, status: 'approved' })}
                              disabled={updatePayout.isPending}
                              className="p-1.5 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg transition-colors"
                              title="Approve"
                            >
                              <Check size={14} />
                            </button>
                            <button
                              onClick={() => updatePayout.mutate({ id: p.id, status: 'rejected' })}
                              disabled={updatePayout.isPending}
                              className="p-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
                              title="Reject"
                            >
                              <X size={14} />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {payouts.length === 0 && (
                <div className="p-8 text-center text-slate-500 text-sm">No payout requests.</div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Add Commission tab */}
      {tab === 'commission' && (
        <div className="max-w-md">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-1">Add Manual Commission</h3>
            <p className="text-sm text-slate-400 mb-6">Add a commission directly to an affiliate's account.</p>

            {commMsg && (
              <div className="mb-4 bg-green-500/10 border border-green-500/30 rounded-lg px-4 py-3 text-green-400 text-sm">
                {commMsg}
              </div>
            )}

            <form onSubmit={handleAddComm} className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1.5">Affiliate Email</label>
                <input
                  type="email"
                  value={commEmail}
                  onChange={(e) => setCommEmail(e.target.value)}
                  required
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-amber-500"
                  placeholder="affiliate@example.com"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1.5">Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={commAmount}
                  onChange={(e) => setCommAmount(e.target.value)}
                  required
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-amber-500"
                  placeholder="0.00"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1.5">Description</label>
                <input
                  type="text"
                  value={commDesc}
                  onChange={(e) => setCommDesc(e.target.value)}
                  required
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-amber-500"
                  placeholder="Manual bonus, promotional commission, etc."
                />
              </div>
              <button
                type="submit"
                disabled={addComm.isPending}
                className="w-full bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-900 font-semibold py-2.5 rounded-lg transition-colors"
              >
                {addComm.isPending ? 'Adding…' : 'Add Commission'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Simulate Subscription tab */}
      {tab === 'simulate' && (
        <div className="max-w-md">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-1">Simulate Subscription</h3>
            <p className="text-sm text-slate-400 mb-6">
              Estimate L1 (20%), L2 (10%), and L3 (5%) commissions up the referral tree. Nothing is saved — use this to preview payouts before a real subscription.
            </p>

            {simMsg && (
              <div
                className={`mb-4 rounded-lg px-4 py-3 text-sm border ${
                  simResult && simResult.commissions.length === 0
                    ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300'
                    : 'bg-green-500/10 border-green-500/30 text-green-400'
                }`}
              >
                {simMsg}
              </div>
            )}
            {simError && (
              <div className="mb-4 bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
                {simError}
              </div>
            )}

            {simResult && simResult.commissions.length > 0 && (
              <div className="mb-6 bg-slate-900/50 border border-slate-600 rounded-lg overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-600 text-sm text-slate-300">
                  Estimated payouts for ${parseFloat(simResult.subscription_amount).toFixed(2)} subscription
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-500 text-xs border-b border-slate-700">
                      <th className="text-left px-4 py-2">Earner</th>
                      <th className="text-left px-4 py-2">Tier</th>
                      <th className="text-right px-4 py-2">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {simResult.commissions.map((c, i) => (
                      <tr key={`${c.earner_email}-${c.tier}-${i}`} className="border-b border-slate-700/50">
                        <td className="px-4 py-2">
                          <p className="text-white">{c.earner_name}</p>
                          <p className="text-xs text-slate-500">{c.earner_email}</p>
                        </td>
                        <td className="px-4 py-2 text-amber-400">L{c.tier}</td>
                        <td className="px-4 py-2 text-right text-white font-medium">
                          ${parseFloat(c.amount).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="px-4 py-3 text-xs text-slate-500">
                  These amounts are for planning only. Real earnings are created when a subscription completes via the winwinlaw checkout webhook.
                </p>
              </div>
            )}

            <form onSubmit={handleSimulate} className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1.5">Buyer affiliate email</label>
                <input
                  type="email"
                  value={simEmail}
                  onChange={(e) => setSimEmail(e.target.value)}
                  required
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-amber-500"
                  placeholder="carol@test.com"
                />
                <p className="text-xs text-slate-500 mt-1">
                  The affiliate who &quot;sold&quot; the subscription — upline earns commissions.
                </p>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1.5">Subscription amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={simAmount}
                  onChange={(e) => setSimAmount(e.target.value)}
                  required
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-amber-500"
                  placeholder="100"
                />
              </div>
              <button
                type="submit"
                disabled={simulateSub.isPending}
                className="w-full bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-900 font-semibold py-2.5 rounded-lg transition-colors"
              >
                {simulateSub.isPending ? 'Calculating…' : 'Calculate Estimate'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
