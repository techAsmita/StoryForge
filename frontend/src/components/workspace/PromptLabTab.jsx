import { STRATEGY_LABELS } from '../../lib/options'

function Row({ label, children }) {
  return (<><dt className="text-muted">{label}</dt><dd className="text-slate-200">{children}</dd></>)
}

export default function PromptLabTab({ story }) {
  const { artifacts, runs, sampling } = story
  return (
    <div className="grid gap-4 text-sm">
      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card-inner p-4">
          <p className="text-sm font-medium text-violet-200 mb-3">Run settings</p>
          <dl className="grid grid-cols-[9rem_1fr] gap-y-1.5">
            <Row label="Strategy">{STRATEGY_LABELS[story.strategy]}</Row>
            <Row label="Model">{story.provider === 'mock' ? 'Demo template (no model)' : `${story.provider} · ${story.model}`}</Row>
            <Row label="Temperature">{sampling.temperature}</Row>
            <Row label="Top-p / Top-k">{sampling.top_p} / {sampling.top_k}</Row>
            <Row label="Max output tokens">{sampling.max_output_tokens}</Row>
            <Row label="LLM calls">{runs.length} ({runs.map((r) => `${r.step}: ${Math.round(r.latency_ms)} ms`).join(', ')})</Row>
          </dl>
        </div>
        <div className="card-inner p-4">
          <p className="text-sm font-medium text-violet-200 mb-3">Intermediate steps</p>
          {Object.keys(artifacts).length === 0 && <p className="text-muted">Direct prompting has no intermediate steps; it is the baseline.</p>}
          {artifacts.interview?.questions.map((q, i) => (
            <p key={i} className="mb-2.5"><span className="text-violet-300">Q:</span> {q.q}<br /><span className="text-sky-300">A:</span> {q.a}</p>
          ))}
          {artifacts.plan && Object.entries(artifacts.plan).map(([k, v]) => (
            <p key={k} className="mb-2.5"><span className="text-violet-300 capitalize">{k}:</span> {v}</p>
          ))}
          {artifacts.branches && (
            <>
              {artifacts.branches.branches.map((b) => {
                const chosen = b.id === artifacts.branches.selected
                return (
                  <div key={b.id} className={`mb-2.5 rounded-lg px-3 py-2 ${chosen ? 'bg-violet-500/15 border border-violet-400/40' : ''}`}>
                    <p className={chosen ? 'text-slate-100' : 'text-slate-400'}><span className="font-semibold">Branch {b.id}{chosen && ' (selected)'}:</span> {b.premise}</p>
                    <p className="text-xs text-muted mt-0.5">Originality {b.scores.originality} · Coherence {b.scores.coherence} · Fit to brief {b.scores.fit_to_brief}</p>
                  </div>
                )
              })}
              <p className="text-xs text-muted">Reason: {artifacts.branches.reason}</p>
            </>
          )}
        </div>
      </div>
      {runs.map((r, i) => (
        <div key={i} className="card-inner p-4">
          <p className="text-sm font-medium text-violet-200 mb-2">Prompt sent: step {i + 1} ({r.step})</p>
          <pre className="text-xs text-slate-300 whitespace-pre-wrap max-h-80 overflow-auto scroll-thin leading-relaxed">{r.prompt}</pre>
        </div>
      ))}
    </div>
  )
}
