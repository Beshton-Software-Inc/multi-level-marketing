import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { DollarSign, Users, TrendingUp, Calendar, Copy, Check, ExternalLink } from 'lucide-react'
import { affiliateApi } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { StatCard } from '../components/StatCard'

export function Dashboard() {
  const { user } = useAuth()
  const [copied, setCopied] = useState(false)

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['affiliate-stats'],
    queryFn: affiliateApi.getStats,
  })

  const { data: earningsData, isLoading: earningsLoading } = useQuery({
    queryKey: ['earnings'],
    queryFn: affiliateApi.getEarnings,
  })

  const referralUrl = `${window.location.origin}/register?ref=${user?.referral_code}`

  const copyReferralLink = async () => {
    await navigator.clipboard.writeText(referralUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const tierBadge = (tier: number) => {
    const colors: Record<number, string> = {
      1: 'bg-amber-500/20 text-amber-400',
      2: 'bg-blue-500/20 text-blue-400',
      3: 'bg-purple-500/20 text-purple-400',
    }
    return (
      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[tier] || colors[1]}`}>
        L{tier}
      </span>
    )
  }

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-500/20 text-yellow-400',
      paid: 'bg-green-500/20 text-green-400',
    }
    return (
      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[status] || 'bg-slate-700 text-slate-400'}`}>
        {status}
      </span>
    )
  }

  const recentEarnings = earningsData?.earnings?.slice(0, 5) || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Welcome back, {user?.name?.split(' ')[0]} 👋</h1>
        <p className="text-slate-400 mt-1">Here's your affiliate overview</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<DollarSign size={20} />}
          label="Total Earnings"
          value={statsLoading ? '…' : `$${parseFloat(stats?.total_earnings || '0').toFixed(2)}`}
          accent
        />
        <StatCard
          icon={<Users size={20} />}
          label="Direct Referrals"
          value={statsLoading ? '…' : stats?.direct_referrals ?? 0}
        />
        <StatCard
          icon={<TrendingUp size={20} />}
          label="Team Size"
          value={statsLoading ? '…' : stats?.team_size ?? 0}
          subtitle="All levels"
        />
        <StatCard
          icon={<Calendar size={20} />}
          label="This Month"
          value={statsLoading ? '…' : `$${parseFloat(stats?.this_month_earnings || '0').toFixed(2)}`}
        />
      </div>

      {/* Referral link */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-slate-300 mb-1">Your Referral Link</h2>
        <p className="text-xs text-slate-500 mb-4">Share this link to earn commissions</p>
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-slate-700/50 border border-slate-600 rounded-lg px-4 py-2.5 font-mono text-sm text-amber-400 truncate">
            {referralUrl}
          </div>
          <button
            onClick={copyReferralLink}
            className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-4 py-2.5 rounded-lg transition-colors text-sm whitespace-nowrap"
          >
            {copied ? <><Check size={16} /> Copied!</> : <><Copy size={16} /> Copy</>}
          </button>
          <a
            href={referralUrl}
            target="_blank"
            rel="noreferrer"
            className="p-2.5 border border-slate-600 hover:border-slate-500 rounded-lg text-slate-400 hover:text-white transition-colors"
          >
            <ExternalLink size={16} />
          </a>
        </div>
        <p className="text-xs text-slate-600 mt-3">
          Referral code: <span className="font-mono text-slate-400">{user?.referral_code}</span>
        </p>
      </div>

      {/* Recent earnings */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700">
          <h2 className="font-semibold text-white">Recent Earnings</h2>
        </div>
        {earningsLoading ? (
          <div className="px-6 py-8 text-center text-slate-500">Loading…</div>
        ) : recentEarnings.length === 0 ? (
          <div className="px-6 py-8 text-center text-slate-500 text-sm">
            No earnings yet. Share your referral link to start earning!
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-500 text-xs border-b border-slate-700">
                <th className="text-left px-6 py-3">Date</th>
                <th className="text-left px-6 py-3">From</th>
                <th className="text-left px-6 py-3">Tier</th>
                <th className="text-right px-6 py-3">Amount</th>
                <th className="text-right px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {recentEarnings.map((e) => (
                <tr key={e.id} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="px-6 py-3 text-slate-400">
                    {new Date(e.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-3 text-white">{e.source_name || '—'}</td>
                  <td className="px-6 py-3">{tierBadge(e.tier)}</td>
                  <td className="px-6 py-3 text-right text-amber-400 font-semibold">
                    ${parseFloat(e.amount).toFixed(2)}
                  </td>
                  <td className="px-6 py-3 text-right">{statusBadge(e.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
