import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, LayoutGrid, Rocket, Search, Mountain, Heart, Skull, Coffee, Sparkles, Swords, Clock, Smile, Lightbulb, MessagesSquare, ListTree, GitBranch, Send } from 'lucide-react'
import { api } from '../api'
import { useApp } from '../lib/AppContext'
import { STARTER_IDEAS, STRATEGY_LABELS } from '../lib/options'
import { Badge, Tabs } from '../components/ui'
import { Art, PageHero } from '../components/NightScene'
import NightScene from '../components/NightScene'

const GENRE_TABS = [
  { id: 'All', label: 'All genres', icon: LayoutGrid }, { id: 'Dark Fantasy', label: 'Dark Fantasy', icon: Swords }, { id: 'Fantasy', label: 'Fantasy', icon: Sparkles },
  { id: 'Sci-Fi', label: 'Sci-Fi', icon: Rocket }, { id: 'Mystery', label: 'Mystery', icon: Search },
  { id: 'Adventure', label: 'Adventure', icon: Mountain }, { id: 'Romance', label: 'Romance', icon: Heart },
  { id: 'Horror', label: 'Horror', icon: Skull }, { id: 'Slice of Life', label: 'Slice of Life', icon: Coffee },
  { id: 'Thriller', label: 'Thriller', icon: Clock }, { id: 'Comedy', label: 'Comedy', icon: Smile },
]

const TECHNIQUES = [
  { id: 'direct', icon: Send, text: 'One prompt with every condition. The baseline every other technique is compared against.' },
  { id: 'interview', icon: MessagesSquare, text: 'The model first asks and answers an editor’s questions about your idea, then writes from that Q&A.' },
  { id: 'cot', icon: ListTree, text: 'The model must write an explicit plan (world, characters, arc) before the story itself.' },
  { id: 'tot', icon: GitBranch, text: 'Three plot branches are generated and scored; the best one becomes the story.' },
]

export default function ExplorePage() {
  const [genre, setGenre] = useState('All')
  const [stories, setStories] = useState([])
  const { loadIntoCreate } = useApp()
  const navigate = useNavigate()
  useEffect(() => { api.listStories().then(setStories).catch(() => {}) }, [])

  const ideas = useMemo(() => STARTER_IDEAS.filter((i) => genre === 'All' || i.genre === genre), [genre])
  const featured = ideas[0]
  const yours = stories.filter((s) => genre === 'All' || s.genre === genre).slice(0, 4)
  const use = (idea) => { loadIntoCreate(idea); navigate('/') }

  return (
    <div className="flex flex-col gap-6">
      <PageHero art="hero-explore" title="Explore" hue={255} subtitle="Discover story ideas, learn the prompting techniques, and revisit your own worlds." />
      <Tabs tabs={GENRE_TABS} value={genre} onChange={setGenre} />

      <div className="grid grid-cols-1 xl:grid-cols-[1.6fr_1fr] gap-6 items-start">
        {featured ? (
          <article className="card overflow-hidden relative min-h-80">
            <Art name={featured.art} hue={featured.hue} className="absolute inset-0 h-full w-full" />
            <div className="absolute inset-0 bg-gradient-to-r from-[#0d0a1f] via-[#0d0a1f]/70 to-transparent" />
            <div className="relative p-7 sm:p-9 max-w-lg">
              <Badge><Sparkles size={13} /> Featured idea</Badge>
              <h2 className="mt-4 font-serif !font-bold text-5xl sm:text-6xl text-white leading-none">{featured.title}</h2>
              <p className="mt-3 text-slate-200">{featured.pitch}</p>
              <p className="mt-2 text-sm text-muted">{featured.genre} · Suggested technique: {STRATEGY_LABELS[featured.strategy]}</p>
              <button onClick={() => use(featured)} className="mt-6 btn-primary rounded-full px-5 py-2.5 text-sm font-medium text-white inline-flex items-center gap-2">
                Use this idea <ArrowRight size={16} />
              </button>
            </div>
          </article>
        ) : (
          <div className="card p-10 text-center text-muted">No starter ideas for this genre yet. Try another one, or start from a blank page on Create.</div>
        )}

        <aside className="card p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-white font-medium">From your library</h3>
            <Link to="/library" className="text-sm text-violet-300 hover:underline">See all →</Link>
          </div>
          {yours.length === 0 ? (
            <p className="mt-4 text-sm text-muted">No {genre === 'All' ? '' : `${genre} `}stories yet. Generate one and it will show up here.</p>
          ) : (
            <ul className="mt-4 flex flex-col gap-3">
              {yours.map((s, i) => (
                <li key={s.id}>
                  <Link to={`/library/${s.id}`} className="flex gap-3 rounded-xl p-2 hover:bg-white/5">
                    <div className="relative w-24 shrink-0 aspect-[4/3] overflow-hidden rounded-lg">
                      {s.cover_url ? <img src={s.cover_url} alt="" className="h-full w-full object-cover" /> : <NightScene hue={(s.id * 53) % 360} className="h-full w-full" />}
                      <span className="absolute bottom-1 left-1 grid place-items-center size-5 rounded bg-violet-600 text-[11px] text-white">{i + 1}</span>
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm text-white truncate">{s.title}</p>
                      <p className="text-xs text-muted mt-0.5">{s.genre} · {STRATEGY_LABELS[s.strategy]}</p>
                      <p className="text-xs text-muted mt-1 line-clamp-1">{s.logline}</p>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </aside>
      </div>

      {ideas.length > 1 && (
        <section>
          <h3 className="text-white font-medium">More starter ideas</h3>
          <div className="mt-3 grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {ideas.slice(1).map((idea) => (
              <article key={idea.title} className="card overflow-hidden flex flex-col">
                <Art name={idea.art} hue={idea.hue} castle={false} className="h-36 w-full" />
                <div className="p-4 flex flex-col flex-1">
                  <h4 className="font-serif text-2xl text-white">{idea.title}</h4>
                  <p className="text-xs text-muted">{idea.genre}</p>
                  <p className="mt-2 text-sm text-slate-300 flex-1">{idea.pitch}</p>
                  <button onClick={() => use(idea)} className="mt-4 self-start text-sm text-violet-300 hover:text-violet-200 inline-flex items-center gap-1.5">
                    Use this idea <ArrowRight size={14} />
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      <section>
        <h3 className="flex items-center gap-2 text-white font-medium"><Lightbulb size={18} className="text-amber-300" /> Prompting techniques you can compare</h3>
        <div className="mt-3 grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {TECHNIQUES.map(({ id, icon: Icon, text }) => (
            <div key={id} className="card p-5">
              <Icon className="text-violet-300" size={22} />
              <p className="mt-3 text-white font-medium">{STRATEGY_LABELS[id]}</p>
              <p className="mt-1.5 text-sm text-muted leading-relaxed">{text}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
