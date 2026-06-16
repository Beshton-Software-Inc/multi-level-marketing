import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Users, User } from 'lucide-react'
import { affiliateApi, TeamMember } from '../lib/api'

const LEVEL_COLORS = [
  'bg-amber-500/20 text-amber-400 border-amber-500/30',
  'bg-blue-500/20 text-blue-400 border-blue-500/30',
  'bg-purple-500/20 text-purple-400 border-purple-500/30',
  'bg-green-500/20 text-green-400 border-green-500/30',
  'bg-pink-500/20 text-pink-400 border-pink-500/30',
]

export function Team() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['team'],
    queryFn: affiliateApi.getTeam,
  })

  const members: TeamMember[] = data?.members || []
  const maxDepth = members.reduce((max, m) => Math.max(max, m.depth), 0)

  const byDepth: Record<number, TeamMember[]> = {}
  for (let d = 1; d <= maxDepth; d++) {
    byDepth[d] = members.filter((m) => m.depth === d)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">My Team</h1>
        <p className="text-slate-400 mt-1">Your entire downline network</p>
      </div>

      {/* Summary bar */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{members.filter((m) => m.depth === 1).length}</p>
          <p className="text-xs text-slate-400 mt-1">Direct Referrals</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-amber-400">{members.length}</p>
          <p className="text-xs text-slate-400 mt-1">Total Team</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{maxDepth}</p>
          <p className="text-xs text-slate-400 mt-1">Levels Deep</p>
        </div>
      </div>

      {isLoading && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-8 text-center text-slate-500">
          Loading team…
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
          Failed to load team. Please try again.
        </div>
      )}

      {!isLoading && members.length === 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-12 text-center">
          <Users size={40} className="text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">Your team is empty.</p>
          <p className="text-slate-500 text-sm mt-1">Share your referral link to start building your network.</p>
        </div>
      )}

      {Object.entries(byDepth).map(([depth, lvMembers]) => {
        const d = parseInt(depth)
        const colorClass = LEVEL_COLORS[(d - 1) % LEVEL_COLORS.length]
        return (
          <div key={depth} className="space-y-3">
            <div className="flex items-center gap-3">
              <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${colorClass}`}>
                Level {depth}
              </span>
              <span className="text-slate-500 text-sm">{lvMembers.length} member{lvMembers.length !== 1 ? 's' : ''}</span>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
              {lvMembers.map((member) => (
                <div
                  key={member.id}
                  className="bg-slate-800 border border-slate-700 hover:border-slate-600 rounded-xl p-4 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-slate-700 flex items-center justify-center text-slate-300">
                        <User size={16} />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">{member.name}</p>
                        <p className="text-xs text-slate-500 truncate max-w-[160px]">{member.email}</p>
                      </div>
                    </div>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        member.status === 'active'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-slate-700 text-slate-400'
                      }`}
                    >
                      {member.status}
                    </span>
                  </div>
                  <div className="mt-3 pt-3 border-t border-slate-700/50 grid grid-cols-2 gap-2 text-xs text-slate-500">
                    <div>
                      <span className="block text-white font-semibold">{member.direct_referrals}</span>
                      Direct refs
                    </div>
                    <div className="text-right">
                      <span className="block text-amber-400 font-semibold">
                        ${parseFloat(member.total_earnings).toFixed(2)}
                      </span>
                      Earned
                    </div>
                  </div>
                  <p className="text-xs text-slate-600 mt-2">
                    Joined {new Date(member.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
