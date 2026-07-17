import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, DollarSign, CreditCard, TrendingUp, Check, X, Plus, RefreshCw } from 'lucide-react'
import { adminApi, SimulateSubscriptionResult, CommissionConfigUpdate, SalesTeam } from '../lib/api'
import { StatCard } from '../components/StatCard'
import { useAuth } from '../contexts/AuthContext'

type Tab = 'affiliates' | 'payouts' | 'commission' | 'simulate' | 'team-config' | 'teams'

const PLATFORM_DEFAULTS = [20, 5, 5, 3, 2, 5, 10]

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

  // Teams tab state
  const [newTeamName, setNewTeamName] = useState('')
  const [newTeamPrefix, setNewTeamPrefix] = useState('')
  const [newTeamRate, setNewTeamRate] = useState('100')
  const [newTeamNotes, setNewTeamNotes] = useState('')
  const [teamsMsg, setTeamsMsg] = useState('')
  const [teamsError, setTeamsError] = useState('')
  const [selectedTeamForCodes, setSelectedTeamForCodes] = useState<SalesTeam | null>(null)
  const [newCodeNotes, setNewCodeNotes] = useState('')
  const [codesMsg, setCodesMsg] = useState('')

  // Commission config tab state
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)
  const [cfgMode, setCfgMode] = useState<'default' | 'custom'>('default')
  const [cfgPolicy, setCfgPolicy] = useState<'compress' | 'retain_admin'>('compress')
  const [cfgRates, setCfgRates] = useState<string[]>(['', '', '', '', '', '', ''])
  const [cfgMsg, setCfgMsg] = useState('')
  const [cfgError, setCfgError] = useState('')

  const qc = useQueryClient()

  const { data: stats } = useQuery({ queryKey: ['admin-stats'], queryFn: adminApi.getStats })
  const { data: affiliatesData } = useQuery({ queryKey: ['admin-affiliates'], queryFn: adminApi.getAffiliates })
  const { data: payoutsData, isLoading: payoutsLoading } = useQuery({
    queryKey: ['admin-payouts'],
    queryFn: adminApi.getPayouts,
  })
  const { data: teamsData } = useQuery({ queryKey: ['admin-teams'], queryFn: adminApi.listTeams })
  const { data: commissionConfig } = useQuery({
    queryKey: ['admin-commission-config', selectedTeamId],
    queryFn: () => adminApi.getCommissionConfig(selectedTeamId!),
    enabled: selectedTeamId !== null,
  })

  const { data: codesData, refetch: refetchCodes } = useQuery({
    queryKey: ['admin-referral-codes', selectedTeamForCodes?.id],
    queryFn: () => adminApi.listReferralCodes(selectedTeamForCodes!.id),
    enabled: selectedTeamForCodes !== null,
  })

  const createTeam = useMutation({
    mutationFn: adminApi.createTeam,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-teams'] })
      setNewTeamName(''); setNewTeamPrefix(''); setNewTeamRate('100'); setNewTeamNotes('')
      setTeamsMsg('Team created.'); setTeamsError('')
      setTimeout(() => setTeamsMsg(''), 3000)
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
      setTeamsError(typeof detail === 'string' ? detail : 'Failed to create team.')
      setTeamsMsg('')
    },
  })

  const toggleTeamActive = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      adminApi.updateTeam(id, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-teams'] }),
  })

  const createCode = useMutation({
    mutationFn: () => adminApi.createReferralCode(selectedTeamForCodes!.id, newCodeNotes || undefined),
    onSuccess: () => {
      refetchCodes()
      setNewCodeNotes('')
      setCodesMsg('Code generated.'); setTimeout(() => setCodesMsg(''), 3000)
    },
  })

  const deactivateCode = useMutation({
    mutationFn: (codeId: number) => adminApi.deactivateReferralCode(codeId),
    onSuccess: () => refetchCodes(),
  })

  const handleCreateTeam = (e: React.FormEvent) => {
    e.preventDefault()
    const prefix = newTeamPrefix.trim().toUpperCase()
    if (!/^[A-Z]{2,4}$/.test(prefix)) {
      setTeamsError('Prefix must be 2–4 uppercase letters (e.g. NS, WWL).')
      return
    }
    createTeam.mutate({ name: newTeamName, referral_prefix: prefix, commission_rate: parseFloat(newTeamRate), notes: newTeamNotes || undefined })
  }

  const updateConfig = useMutation({
    mutationFn: ({ teamId, data }: { teamId: number; data: CommissionConfigUpdate }) =>
      adminApi.updateCommissionConfig(teamId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-commission-config', selectedTeamId] })
      setCfgMsg('Commission rates saved.')
      setCfgError('')
      setTimeout(() => setCfgMsg(''), 3000)
    },
    onError: () => {
      setCfgError('Failed to save — check that all rates are between 0 and 100.')
      setCfgMsg('')
    },
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

  useEffect(() => {
    if (!isTeamAdmin || !teamsData?.teams) return
    const myTeam = teamsData.teams.find(t => t.id === user!.managed_team_id)
    if (myTeam && (!selectedTeamForCodes || selectedTeamForCodes.id !== myTeam.id)) {
      setSelectedTeamForCodes(myTeam)
    }
  }, [isTeamAdmin, teamsData, user?.managed_team_id])

  useEffect(() => {
    if (!commissionConfig) return
    setCfgMode(commissionConfig.commission_mode)
    setCfgPolicy(commissionConfig.unassigned_policy)
    setCfgRates([
      commissionConfig.custom_rate_l1,
      commissionConfig.custom_rate_l2,
      commissionConfig.custom_rate_l3,
      commissionConfig.custom_rate_l4,
      commissionConfig.custom_rate_l5,
      commissionConfig.custom_rate_l6,
      commissionConfig.custom_rate_l7,
    ].map((v) => (v === null ? '' : String(parseFloat(v)))))
  }, [commissionConfig])

  const handleSaveConfig = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTeamId) return
    const payload: CommissionConfigUpdate = { commission_mode: cfgMode, unassigned_policy: cfgPolicy }
    if (cfgMode === 'custom') {
      const keys = [
        'custom_rate_l1', 'custom_rate_l2', 'custom_rate_l3', 'custom_rate_l4',
        'custom_rate_l5', 'custom_rate_l6', 'custom_rate_l7',
      ] as const
      keys.forEach((key, i) => {
        const val = cfgRates[i]
        payload[key] = val === '' ? null : parseFloat(val)
      })
    }
    updateConfig.mutate({ teamId: selectedTeamId, data: payload })
  }

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

  const { user } = useAuth()
  const isTeamAdmin = !!(user?.managed_team_id)

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

  // ── Team admin view (scoped — only their team's referral codes) ──────────
  if (isTeamAdmin) {
    const myTeam = (teamsData?.teams ?? []).find(t => t.id === user!.managed_team_id)
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Team Admin</h1>
          <p className="text-slate-400 mt-1">
            Manage referral codes for{' '}
            <span className="text-amber-400 font-medium">{myTeam?.name ?? '…'}</span>
          </p>
        </div>

        {myTeam && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between gap-4">
              <div>
                <h3 className="text-base font-semibold text-white">
                  Referral Codes — <span className="text-amber-400">{myTeam.name}</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Format: <span className="font-mono">{myTeam.referral_prefix}-XXXXXXXX</span>
                </p>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                {codesMsg && <span className="text-xs text-green-400">{codesMsg}</span>}
                <input
                  type="text"
                  value={newCodeNotes}
                  onChange={(e) => setNewCodeNotes(e.target.value)}
                  placeholder="Notes (optional)"
                  className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-amber-500 w-44"
                />
                <button
                  onClick={() => {
                    if (!selectedTeamForCodes || selectedTeamForCodes.id !== myTeam.id) {
                      setSelectedTeamForCodes(myTeam)
                    }
                    createCode.mutate()
                  }}
                  disabled={createCode.isPending}
                  className="flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-900 text-sm font-semibold px-4 py-1.5 rounded-lg transition-colors whitespace-nowrap"
                >
                  <Plus size={14} />
                  {createCode.isPending ? 'Generating…' : 'Generate Code'}
                </button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-500 text-xs border-b border-slate-700 bg-slate-700/30">
                    <th className="text-left px-6 py-3">Code</th>
                    <th className="text-left px-6 py-3">Notes</th>
                    <th className="text-left px-6 py-3">Status</th>
                    <th className="text-left px-6 py-3">Created</th>
                    <th className="text-right px-6 py-3">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {(codesData?.codes ?? []).map((c) => (
                    <tr key={c.id} className="border-b border-slate-700/50 hover:bg-slate-700/10">
                      <td className="px-6 py-3 font-mono text-amber-400 text-xs tracking-wide">{c.code}</td>
                      <td className="px-6 py-3 text-slate-400 text-xs">{c.notes || '—'}</td>
                      <td className="px-6 py-3">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          c.is_active ? 'bg-green-500/20 text-green-400' : 'bg-slate-600 text-slate-500'
                        }`}>
                          {c.is_active ? 'active' : 'inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-3 text-slate-500 text-xs">{new Date(c.created_at).toLocaleDateString()}</td>
                      <td className="px-6 py-3 text-right">
                        {c.is_active && (
                          <button
                            onClick={() => deactivateCode.mutate(c.id)}
                            disabled={deactivateCode.isPending}
                            className="text-xs px-3 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
                          >
                            Deactivate
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(codesData?.codes ?? []).length === 0 && (
                <div className="p-8 text-center text-slate-500 text-sm">No codes yet. Generate one above.</div>
              )}
            </div>
          </div>
        )}
      </div>
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
          {(['affiliates', 'payouts', 'teams', 'commission', 'simulate', 'team-config'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`pb-3 text-sm font-medium capitalize transition-colors border-b-2 whitespace-nowrap ${
                tab === t
                  ? 'text-amber-400 border-amber-400'
                  : 'text-slate-400 border-transparent hover:text-white'
              }`}
            >
              {t === 'commission'
                ? 'Add Commission'
                : t === 'simulate'
                  ? 'Simulate Subscription'
                  : t === 'team-config'
                    ? 'Commission Rates'
                    : t === 'teams'
                      ? 'Teams'
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

      {/* Commission Rates tab */}
      {tab === 'team-config' && (
        <div className="max-w-lg">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-1">Commission Rates</h3>
            <p className="text-sm text-slate-400 mb-6">
              Set how commissions are distributed across 7 levels for a sales team.
              Custom mode overrides the platform defaults (L1 20% · L2 5% · L3 5% · L4 3% · L5 2% · L6 5% · L7 10%).
            </p>

            {/* Team selector */}
            {(teamsData?.teams ?? []).length === 0 ? (
              <p className="text-slate-500 text-sm">No sales teams configured yet.</p>
            ) : (
              <div className="mb-6">
                <label className="block text-sm text-slate-400 mb-1.5">Sales Team</label>
                <select
                  value={selectedTeamId ?? ''}
                  onChange={(e) => {
                    setSelectedTeamId(e.target.value ? Number(e.target.value) : null)
                    setCfgMsg('')
                    setCfgError('')
                  }}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-amber-500"
                >
                  <option value="">Select a team…</option>
                  {(teamsData?.teams ?? []).map((t) => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>
            )}

            {selectedTeamId && (
              <form onSubmit={handleSaveConfig} className="space-y-6">

                {cfgMsg && (
                  <div className="bg-green-500/10 border border-green-500/30 rounded-lg px-4 py-3 text-green-400 text-sm">
                    {cfgMsg}
                  </div>
                )}
                {cfgError && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
                    {cfgError}
                  </div>
                )}

                {/* Mode toggle */}
                <div>
                  <label className="block text-sm text-slate-400 mb-2">Commission Mode</label>
                  <div className="flex rounded-lg overflow-hidden border border-slate-600">
                    {(['default', 'custom'] as const).map((m) => (
                      <button
                        key={m}
                        type="button"
                        onClick={() => setCfgMode(m)}
                        className={`flex-1 py-2 text-sm font-medium transition-colors ${
                          cfgMode === m
                            ? 'bg-amber-500 text-slate-900'
                            : 'bg-slate-700 text-slate-400 hover:text-white'
                        }`}
                      >
                        {m === 'default' ? 'Default (platform rates)' : 'Custom'}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Custom mode options */}
                {cfgMode === 'custom' && (
                  <>
                    {/* Unassigned policy */}
                    <div>
                      <label className="block text-sm text-slate-400 mb-2">Unfilled level policy</label>
                      <div className="flex rounded-lg overflow-hidden border border-slate-600">
                        {(['compress', 'retain_admin'] as const).map((p) => (
                          <button
                            key={p}
                            type="button"
                            onClick={() => setCfgPolicy(p)}
                            className={`flex-1 py-2 text-sm font-medium transition-colors ${
                              cfgPolicy === p
                                ? 'bg-amber-500 text-slate-900'
                                : 'bg-slate-700 text-slate-400 hover:text-white'
                            }`}
                          >
                            {p === 'compress' ? 'Compress to top' : 'Retain by admin'}
                          </button>
                        ))}
                      </div>
                      <p className="text-xs text-slate-500 mt-1.5">
                        {cfgPolicy === 'compress'
                          ? 'When a chain is shorter than 7 levels, overflow commissions roll up to the topmost ancestor.'
                          : 'Overflow commissions go to the team admin affiliate instead of the topmost ancestor.'}
                      </p>
                    </div>

                    {/* Per-level rate inputs */}
                    <div>
                      <label className="block text-sm text-slate-400 mb-3">Per-level rates (%)</label>
                      <div className="grid grid-cols-2 gap-3">
                        {PLATFORM_DEFAULTS.map((def, i) => (
                          <div key={i}>
                            <label className="block text-xs text-slate-500 mb-1">
                              Level {i + 1}
                              <span className="ml-1 text-slate-600">· default {def}%</span>
                            </label>
                            <div className="relative">
                              <input
                                type="number"
                                min="0"
                                max="100"
                                step="0.01"
                                value={cfgRates[i]}
                                onChange={(e) => {
                                  const next = [...cfgRates]
                                  next[i] = e.target.value
                                  setCfgRates(next)
                                }}
                                placeholder={String(def)}
                                className="w-full bg-slate-700 border border-slate-600 rounded-lg pl-3 pr-8 py-2 text-white text-sm focus:outline-none focus:border-amber-500"
                              />
                              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs">%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                      <p className="text-xs text-slate-500 mt-2">Leave blank to treat a level as 0%.</p>
                    </div>
                  </>
                )}

                <button
                  type="submit"
                  disabled={updateConfig.isPending}
                  className="w-full bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-900 font-semibold py-2.5 rounded-lg transition-colors"
                >
                  {updateConfig.isPending ? 'Saving…' : 'Save'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Teams tab */}
      {tab === 'teams' && (
        <div className="space-y-6">
          {/* Create team form */}
          <div className="max-w-lg">
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-1">Create Sales Team</h3>
              <p className="text-sm text-slate-400 mb-5">
                Each team gets a unique prefix used to namespace its referral codes (e.g. prefix <span className="font-mono text-amber-400">NS</span> → codes like <span className="font-mono text-amber-400">NS-A3KX9Q7B</span>).
              </p>
              {teamsMsg && (
                <div className="mb-4 bg-green-500/10 border border-green-500/30 rounded-lg px-4 py-3 text-green-400 text-sm">{teamsMsg}</div>
              )}
              {teamsError && (
                <div className="mb-4 bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">{teamsError}</div>
              )}
              <form onSubmit={handleCreateTeam} className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-1.5">Team Name</label>
                  <input
                    type="text"
                    value={newTeamName}
                    onChange={(e) => setNewTeamName(e.target.value)}
                    required
                    className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-amber-500"
                    placeholder="NS Partners"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-slate-400 mb-1.5">Prefix <span className="text-slate-500">(2–4 letters)</span></label>
                    <input
                      type="text"
                      value={newTeamPrefix}
                      onChange={(e) => setNewTeamPrefix(e.target.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 4))}
                      required
                      maxLength={4}
                      className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white font-mono focus:outline-none focus:border-amber-500 uppercase"
                      placeholder="NS"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1.5">Commission Rate <span className="text-slate-500">(%)</span></label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      value={newTeamRate}
                      onChange={(e) => setNewTeamRate(e.target.value)}
                      required
                      className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-amber-500"
                      placeholder="100"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1.5">Notes <span className="text-slate-500">(optional)</span></label>
                  <input
                    type="text"
                    value={newTeamNotes}
                    onChange={(e) => setNewTeamNotes(e.target.value)}
                    className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-amber-500"
                    placeholder="Internal notes about this team"
                  />
                </div>
                <button
                  type="submit"
                  disabled={createTeam.isPending}
                  className="w-full bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-900 font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <Plus size={16} />
                  {createTeam.isPending ? 'Creating…' : 'Create Team'}
                </button>
              </form>
            </div>
          </div>

          {/* Teams list */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-700">
              <h3 className="text-base font-semibold text-white">All Teams</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-500 text-xs border-b border-slate-700 bg-slate-700/30">
                    <th className="text-left px-6 py-3">Name</th>
                    <th className="text-left px-6 py-3">Prefix</th>
                    <th className="text-left px-6 py-3">Commission</th>
                    <th className="text-left px-6 py-3">Members</th>
                    <th className="text-left px-6 py-3">Status</th>
                    <th className="text-right px-6 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(teamsData?.teams ?? []).map((team) => (
                    <tr
                      key={team.id}
                      className={`border-b border-slate-700/50 transition-colors ${
                        selectedTeamForCodes?.id === team.id ? 'bg-slate-700/40' : 'hover:bg-slate-700/20'
                      }`}
                    >
                      <td className="px-6 py-3 text-white font-medium">{team.name}</td>
                      <td className="px-6 py-3">
                        <span className="font-mono text-xs bg-slate-700 text-amber-400 px-2 py-1 rounded">{team.referral_prefix}</span>
                      </td>
                      <td className="px-6 py-3 text-slate-300">{parseFloat(team.commission_rate).toFixed(1)}%</td>
                      <td className="px-6 py-3 text-slate-400">{team.member_count}</td>
                      <td className="px-6 py-3">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          team.is_active ? 'bg-green-500/20 text-green-400' : 'bg-slate-600 text-slate-400'
                        }`}>
                          {team.is_active ? 'active' : 'inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => setSelectedTeamForCodes(selectedTeamForCodes?.id === team.id ? null : team)}
                            className="text-xs px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors"
                          >
                            {selectedTeamForCodes?.id === team.id ? 'Hide codes' : 'Ref codes'}
                          </button>
                          <button
                            onClick={() => toggleTeamActive.mutate({ id: team.id, is_active: !team.is_active })}
                            disabled={toggleTeamActive.isPending}
                            className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
                              team.is_active
                                ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400'
                                : 'bg-green-500/10 hover:bg-green-500/20 text-green-400'
                            }`}
                          >
                            {team.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(teamsData?.teams ?? []).length === 0 && (
                <div className="p-8 text-center text-slate-500 text-sm">No teams yet. Create one above.</div>
              )}
            </div>
          </div>

          {/* Referral codes panel for selected team */}
          {selectedTeamForCodes && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-base font-semibold text-white">
                    Referral Codes — <span className="text-amber-400">{selectedTeamForCodes.name}</span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Format: <span className="font-mono">{selectedTeamForCodes.referral_prefix}-XXXXXXXX</span>
                  </p>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  {codesMsg && <span className="text-xs text-green-400">{codesMsg}</span>}
                  <input
                    type="text"
                    value={newCodeNotes}
                    onChange={(e) => setNewCodeNotes(e.target.value)}
                    placeholder="Notes (optional)"
                    className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-amber-500 w-44"
                  />
                  <button
                    onClick={() => createCode.mutate()}
                    disabled={createCode.isPending}
                    className="flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-900 text-sm font-semibold px-4 py-1.5 rounded-lg transition-colors whitespace-nowrap"
                  >
                    <Plus size={14} />
                    {createCode.isPending ? 'Generating…' : 'Generate Code'}
                  </button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-500 text-xs border-b border-slate-700 bg-slate-700/30">
                      <th className="text-left px-6 py-3">Code</th>
                      <th className="text-left px-6 py-3">Notes</th>
                      <th className="text-left px-6 py-3">Status</th>
                      <th className="text-left px-6 py-3">Created</th>
                      <th className="text-right px-6 py-3">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(codesData?.codes ?? []).map((c) => (
                      <tr key={c.id} className="border-b border-slate-700/50 hover:bg-slate-700/10">
                        <td className="px-6 py-3 font-mono text-amber-400 text-xs tracking-wide">{c.code}</td>
                        <td className="px-6 py-3 text-slate-400 text-xs">{c.notes || '—'}</td>
                        <td className="px-6 py-3">
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            c.is_active ? 'bg-green-500/20 text-green-400' : 'bg-slate-600 text-slate-500'
                          }`}>
                            {c.is_active ? 'active' : 'inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-3 text-slate-500 text-xs">{new Date(c.created_at).toLocaleDateString()}</td>
                        <td className="px-6 py-3 text-right">
                          {c.is_active && (
                            <button
                              onClick={() => deactivateCode.mutate(c.id)}
                              disabled={deactivateCode.isPending}
                              className="text-xs px-3 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
                            >
                              Deactivate
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {(codesData?.codes ?? []).length === 0 && (
                  <div className="p-8 text-center text-slate-500 text-sm">No codes yet. Generate one above.</div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Simulate Subscription tab */}
      {tab === 'simulate' && (
        <div className="max-w-md">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-1">Simulate Subscription</h3>
            <p className="text-sm text-slate-400 mb-4">
              Distribute commissions up to 7 levels: L1 20% · L2 5% · L3 5% · L4 3% · L5 2% · L6 5% · L7 10%.
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
                <div className="px-4 py-3 border-b border-slate-600 text-sm text-slate-300 flex items-center justify-between">
                  <span>Commissions for ${parseFloat(simResult.subscription_amount).toFixed(2)} subscription</span>
                  <span className="text-amber-400 font-semibold">
                    Total: ${simResult.commissions.reduce((s, c) => s + parseFloat(c.amount), 0).toFixed(2)}
                  </span>
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
                        <td className="px-4 py-2">
                          {(() => {
                            const colors: Record<number, string> = {
                              1: 'bg-amber-500/20 text-amber-400',
                              2: 'bg-blue-500/20 text-blue-400',
                              3: 'bg-purple-500/20 text-purple-400',
                              4: 'bg-green-500/20 text-green-400',
                              5: 'bg-pink-500/20 text-pink-400',
                              6: 'bg-cyan-500/20 text-cyan-400',
                              7: 'bg-orange-500/20 text-orange-400',
                            }
                            return (
                              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[c.tier] || 'bg-slate-700 text-slate-400'}`}>
                                Level {c.tier}
                              </span>
                            )
                          })()}
                        </td>
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
