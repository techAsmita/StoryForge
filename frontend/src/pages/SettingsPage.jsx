import { useEffect, useState } from 'react'
import { Settings2, WandSparkles, Cpu, Info, CheckCircle2, Save, BookOpen, Drama, Workflow, Thermometer, Box, Droplet, Hash } from 'lucide-react'
import { api } from '../api'
import { useApp } from '../lib/AppContext'
import { GENRES, TONES, nearestTone } from '../lib/options'
import { Badge, Button, ErrorBanner, Select, Slider, Tabs } from '../components/ui'
import { PageHero } from '../components/NightScene'

const DEFAULTS = {
  default_genre: 'Dark Fantasy', default_tone: 30,
  plot: { tone: 30, conflict: 80, romance: 45, action: 85, length: 60 },
  strategy: 'direct', sampling: { temperature: 0.9, top_p: 0.95, top_k: 40, max_output_tokens: 4096, seed: null },
}

const SYLLABUS = [
  ['Large language models, Transformers', 'Story text comes from a pretrained Transformer LLM (Gemini) via its API.'],
  ['Conditional text generation', 'Genre, tone, world rule, twist and plot dials become explicit conditions in the prompt.'],
  ['Sampling strategies', 'Temperature, Top-K and Top-P are passed to the model; the temperature sweep compares them.'],
  ['Prompt engineering', 'Direct, Interview Pattern, Chain-of-Thought and Tree-of-Thought, with every prompt visible in Prompt Lab.'],
  ['Image generation', 'Each scene prompt is rendered into a storyboard panel by an image model (OpenAI gpt-image or Flux, configurable). The interface art is generated the same way.'],
  ['Multimodal generation', 'The LLM writes scene prompts and a shared character sheet that drive the image model.'],
  ['Evaluation metrics', 'Distinct-n, brief coverage, character presence, length and structure, plus human ratings.'],
]

function Row({ icon: Icon, label, children }) {
  return (
    <div className="grid sm:grid-cols-[12rem_1fr] items-center gap-2 sm:gap-6 py-3 border-b border-white/5 last:border-0">
      <span className="flex items-center gap-3 text-sm text-slate-200"><Icon size={18} className="text-violet-300" /> {label}</span>
      <div>{children}</div>
    </div>
  )
}

export default function SettingsPage() {
  const { settings, setSettings, health, setDraft, draft } = useApp()
  const [tab, setTab] = useState('generation')
  const [form, setForm] = useState(settings ?? DEFAULTS)
  const [strategies, setStrategies] = useState([])
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  useEffect(() => { if (settings) setForm(settings) }, [settings])
  useEffect(() => { api.strategies().then(setStrategies).catch(() => {}) }, [])

  const set = (k) => (v) => setForm({ ...form, [k]: v })
  const setS = (k) => (v) => setForm({ ...form, sampling: { ...form.sampling, [k]: v } })
  const setP = (k) => (v) => setForm({ ...form, plot: { ...form.plot, [k]: v } })

  const save = async () => {
    setError('')
    try {
      const saved = await api.saveSettings(form)
      setSettings(saved)
      // Apply to the Create form too, keeping whatever idea text is already typed.
      setDraft({ ...draft, idea: { ...draft.idea, genre: saved.default_genre }, plot: { ...saved.plot, tone: saved.default_tone }, sampling: saved.sampling, strategy: saved.strategy })
      setStatus('Settings saved. New stories will use these defaults.')
      setTimeout(() => setStatus(''), 4000)
    } catch (e) { setError(e.message) }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHero art="hero-settings" title="Settings" hue={245} subtitle="Defaults for new stories, and the models behind them.">
      </PageHero>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Tabs value={tab} onChange={setTab} tabs={[
          { id: 'generation', label: 'Generation', icon: WandSparkles },
          { id: 'general', label: 'Story defaults', icon: Settings2 },
          { id: 'models', label: 'Models and keys', icon: Cpu },
          { id: 'about', label: 'About', icon: Info },
        ]} />
        <Button variant="ghost" onClick={() => setForm(DEFAULTS)}>Reset to default</Button>
      </div>

      <ErrorBanner message={error} onClose={() => setError('')} />

      {tab === 'generation' && (
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-white">Generation defaults</h2>
          <p className="text-sm text-muted">These directly change what the model produces, so they are saved with every story for comparison.</p>
          <div className="mt-4 grid lg:grid-cols-2 gap-x-10">
            <div>
              <Row icon={Workflow} label="Prompt strategy">
                <Select value={form.strategy} onChange={set('strategy')}>
                  {strategies.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
                </Select>
              </Row>
              <Row icon={Hash} label="Max output tokens">
                <Select value={form.sampling.max_output_tokens} onChange={(v) => setS('max_output_tokens')(Number(v))}>
                  {[2048, 4096, 6144, 8192].map((n) => <option key={n} value={n}>{n.toLocaleString()}</option>)}
                </Select>
              </Row>
            </div>
            <div>
              <Row icon={Thermometer} label="Temperature"><Slider label="" value={form.sampling.temperature} min={0} max={2} step={0.05} onChange={setS('temperature')} format={(v) => v.toFixed(2)} /></Row>
              <Row icon={Box} label="Top-K"><Slider label="" value={form.sampling.top_k} min={1} max={100} onChange={setS('top_k')} /></Row>
              <Row icon={Droplet} label="Top-P"><Slider label="" value={form.sampling.top_p} min={0.05} max={1} step={0.05} onChange={setS('top_p')} format={(v) => v.toFixed(2)} /></Row>
            </div>
          </div>
        </section>
      )}

      {tab === 'general' && (
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-white">Story defaults</h2>
          <p className="text-sm text-muted">Starting values for the Create form.</p>
          <div className="mt-4 grid lg:grid-cols-2 gap-x-10">
            <div>
              <Row icon={BookOpen} label="Default genre">
                <Select value={form.default_genre} onChange={set('default_genre')}>{GENRES.map((g) => <option key={g}>{g}</option>)}</Select>
              </Row>
              <Row icon={Drama} label="Default tone">
                <Select value={nearestTone(form.default_tone)} onChange={(v) => set('default_tone')(Number(v))}>
                  {TONES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </Select>
              </Row>
            </div>
            <div className="flex flex-col gap-4 py-3">
              <Slider label="Conflict level" value={form.plot.conflict} onChange={setP('conflict')} />
              <Slider label="Romance" value={form.plot.romance} onChange={setP('romance')} />
              <Slider label="Action intensity" value={form.plot.action} onChange={setP('action')} />
              <Slider label="Story length" value={form.plot.length} onChange={setP('length')} left="Short" right="Long" />
            </div>
          </div>
        </section>
      )}

      {tab === 'models' && (
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-white">Models and keys</h2>
          <p className="text-sm text-muted">Keys live only in <code className="text-violet-300">backend/.env</code> and are never sent to the browser.</p>
          {health && (
            <div className="mt-4 grid lg:grid-cols-2 gap-4">
              <div className="card-inner p-5">
                <div className="flex items-center justify-between"><p className="text-white font-medium">Text model</p>
                  <Badge tone={health.mode === 'live' ? 'green' : 'amber'}>{health.mode === 'live' ? 'Live' : 'Demo mode'}</Badge></div>
                <p className="mt-2 text-sm text-slate-300">{health.mode === 'live' ? `Gemini · ${health.model}` : 'Template text, no API calls.'}</p>
                <p className="mt-2 text-xs text-muted leading-relaxed">
                  Live mode turns on automatically when <code>GEMINI_API_KEY</code> is set in backend/.env (restart uvicorn after editing it).
                  Get a free key at aistudio.google.com.
                </p>
              </div>
              <div className="card-inner p-5">
                <div className="flex items-center justify-between"><p className="text-white font-medium">Image model</p>
                  <Badge tone={health.image_provider === 'placeholder' ? 'amber' : health.image_key || health.image_provider === 'pollinations' ? 'green' : 'rose'}>
                    {health.image_provider === 'placeholder' ? 'Placeholders' : health.image_provider === 'openai' && !health.image_key ? 'Key missing' : 'Live'}
                  </Badge></div>
                <p className="mt-2 text-sm text-slate-300">
                  {health.image_provider === 'openai'
                    ? `OpenAI · ${health.image_model} · panels about ${Math.round(health.image_interval_s)} s apart`
                    : health.image_provider === 'pollinations'
                      ? `Pollinations (Flux) · ${health.image_key ? 'API key set, no wait between panels' : `free tier, one panel every ~${Math.round(health.image_interval_s)} s`}`
                      : 'Offline placeholder cards.'}
                </p>
                <p className="mt-2 text-xs text-muted leading-relaxed">
                  Switch with <code>IMAGE_PROVIDER</code> in backend/.env: <code>openai</code> (needs <code>OPENAI_API_KEY</code>, paid per image) or <code>pollinations</code> (free Flux; a secret key from enter.pollinations.ai removes the wait).
                </p>
              </div>
            </div>
          )}
        </section>
      )}

      {tab === 'about' && (
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-white">About StoryForge</h2>
          <p className="text-sm text-muted">UCS748 Generative AI course project. How each part of the syllabus appears in the app:</p>
          <div className="mt-4 card-inner overflow-hidden">
            <table className="w-full text-sm">
              <tbody>
                {SYLLABUS.map(([topic, how]) => (
                  <tr key={topic} className="border-b border-white/5 last:border-0">
                    <td className="px-4 py-3 text-slate-100 align-top w-64">{topic}</td>
                    <td className="px-4 py-3 text-slate-300">{how}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {(tab === 'generation' || tab === 'general') && (
        <div className="flex flex-wrap items-center justify-end gap-4">
          <span className="text-sm text-emerald-300 flex items-center gap-2">{status && <><CheckCircle2 size={17} /> {status}</>}</span>
          <Button variant="primary" onClick={save}><Save size={16} /> Save changes</Button>
        </div>
      )}
    </div>
  )
}
