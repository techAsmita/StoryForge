import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search, Heart, CalendarDays, Images, Sparkles, Plus } from 'lucide-react'
import { api } from '../api'
import { STRATEGY_LABELS } from '../lib/options'
import { Badge, ErrorBanner, Select, Tabs } from '../components/ui'
import { PageHero } from '../components/NightScene'
import NightScene from '../components/NightScene'

const STATUS = {
  ready: ['green', 'Completed'],
  rendering: ['amber', 'Illustrating'],
  failed: ['rose', 'Images failed'],
}

function StoryCard({ s, onFavorite }) {
  const [tone, label] = STATUS[s.image_status]
  return (
    <article className="card overflow-hidden group relative">
      <Link to={`/library/${s.id}`} className="block">
        <div className="relative aspect-[16/10] overflow-hidden">
          {s.cover_url
            ? <img src={s.cover_url} alt="" className="h-full w-full object-cover transition duration-500 group-hover:scale-105" />
            : <NightScene hue={(s.id * 53) % 360} className="h-full w-full" />}
          <div className="absolute inset-0 bg-gradient-to-t from-[#140f2e] via-transparent to-transparent" />
          <span className="absolute top-3 right-3"><Badge tone={tone}>{label}</Badge></span>
        </div>
        <div className="p-5 pt-3">
          <h3 className="font-serif text-2xl text-white leading-tight line-clamp-1">{s.title}</h3>
          <p className="text-xs text-muted mt-1">{s.genre} · {STRATEGY_LABELS[s.strategy]}{s.provider === 'mock' && ' · Demo'}</p>
          <p className="text-sm text-slate-300 mt-2 line-clamp-2 min-h-10">{s.logline}</p>
          <div className="mt-4 flex items-center gap-4 text-xs text-muted">
            <span className="flex items-center gap-1.5"><CalendarDays size={14} /> {new Date(s.created_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}</span>
            <span className="flex items-center gap-1.5"><Images size={14} /> {s.scenes_ready}/{s.scenes_total} images</span>
            <span>Temp. {s.temperature}</span>
          </div>
        </div>
      </Link>
      <button onClick={() => onFavorite(s)} aria-label={s.favorite ? 'Remove from favorites' : 'Add to favorites'}
        className="absolute top-3 left-3 grid place-items-center size-9 rounded-full bg-black/45 backdrop-blur hover:bg-black/60">
        <Heart size={17} className={s.favorite ? 'fill-rose-400 text-rose-400' : 'text-white'} />
      </button>
    </article>
  )
}

export default function LibraryPage() {
  const [stories, setStories] = useState(null)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('all')
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState('newest')

  useEffect(() => {
    const load = () => api.listStories().then(setStories).catch((e) => setError(e.message))
    load()
    const t = setInterval(load, 8000) // picks up images that finish rendering
    return () => clearInterval(t)
  }, [])

  const toggleFavorite = async (s) => {
    setStories((all) => all.map((x) => (x.id === s.id ? { ...x, favorite: !x.favorite } : x)))
    try { await api.updateStory(s.id, { favorite: !s.favorite }) } catch (e) { setError(e.message) }
  }

  const list = useMemo(() => {
    let l = stories ?? []
    if (filter === 'favorites') l = l.filter((s) => s.favorite)
    if (filter === 'live') l = l.filter((s) => s.provider !== 'mock')
    if (query.trim()) {
      const q = query.toLowerCase()
      l = l.filter((s) => `${s.title} ${s.genre} ${s.logline}`.toLowerCase().includes(q))
    }
    const by = { newest: (a, b) => b.created_at.localeCompare(a.created_at), oldest: (a, b) => a.created_at.localeCompare(b.created_at), title: (a, b) => a.title.localeCompare(b.title) }
    return [...l].sort(by[sort])
  }, [stories, filter, query, sort])

  const all = stories ?? []
  return (
    <div className="flex flex-col gap-6">
      <PageHero art="hero-library" title="Your stories" accent="Library" hue={275}
        subtitle="Revisit, compare and manage every story you have generated, with its scenes, prompts and evaluation." />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Tabs value={filter} onChange={setFilter} tabs={[
          { id: 'all', label: 'All stories', count: all.length },
          { id: 'favorites', label: 'Favorites', count: all.filter((s) => s.favorite).length },
          { id: 'live', label: 'Live generations', count: all.filter((s) => s.provider !== 'mock').length },
        ]} />
        <div className="flex gap-3 w-full sm:w-auto">
          <label className="relative flex-1 sm:w-72">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
            <input className="field !pl-10 !rounded-full" placeholder="Search your stories…" value={query} onChange={(e) => setQuery(e.target.value)} />
          </label>
          <Select value={sort} onChange={setSort} className="w-44 [&_select]:!rounded-full" aria-label="Sort stories">
            <option value="newest">Sort by: Newest</option>
            <option value="oldest">Sort by: Oldest</option>
            <option value="title">Sort by: Title</option>
          </Select>
        </div>
      </div>

      <ErrorBanner message={error} onClose={() => setError('')} />
      {stories === null ? (
        <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">{[0, 1, 2].map((i) => <div key={i} className="shimmer rounded-2xl h-80" />)}</div>
      ) : list.length === 0 ? (
        <div className="card p-12 text-center">
          <Sparkles className="mx-auto text-violet-300" />
          <p className="mt-3 text-white">{all.length ? 'No stories match this view.' : 'No stories yet.'}</p>
          <Link to="/" className="mt-4 inline-flex items-center gap-2 btn-primary rounded-full px-5 py-2.5 text-sm text-white"><Plus size={16} /> Create a story</Link>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
          {list.map((s) => <StoryCard key={s.id} s={s} onFavorite={toggleFavorite} />)}
        </div>
      )}
    </div>
  )
}
