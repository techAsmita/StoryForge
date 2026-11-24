import { NavLink } from 'react-router-dom'
import { WandSparkles, BookOpen, Compass, Settings } from 'lucide-react'
import { useApp } from '../lib/AppContext'

export const NAV = [
  { to: '/', label: 'Create', icon: WandSparkles, end: true },
  { to: '/library', label: 'Library', icon: BookOpen },
  { to: '/explore', label: 'Explore', icon: Compass },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export function Logo() {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <img src="/favicon.svg" alt="" className="size-12" />
      <span className="text-xl font-semibold tracking-tight">Story<span className="text-violet-400">Forge</span></span>
    </div>
  )
}

export function ModeCard() {
  const { health, healthError } = useApp()
  if (healthError) {
    return <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 p-3 text-xs text-rose-100">Backend offline. Start uvicorn on port 8000.</div>
  }
  if (!health) return null
  const live = health.mode === 'live'
  return (
    <div className="relative overflow-hidden rounded-2xl border border-violet-400/20 bg-gradient-to-b from-violet-600/25 to-[#140f2e] p-3.5 pb-12 text-xs">
      <svg viewBox="0 0 200 60" preserveAspectRatio="none" className="absolute inset-x-0 bottom-0 h-12 w-full" aria-hidden="true">
        <path d="M0 40 C40 10 80 60 120 30 S180 20 200 35 V60 H0Z" fill="#7c3aed" opacity=".35" />
        <path d="M0 48 C50 25 90 62 140 40 S185 38 200 46 V60 H0Z" fill="#a855f7" opacity=".45" />
      </svg>
      <div className="relative flex items-center gap-2 font-medium text-slate-100">
        <span className={`size-2 rounded-full ${live ? 'bg-emerald-400' : 'bg-amber-400'}`} />
        {live ? 'Live mode' : 'Demo mode'}
      </div>
      <p className="relative mt-1.5 text-muted leading-relaxed">
        {live ? `Text by ${health.model}. Images by ${health.image_provider === 'openai' ? 'OpenAI' : 'Pollinations'}.` : 'Template text, no API calls. Add a Gemini key in backend/.env to go live.'}
      </p>
    </div>
  )
}

export default function Sidebar() {
  return (
    <>
      <aside className="hidden lg:flex fixed inset-y-0 left-0 w-56 flex-col border-r border-white/5 bg-[#0e0b21]/90 backdrop-blur px-4 py-7">
        <Logo />
        <nav className="mt-10 flex flex-col gap-1.5">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end}
              className={({ isActive }) => `flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm transition
                ${isActive ? 'bg-violet-600/80 text-white shadow-[0_0_24px_rgba(139,92,246,.35)]' : 'text-slate-300 hover:bg-white/5'}`}>
              <Icon size={18} /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto"><ModeCard /></div>
      </aside>

      {/* Phones and tablets: bottom tab bar */}
      <nav className="lg:hidden fixed bottom-0 inset-x-0 z-40 grid grid-cols-4 border-t border-white/10 bg-[#0e0b21]/95 backdrop-blur pb-[env(safe-area-inset-bottom)]">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end}
            className={({ isActive }) => `flex flex-col items-center gap-1 py-2.5 text-[11px] ${isActive ? 'text-violet-300' : 'text-slate-400'}`}>
            <Icon size={20} /> {label}
          </NavLink>
        ))}
      </nav>
    </>
  )
}
