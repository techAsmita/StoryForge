/** Character relationship map drawn from the LLM's structured output. */
export default function RelationshipMap({ characters, relationships = [] }) {
  if (!characters?.length) return null
  const hero = characters.find((c) => c.role === 'protagonist') ?? characters[0]
  const others = characters.filter((c) => c !== hero).slice(0, 4)
  const W = 520, H = 250
  const slots = [[95, 60], [95, 190], [425, 60], [425, 190]]
  const pos = { [hero.name]: [W / 2, H / 2] }
  others.forEach((c, i) => { pos[c.name] = slots[i] })
  const initials = (n) => n.split(/\s+/).filter(Boolean).map((w) => w[0]).join('').slice(0, 2).toUpperCase()

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-xl mx-auto" role="img" aria-label="Character relationship map">
      {relationships.filter((r) => pos[r.source] && pos[r.target]).map((r, i) => {
        const [x1, y1] = pos[r.source], [x2, y2] = pos[r.target]
        return (
          <g key={i}>
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#8b5cf6" strokeWidth="1.5" strokeDasharray="5 4" opacity="0.8" />
            <text x={(x1 + x2) / 2} y={(y1 + y2) / 2 - 7} textAnchor="middle" fontSize="12" fill="#c4b5fd"
              fontFamily="Inter">{r.label.charAt(0).toUpperCase() + r.label.slice(1).toLowerCase()}</text>
          </g>
        )
      })}
      {[hero, ...others].map((c) => {
        const [x, y] = pos[c.name]
        const big = c === hero
        return (
          <g key={c.name}>
            <circle cx={x} cy={y} r={big ? 40 : 30} fill="#1c1640" stroke={big ? '#a78bfa' : '#7c6cf0'} strokeWidth="2"
              style={{ filter: 'drop-shadow(0 0 10px rgba(139,92,246,0.6))' }} />
            <text x={x} y={y + 6} textAnchor="middle" fontSize={big ? 20 : 15} fontWeight="600" fill="#ede9fe" fontFamily="Inter">{initials(c.name)}</text>
            <text x={x} y={y + (big ? 58 : 48)} textAnchor="middle" fontSize="12" fill="#b4acd6" fontFamily="Inter">{c.name}</text>
          </g>
        )
      })}
    </svg>
  )
}
