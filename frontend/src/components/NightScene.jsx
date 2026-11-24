import { useState } from 'react'

/** Decorative night sky with moon and castle silhouette, drawn in SVG (no external images). */
const STARS = Array.from({ length: 70 }, (_, i) => ({
  x: (i * 137.5) % 1000, y: (i * 61.3) % 260, r: (i % 5 === 0 ? 1.6 : 0.9),
}))
const TOWERS = [
  { x: 560, w: 26, h: 120 }, { x: 600, w: 34, h: 170 }, { x: 648, w: 22, h: 140 },
  { x: 680, w: 40, h: 230 }, { x: 735, w: 24, h: 160 }, { x: 772, w: 30, h: 195 },
  { x: 815, w: 22, h: 130 }, { x: 850, w: 28, h: 150 },
]

export default function NightScene({ hue = 265, className = '', castle = true }) {
  const base = 330
  return (
    <svg viewBox="0 0 1000 340" preserveAspectRatio="xMaxYMid slice" className={className} aria-hidden="true">
      <defs>
        <linearGradient id={`sky${hue}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={`hsl(${hue} 55% 14%)`} />
          <stop offset="0.6" stopColor={`hsl(${hue} 60% 24%)`} />
          <stop offset="1" stopColor={`hsl(${hue} 45% 12%)`} />
        </linearGradient>
        <radialGradient id={`moon${hue}`}>
          <stop offset="0" stopColor="#f5f0ff" />
          <stop offset="0.55" stopColor="#d9ccff" />
          <stop offset="1" stopColor={`hsl(${hue} 80% 75%)`} stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="1000" height="340" fill={`url(#sky${hue})`} />
      {STARS.map((s, i) => <circle key={i} cx={s.x} cy={s.y} r={s.r} fill="#fff" opacity={0.35 + (i % 4) * 0.15} />)}
      <circle cx="760" cy="95" r="120" fill={`url(#moon${hue})`} opacity="0.35" />
      <circle cx="760" cy="95" r="52" fill="#efe8ff" opacity="0.9" />
      <path d={`M0 ${base} L0 260 Q120 210 240 250 T480 235 T720 250 T1000 225 L1000 ${base} Z`} fill={`hsl(${hue} 40% 10%)`} opacity="0.85" />
      {castle && (
        <g fill={`hsl(${hue} 45% 7%)`}>
          <path d={`M520 ${base} Q690 230 900 ${base} Z`} />
          <rect x="570" y="225" width="300" height="80" />
          {TOWERS.map((t, i) => (
            <g key={i}>
              <rect x={t.x} y={300 - t.h} width={t.w} height={t.h} />
              <polygon points={`${t.x - 4},${300 - t.h} ${t.x + t.w / 2},${300 - t.h - t.w * 1.6} ${t.x + t.w + 4},${300 - t.h}`} />
              <rect x={t.x + t.w / 2 - 2.5} y={300 - t.h + 20} width="5" height="9" fill="#f6c76b" opacity="0.8" />
            </g>
          ))}
        </g>
      )}
      <path d={`M0 ${base} L0 300 Q200 270 380 300 T760 295 T1000 290 L1000 ${base} Z`} fill={`hsl(${hue} 50% 6%)`} />
    </svg>
  )
}

/**
 * Painted artwork from /public/art (made by backend/scripts/generate_art.py).
 * Until the file exists, the SVG night scene is shown instead.
 */
export function Art({ name, hue, castle = true, className = '', imgClassName = 'object-cover' }) {
  const [missing, setMissing] = useState(!name)
  if (missing) return <NightScene hue={hue} castle={castle} className={className} />
  return <img src={`/art/${name}.jpg`} alt="" aria-hidden="true" onError={() => setMissing(true)} className={`${className} ${imgClassName}`} />
}

/** Page header: painted art fading into the page, large title on the dark left side (as in the mockups). */
export function PageHero({ title, accent, subtitle, children, hue, art }) {
  return (
    <header className="relative overflow-hidden rounded-3xl border border-violet-400/10 min-h-[190px] sm:min-h-[215px] flex items-center">
      <Art name={art} hue={hue} className="absolute inset-0 h-full w-full" imgClassName="object-cover object-right" />
      <div className="absolute inset-0 bg-gradient-to-r from-[#0b0919]/95 via-[#0b0919]/60 sm:via-[#0b0919]/25 to-transparent" />
      <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-[#0b0919]/70 to-transparent" />
      <div className="relative w-full px-6 sm:px-10 py-7">
        <h1 className="font-sans text-4xl sm:text-5xl font-extrabold tracking-tight text-white drop-shadow-[0_2px_12px_rgba(0,0,0,.6)]">
          {title} {accent && <span className="bg-gradient-to-r from-violet-300 to-fuchsia-400 bg-clip-text text-transparent">{accent}</span>}
        </h1>
        {subtitle && <p className="mt-2.5 text-base sm:text-lg text-slate-100/90 max-w-2xl drop-shadow-[0_1px_8px_rgba(0,0,0,.7)]">{subtitle}</p>}
        {children}
      </div>
    </header>
  )
}
