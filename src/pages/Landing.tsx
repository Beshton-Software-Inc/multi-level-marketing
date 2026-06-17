import React from 'react'
import { Link } from 'react-router-dom'
import { Scale, Users, TrendingUp, CheckCircle, ArrowRight, DollarSign, Shield, BarChart2 } from 'lucide-react'

export function Landing() {
  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Navbar */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-slate-800 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amber-500 rounded-lg">
            <Scale size={20} className="text-slate-900" />
          </div>
          <div>
            <span className="font-bold text-white">WinWin Law</span>
            <span className="text-amber-400 text-sm ml-2">Team</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/login"
            className="text-sm text-slate-300 hover:text-white transition-colors px-4 py-2"
          >
            Sign In
          </Link>
          <Link
            to="/register"
            className="text-sm bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            Join Now
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-amber-500/10 via-transparent to-slate-900 pointer-events-none" />
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="max-w-7xl mx-auto px-6 py-24 text-center relative">
          <div className="inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-full px-4 py-1.5 text-amber-400 text-sm mb-8">
            <DollarSign size={14} />
            Earn up to 20% commission per referral
          </div>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Turn Legal Connections
            <br />
            <span className="text-amber-400">Into Income</span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10">
            Join the WinWin Law affiliate program. Refer law firms and legal professionals,
            earn recurring commissions, and build a passive income stream — all while helping
            people access justice.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/register"
              className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-8 py-4 rounded-xl text-lg transition-colors"
            >
              Start Earning Today <ArrowRight size={20} />
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 border border-slate-600 hover:border-slate-500 text-slate-300 hover:text-white px-8 py-4 rounded-xl text-lg transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 px-6 bg-slate-800/30">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-4">How It Works</h2>
          <p className="text-slate-400 text-center mb-12">Get started in minutes and start earning</p>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Create Your Account',
                desc: 'Sign up for free and get your unique referral link instantly.',
                icon: <Users size={24} className="text-amber-400" />,
              },
              {
                step: '02',
                title: 'Share Your Link',
                desc: 'Share with law firms, attorneys, and legal professionals who can benefit from WinWin Law.',
                icon: <TrendingUp size={24} className="text-amber-400" />,
              },
              {
                step: '03',
                title: 'Earn Commissions',
                desc: 'Earn recurring commissions when your referrals subscribe — and when their referrals subscribe too.',
                icon: <DollarSign size={24} className="text-amber-400" />,
              },
            ].map((item) => (
              <div key={item.step} className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-4xl font-bold text-slate-700">{item.step}</span>
                  <div className="p-2 bg-amber-500/10 rounded-lg">{item.icon}</div>
                </div>
                <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Commission tiers */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-4">Commission Structure</h2>
          <p className="text-slate-400 text-center mb-12">Earn from multiple levels of your network</p>
          <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
            <div className="grid grid-cols-4 gap-0 text-sm font-semibold text-slate-400 px-6 py-3 border-b border-slate-700 bg-slate-700/30">
              <div>Level</div>
              <div>Who</div>
              <div>Rate</div>
              <div>Example ($100/mo sub)</div>
            </div>
            {[
              { level: 'Level 1', who: 'Direct referrals', rate: '20%', example: '$20.00', highlight: true },
              { level: 'Level 2', who: "2nd-degree connections", rate: '5%', example: '$5.00', highlight: false },
              { level: 'Level 3', who: '3rd-degree connections', rate: '5%', example: '$5.00', highlight: false },
              { level: 'Level 4', who: '4th-degree connections', rate: '3%', example: '$3.00', highlight: false },
              { level: 'Level 5', who: '5th-degree connections', rate: '2%', example: '$2.00', highlight: false },
              { level: 'Level 6', who: '6th-degree connections', rate: '5%', example: '$5.00', highlight: false },
              { level: 'Level 7', who: '7th-degree connections', rate: '10%', example: '$10.00', highlight: false },
            ].map((row) => (
              <div
                key={row.level}
                className={`grid grid-cols-4 gap-0 px-6 py-4 border-b border-slate-700/50 text-sm ${
                  row.highlight ? 'bg-amber-500/5' : ''
                }`}
              >
                <div className={`font-semibold ${row.highlight ? 'text-amber-400' : 'text-white'}`}>
                  {row.level}
                </div>
                <div className="text-slate-400">{row.who}</div>
                <div className={`font-bold text-lg ${row.highlight ? 'text-amber-400' : 'text-white'}`}>
                  {row.rate}
                </div>
                <div className="text-slate-300">{row.example}</div>
              </div>
            ))}
          </div>
          <p className="text-center text-xs text-slate-500 mt-4">
            * Commissions calculated on monthly subscription amount
          </p>
        </div>
      </section>

      {/* Why section */}
      <section className="py-20 px-6 bg-slate-800/30">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Why WinWin Law?</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: <Shield size={28} className="text-amber-400" />,
                title: 'Trusted Legal Platform',
                desc: 'WinWin Law is a vetted marketplace connecting clients with licensed law firms. Your referrals trust what you promote.',
              },
              {
                icon: <DollarSign size={28} className="text-amber-400" />,
                title: 'Recurring Commissions',
                desc: 'Earn monthly as long as your referrals remain subscribed. Build a true passive income stream over time.',
              },
              {
                icon: <BarChart2 size={28} className="text-amber-400" />,
                title: 'Real-Time Tracking',
                desc: 'Monitor your team, earnings, and commissions in real time through your personal affiliate dashboard.',
              },
            ].map((f) => (
              <div key={f.title} className="text-center">
                <div className="inline-flex p-4 bg-amber-500/10 rounded-2xl mb-4">{f.icon}</div>
                <h3 className="text-lg font-semibold mb-3">{f.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <div className="bg-gradient-to-r from-amber-500/10 to-amber-600/10 border border-amber-500/20 rounded-2xl p-12">
            <h2 className="text-3xl font-bold mb-4">Ready to Start Earning?</h2>
            <p className="text-slate-400 mb-8">
              Join hundreds of affiliates already building income with WinWin Law.
              It's free to join — no subscription required.
            </p>
            <Link
              to="/register"
              className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-8 py-4 rounded-xl text-lg transition-colors"
            >
              Join the Team <ArrowRight size={20} />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-8 px-6 text-center text-slate-500 text-sm">
        <p>© {new Date().getFullYear()} WinWin Law Team. All rights reserved.</p>
      </footer>
    </div>
  )
}
