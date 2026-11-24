import { useState } from 'react'
import { ChevronDown, LoaderCircle } from 'lucide-react'

export function Select({ value, onChange, children, className = '', ...rest }) {
  return (
    <div className={`relative ${className}`}>
      <select className="field select" value={value} onChange={(e) => onChange(e.target.value)} {...rest}>
        {children}
      </select>
      {/* sits 14px in from the edge rather than hugging it */}
      <ChevronDown size={16} className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-violet-300" />
    </div>
  )
}

export function Slider({ label, value, onChange, min = 0, max = 100, step = 1, left, right, format, hint }) {
  const pct = ((value - min) / (max - min)) * 100
  return (
    <div>
      <div className="flex justify-between items-baseline text-sm">
        <span className="text-slate-200">{label}</span>
        <span className="text-violet-300 tabular-nums text-xs">{format ? format(value) : value}</span>
      </div>
      <input type="range" className="slider mt-2.5" min={min} max={max} step={step} value={value}
        style={{ '--pct': `${pct}%` }} aria-label={label} onChange={(e) => onChange(Number(e.target.value))} />
      {(left || right) && (
        <div className="flex justify-between text-[11px] text-muted mt-1"><span>{left}</span><span>{right}</span></div>
      )}
      {hint && <p className="text-[11px] text-muted mt-1">{hint}</p>}
    </div>
  )
}

export function Collapsible({ icon: Icon, title, subtitle, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="card-inner">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open}
        className="w-full flex items-center gap-3 px-4 py-3.5 text-left">
        {Icon && <Icon size={20} className="text-violet-300 shrink-0" />}
        <span className="flex-1 min-w-0">
          <span className="block text-sm font-medium text-slate-100">{title}</span>
          {subtitle && <span className="block text-xs text-muted truncate">{subtitle}</span>}
        </span>
        <ChevronDown size={18} className={`text-violet-300 transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && <div className="px-4 pb-4 flex flex-col gap-4">{children}</div>}
    </div>
  )
}

export function Tabs({ tabs, value, onChange, size = 'md' }) {
  return (
    <div className="flex gap-1.5 overflow-x-auto no-scrollbar">
      {tabs.map(({ id, label, icon: Icon, count }) => (
        <button key={id} type="button" onClick={() => onChange(id)}
          className={`flex items-center gap-2 whitespace-nowrap rounded-full border transition
            ${size === 'sm' ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-sm'}
            ${value === id
              ? 'bg-violet-600/90 border-violet-400/60 text-white shadow-[0_0_20px_rgba(139,92,246,.35)]'
              : 'border-white/10 text-slate-300 hover:bg-white/5'}`}>
          {Icon && <Icon size={size === 'sm' ? 14 : 16} />} {label}
          {count !== undefined && (
            <span className={`rounded-full px-1.5 text-[11px] ${value === id ? 'bg-white/20' : 'bg-white/10'}`}>{count}</span>
          )}
        </button>
      ))}
    </div>
  )
}

export function Button({ children, variant = 'ghost', loading, className = '', ...rest }) {
  const styles = {
    primary: 'btn-primary text-white',
    ghost: 'border border-white/12 text-slate-200 hover:bg-white/5',
    danger: 'border border-rose-400/40 text-rose-200 hover:bg-rose-500/10',
  }
  return (
    <button type="button" className={`inline-flex items-center justify-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition disabled:opacity-60 ${styles[variant]} ${className}`}
      disabled={loading || rest.disabled} {...rest}>
      {loading && <LoaderCircle size={16} className="animate-spin" />} {children}
    </button>
  )
}

export function Badge({ tone = 'violet', children }) {
  const tones = {
    violet: 'border-violet-400/40 text-violet-200 bg-violet-500/10',
    green: 'border-emerald-400/40 text-emerald-200 bg-emerald-500/10',
    amber: 'border-amber-400/40 text-amber-200 bg-amber-500/10',
    rose: 'border-rose-400/40 text-rose-200 bg-rose-500/10',
  }
  return <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs ${tones[tone]}`}>{children}</span>
}

export function Label({ children, aside }) {
  return (
    <div className="flex justify-between items-baseline mb-1.5">
      <span className="text-sm text-slate-200">{children}</span>
      {aside && <span className="text-xs text-muted">{aside}</span>}
    </div>
  )
}

export function ErrorBanner({ message, onClose }) {
  if (!message) return null
  return (
    <div role="alert" className="flex items-start justify-between gap-4 rounded-xl border border-rose-400/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
      <span>{message}</span>
      {onClose && <button onClick={onClose} className="text-rose-200 hover:text-white" aria-label="Dismiss">×</button>}
    </div>
  )
}
