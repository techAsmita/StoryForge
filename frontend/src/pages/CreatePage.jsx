import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, Feather, Drama, AudioLines, Target, Globe, SlidersHorizontal, Sparkles, ArrowRight, Check, LoaderCircle, Wand2 } from 'lucide-react'
import { api } from '../api'
import { useApp } from '../lib/AppContext'
import { useStory } from '../lib/useStory'
import { GENRES, TONES, STRATEGY_LABELS, STRATEGY_STEPS, nearestTone } from '../lib/options'
import { Collapsible, ErrorBanner, Label, Select, Slider } from '../components/ui'
import { Art, PageHero } from '../components/NightScene'
import Workspace from '../components/workspace/Workspace'

function Stepper({ step }) {
  const steps = ['Brief', 'Configure', 'Create', 'Explore']
  return (
    <ol className="mt-6 flex flex-wrap items-center gap-x-3 gap-y-2">
      {steps.map((label, i) => {
        const n = i + 1, done = n < step, active = n === step
        return (
          <li key={label} className="flex items-center gap-3">
            <span className={`grid place-items-center size-8 rounded-full text-sm font-semibold border
              ${active ? 'bg-violet-600 border-violet-400 text-white shadow-[0_0_18px_rgba(139,92,246,.6)]' : done ? 'bg-violet-500/25 border-violet-400/50 text-violet-200' : 'border-white/15 text-slate-400'}`}>
              {done ? <Check size={15} /> : n}
            </span>
            <span className={`text-sm ${active ? 'text-white font-medium' : 'text-slate-400'}`}>{label}</span>
            {n < steps.length && <span className="hidden sm:block w-10 h-px bg-white/15" />}
          </li>
        )
      })}
    </ol>
  )
}

function GeneratingState({ strategy }) {
  const steps = STRATEGY_STEPS[strategy]
  const [i, setI] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setI((x) => Math.min(x + 1, steps.length - 1)), 6000)
    return () => clearInterval(t)
  }, [steps.length])
  return (
    <div className="py-16 px-6 text-center">
      <LoaderCircle size={36} className="mx-auto animate-spin text-violet-300" />
      <p className="mt-4 text-white font-medium">Forging your story with {STRATEGY_LABELS[strategy]}</p>
      <ul className="mt-5 inline-flex flex-col gap-2 text-left text-sm">
        {steps.map((s, n) => (
          <li key={s} className={`flex items-center gap-2 ${n <= i ? 'text-slate-200' : 'text-slate-500'}`}>
            {n < i ? <Check size={15} className="text-emerald-300" /> : n === i ? <LoaderCircle size={15} className="animate-spin text-violet-300" /> : <span className="size-[15px]" />} {s}
          </li>
        ))}
        <li className="flex items-center gap-2 text-slate-500"><span className="size-[15px]" /> Illustrating 4 scenes (continues in the background)</li>
      </ul>
    </div>
  )
}

function EmptyWorkspace() {
  return (
    <div className="flex flex-col gap-5">
      <div className="relative overflow-hidden rounded-2xl aspect-[16/7] min-h-48">
        <Art name="workspace-empty" className="absolute inset-0 h-full w-full" />
        <div className="absolute inset-0 flex items-end bg-gradient-to-t from-black/75 via-black/20 to-transparent">
          <p className="font-serif text-3xl sm:text-4xl text-white px-6 pb-5">Your story will appear here</p>
        </div>
      </div>
      <p className="text-sm text-muted leading-relaxed">
        Describe your idea, pick a genre and tone, then press <span className="text-violet-300">Generate my story</span>.
        You will get a full story, a four-panel storyboard, the characters and the exact prompts that produced them.
        New here? Try a starter idea from <Link to="/explore" className="text-violet-300 hover:underline">Explore</Link>.
      </p>
    </div>
  )
}

export default function CreatePage() {
  const { draft, setDraft, currentStoryId, setCurrentStoryId, refreshHealth } = useApp()
  const { story, setStory } = useStory(currentStoryId)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [strategies, setStrategies] = useState([])
  useEffect(() => { api.strategies().then(setStrategies).catch(() => {}) }, [])

  const { idea, plot, sampling, strategy } = draft
  const setIdea = (k) => (v) => setDraft({ ...draft, idea: { ...idea, [k]: v } })
  const setPlot = (k) => (v) => setDraft({ ...draft, plot: { ...plot, [k]: v } })
  const setSampling = (k) => (v) => setDraft({ ...draft, sampling: { ...sampling, [k]: v } })
  const briefDone = idea.protagonist.trim().length >= 2 && idea.goal.trim().length >= 2
  const step = loading ? 3 : story ? 4 : briefDone ? 2 : 1

  const generate = async () => {
    setLoading(true); setError('')
    try {
      const s = await api.generate(draft)
      setCurrentStoryId(s.id); setStory(s)
      refreshHealth()
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHero art="hero-create" title="Create. Imagine." accent="StoryForge." subtitle="Turn your ideas into immersive stories, complete with visuals.">
        <Stepper step={step} />
      </PageHero>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(360px,440px)_1fr] gap-6 items-start">
        <section className="card p-5 sm:p-6 flex flex-col gap-4 xl:sticky xl:top-6">
          <div className="flex items-center gap-4">
            <Feather size={30} className="text-violet-400" />
            <div>
              <h2 className="text-xl font-semibold text-white">Create your story</h2>
              <p className="text-sm text-muted">Start with an idea. Let your imagination take shape.</p>
            </div>
          </div>

          <div className="card-inner p-4">
            <Label aside={`${idea.protagonist.length}/500`}><span className="flex items-center gap-2"><Sparkles size={16} className="text-violet-300" /> Your story idea</span></Label>
            <textarea className="field" rows={3} maxLength={500} value={idea.protagonist}
              placeholder="A lone exorcist with forgotten powers…" onChange={(e) => setIdea('protagonist')(e.target.value)} />
            <p className="mt-1.5 text-xs text-muted">Describe your main character and their situation.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="card-inner p-4">
              <Label><span className="flex items-center gap-2"><Drama size={16} className="text-violet-300" /> Genre</span></Label>
              <Select value={idea.genre} onChange={setIdea('genre')}>
                {GENRES.map((g) => <option key={g}>{g}</option>)}
              </Select>
            </div>
            <div className="card-inner p-4">
              <Label><span className="flex items-center gap-2"><AudioLines size={16} className="text-violet-300" /> Tone</span></Label>
              <Select value={nearestTone(plot.tone)} onChange={(v) => setPlot('tone')(Number(v))}>
                {TONES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </Select>
            </div>
          </div>

          <div className="card-inner p-4">
            <Label><span className="flex items-center gap-2"><Target size={16} className="text-violet-300" /> Story objective</span></Label>
            <input className="field" maxLength={300} value={idea.goal} placeholder="Uncover the truth behind a shattered world."
              onChange={(e) => setIdea('goal')(e.target.value)} />
          </div>

          <Collapsible icon={Globe} title="World and twist" subtitle="Optional: a rule of the world and an ending twist">
            <div>
              <Label>World rule</Label>
              <textarea className="field" rows={2} maxLength={300} value={idea.world_rule}
                placeholder="Magic exists, but every spell has a deadly price" onChange={(e) => setIdea('world_rule')(e.target.value)} />
            </div>
            <div>
              <Label>Ending twist</Label>
              <textarea className="field" rows={2} maxLength={300} value={idea.ending_twist}
                placeholder="The real villain is the protagonist's future self" onChange={(e) => setIdea('ending_twist')(e.target.value)} />
            </div>
          </Collapsible>

          <Collapsible icon={BookOpen} title="Plot dials" subtitle="Conflict · Romance · Action · Length">
            <Slider label="Conflict level" value={plot.conflict} onChange={setPlot('conflict')} left="Low" right="High" />
            <Slider label="Romance" value={plot.romance} onChange={setPlot('romance')} left="Low" right="High" />
            <Slider label="Action intensity" value={plot.action} onChange={setPlot('action')} left="Low" right="High" />
            <Slider label="Story length" value={plot.length} onChange={setPlot('length')} left="Short" right="Long" />
            <p className="text-xs text-muted">These dials change the prompt (conditional generation), not the model's sampling.</p>
          </Collapsible>

          <Collapsible icon={SlidersHorizontal} title="Advanced generation settings" subtitle="Prompt strategy · Temperature · Top-K · Top-P">
            <div>
              <Label>Prompt strategy</Label>
              <Select value={strategy} onChange={(v) => setDraft({ ...draft, strategy: v })}>
                {strategies.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
              </Select>
              <p className="mt-1.5 text-xs text-muted">{strategies.find((s) => s.id === strategy)?.description}</p>
            </div>
            <Slider label="Temperature" value={sampling.temperature} min={0} max={2} step={0.05} onChange={setSampling('temperature')}
              format={(v) => v.toFixed(2)} left="Focused" right="Creative" />
            <Slider label="Top-K" value={sampling.top_k} min={1} max={100} onChange={setSampling('top_k')}
              hint="Sample only from the K most likely next tokens." />
            <Slider label="Top-P" value={sampling.top_p} min={0.05} max={1} step={0.05} onChange={setSampling('top_p')}
              format={(v) => v.toFixed(2)} hint="Sample from the smallest set of tokens whose probabilities add up to P." />
          </Collapsible>

          <ErrorBanner message={error} onClose={() => setError('')} />
          <button type="button" onClick={generate} disabled={loading || !briefDone}
            className="btn-primary w-full rounded-2xl py-4 text-lg font-semibold text-white flex items-center justify-center gap-3">
            {loading ? <><LoaderCircle className="animate-spin" /> Generating…</> : <><Wand2 size={20} /> Generate my story <ArrowRight size={20} /></>}
          </button>
          {!briefDone && <p className="-mt-2 text-center text-xs text-muted">Add your story idea and objective to continue.</p>}
        </section>

        <section className="card p-5 sm:p-6 min-w-0">
          <div className="flex items-center justify-between mb-5">
            <h2 className="flex items-center gap-3 text-lg font-medium text-white"><BookOpen size={20} className="text-violet-300" /> Your creative workspace</h2>
            {story && <Link to={`/library/${story.id}`} className="text-sm text-violet-300 hover:underline">Open in Library</Link>}
          </div>
          {loading ? <GeneratingState strategy={strategy} />
            : story ? <Workspace story={story} setStory={setStory} onRegenerated={(s) => { setCurrentStoryId(s.id); setStory(s) }} />
              : <EmptyWorkspace />}
        </section>
      </div>
    </div>
  )
}
