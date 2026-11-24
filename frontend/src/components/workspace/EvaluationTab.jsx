import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FlaskConical, Star, Thermometer } from 'lucide-react'
import { api } from '../../api'
import { STRATEGY_LABELS } from '../../lib/options'
import { Badge, Button, ErrorBanner } from '../ui'

const METRICS = [
  { key: 'distinct_2', label: 'Distinct-2', pct: false, help: 'Unique word pairs ÷ all word pairs. Higher means more varied wording; it usually rises with temperature.' },
  { key: 'brief_coverage', label: 'Brief coverage', pct: true, help: 'Share of content words from your brief that appear in the story. A lexical proxy for prompt adherence.' },
  { key: 'character_presence', label: 'Character presence', pct: true, help: 'Average share of chapters each named character appears in. A proxy for character consistency.' },
  { key: 'length_ratio', label: 'Length ratio', pct: false, help: 'Words written ÷ words requested. 1.0 means the length condition was followed exactly.' },
  { key: 'structure_score', label: 'Structure', pct: true, help: 'Share of format checks passed: 6 beats, 4 scenes and the requested number of chapters.' },
  { key: 'distinct_1', label: 'Distinct-1', pct: false, help: 'Unique words ÷ all words (lexical diversity).' },
]
const RATING_FIELDS = [
  ['coherence', 'Coherence'], ['creativity', 'Creativity'],
  ['adherence', 'Follows the brief'], ['character_consistency', 'Character consistency'],
]

const fmt = (v, pct) => (v === null || v === undefined ? '–' : pct ? `${Math.round(v * 100)}%` : v)
const avgRating = (r) => (r ? (RATING_FIELDS.reduce((a, [k]) => a + r[k], 0) / RATING_FIELDS.length).toFixed(1) : '–')

function Stars({ value, onChange, label }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-sm text-slate-200">{label}</span>
      <div className="flex gap-1" role="radiogroup" aria-label={label}>
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} type="button" onClick={() => onChange(n)} aria-label={`${n} of 5`}
            className={n <= value ? 'text-amber-300' : 'text-slate-600 hover:text-slate-400'}>
            <Star size={18} fill={n <= value ? 'currentColor' : 'none'} />
          </button>
        ))}
      </div>
    </div>
  )
}

export default function EvaluationTab({ story, setStory }) {
  const m = story.metrics ?? {}
  const demo = story.provider === 'mock'
  const [rating, setRating] = useState(story.human_rating ?? { coherence: 0, creativity: 0, adherence: 0, character_consistency: 0, notes: '' })
  const [saved, setSaved] = useState(false)
  const [related, setRelated] = useState([])
  const [running, setRunning] = useState('')
  const [error, setError] = useState('')

  const loadRelated = useCallback(() => api.related(story.id).then(setRelated).catch(() => {}), [story.id])
  useEffect(() => { loadRelated() }, [loadRelated])

  const saveRating = async () => {
    setError('')
    try {
      setStory(await api.updateStory(story.id, { human_rating: rating }))
      setSaved(true); setTimeout(() => setSaved(false), 2500)
    } catch (e) { setError(e.message) }
  }

  /** Re-run the same idea with other settings, one request at a time (keeps within free API limits). */
  const runExperiment = async (variants, name) => {
    setError('')
    for (let i = 0; i < variants.length; i++) {
      setRunning(`${name}: run ${i + 1} of ${variants.length}`)
      try {
        await api.generate({
          idea: story.idea, plot: story.plot,
          sampling: { ...story.sampling, ...variants[i].sampling }, strategy: variants[i].strategy ?? story.strategy,
        })
        await loadRelated()
      } catch (e) { setError(e.message); break }
    }
    setRunning('')
  }
  const otherStrategies = ['direct', 'interview', 'cot', 'tot'].filter((s) => !related.some((r) => r.strategy === s && r.sampling.temperature === story.sampling.temperature))
  const temps = [0.3, 0.9, 1.5].filter((t) => !related.some((r) => r.strategy === story.strategy && r.sampling.temperature === t))

  return (
    <div className="flex flex-col gap-6">
      {demo && (
        <div className="rounded-xl border border-amber-400/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
          This story was made in demo mode from a template, so these numbers only show that the metrics work. Use live mode for results you report.
        </div>
      )}
      <ErrorBanner message={error} onClose={() => setError('')} />

      <section>
        <h3 className="text-sm font-medium text-slate-100">Automatic metrics</h3>
        <p className="text-xs text-muted mt-1">Reference-free: a creative story has no single correct answer, so BLEU or ROUGE against a reference would not be meaningful here.</p>
        <div className="mt-3 grid grid-cols-2 lg:grid-cols-3 gap-3">
          {METRICS.map(({ key, label, pct, help }) => (
            <div key={key} className="card-inner p-4">
              <p className="text-xs text-muted">{label}</p>
              <p className="text-2xl font-semibold text-white mt-1 tabular-nums">{fmt(m[key], pct)}</p>
              <p className="text-[11px] text-muted mt-1.5 leading-relaxed">{help}</p>
            </div>
          ))}
        </div>
        {m.brief_terms_missing?.length > 0 && (
          <p className="text-xs text-muted mt-3">Brief words not found in the story: {m.brief_terms_missing.join(', ')}</p>
        )}
        <p className="text-xs text-muted mt-1">{m.word_count} words · {m.llm_calls} LLM calls · {(m.latency_ms / 1000).toFixed(1)} s generation time</p>
      </section>

      <section className="card-inner p-5">
        <h3 className="text-sm font-medium text-slate-100">Human evaluation</h3>
        <p className="text-xs text-muted mt-1">Your own 1–5 ratings, stored separately from the automatic metrics.</p>
        <div className="mt-4 grid sm:grid-cols-2 gap-x-10 gap-y-3">
          {RATING_FIELDS.map(([k, label]) => (
            <Stars key={k} label={label} value={rating[k]} onChange={(v) => setRating({ ...rating, [k]: v })} />
          ))}
        </div>
        <textarea className="field mt-4" rows={2} placeholder="Notes (optional)" value={rating.notes}
          onChange={(e) => setRating({ ...rating, notes: e.target.value })} />
        <div className="mt-3 flex items-center gap-3">
          <Button variant="primary" onClick={saveRating} disabled={RATING_FIELDS.some(([k]) => !rating[k])}>Save rating</Button>
          {saved && <span className="text-xs text-emerald-300">Rating saved</span>}
        </div>
      </section>

      <section>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h3 className="text-sm font-medium text-slate-100">Experiment: same idea, different settings</h3>
            <p className="text-xs text-muted mt-1">Every run of this exact idea and plot dials, side by side.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => runExperiment(otherStrategies.map((s) => ({ strategy: s })), 'Strategies')}
              loading={running.startsWith('Strategies')} disabled={!!running || otherStrategies.length === 0}>
              <FlaskConical size={15} /> Compare all strategies
            </Button>
            <Button onClick={() => runExperiment(temps.map((t) => ({ sampling: { temperature: t } })), 'Temperatures')}
              loading={running.startsWith('Temperatures')} disabled={!!running || temps.length === 0}>
              <Thermometer size={15} /> Temperature sweep (0.3 / 0.9 / 1.5)
            </Button>
          </div>
        </div>
        {running && <p className="mt-2 text-xs text-violet-300">{running}…</p>}
        <div className="mt-3 overflow-x-auto scroll-thin card-inner">
          <table className="w-full text-sm">
            <thead className="text-xs text-muted text-left">
              <tr className="border-b border-white/5">
                {['Run', 'Strategy', 'Temp.', 'Distinct-2', 'Brief coverage', 'Characters', 'Length', 'Structure', 'Time', 'Human avg.'].map((h) => (
                  <th key={h} className="px-3 py-2.5 font-normal whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {related.map((r) => (
                <tr key={r.id} className={`border-b border-white/5 last:border-0 ${r.id === story.id ? 'bg-violet-500/10' : ''}`}>
                  <td className="px-3 py-2.5"><Link to={`/library/${r.id}`} className="text-violet-300 hover:underline">#{r.id}</Link></td>
                  <td className="px-3 py-2.5 whitespace-nowrap">{STRATEGY_LABELS[r.strategy]}</td>
                  <td className="px-3 py-2.5 tabular-nums">{r.sampling.temperature}</td>
                  <td className="px-3 py-2.5 tabular-nums">{fmt(r.metrics?.distinct_2)}</td>
                  <td className="px-3 py-2.5 tabular-nums">{fmt(r.metrics?.brief_coverage, true)}</td>
                  <td className="px-3 py-2.5 tabular-nums">{fmt(r.metrics?.character_presence, true)}</td>
                  <td className="px-3 py-2.5 tabular-nums">{fmt(r.metrics?.length_ratio)}</td>
                  <td className="px-3 py-2.5 tabular-nums">{fmt(r.metrics?.structure_score, true)}</td>
                  <td className="px-3 py-2.5 tabular-nums whitespace-nowrap">{((r.metrics?.latency_ms ?? 0) / 1000).toFixed(1)} s</td>
                  <td className="px-3 py-2.5 tabular-nums">{avgRating(r.human_rating)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-muted">
          {related.length < 2 ? 'Run an experiment to add rows. ' : ''}Each run makes 1–3 requests to the text model, so this uses your free quota. <Badge>{related.length} runs</Badge>
        </p>
      </section>
    </div>
  )
}
