import React, { ReactNode } from 'react'

interface StatCardProps {
  icon: ReactNode
  label: string
  value: string | number
  subtitle?: string
  accent?: boolean
}

export function StatCard({ icon, label, value, subtitle, accent }: StatCardProps) {
  return (
    <div className={`rounded-xl p-5 border ${accent ? 'bg-amber-500/10 border-amber-500/30' : 'bg-slate-800 border-slate-700'}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400 mb-1">{label}</p>
          <p className={`text-2xl font-bold ${accent ? 'text-amber-400' : 'text-white'}`}>{value}</p>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-2 rounded-lg ${accent ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-700 text-slate-300'}`}>
          {icon}
        </div>
      </div>
    </div>
  )
}
