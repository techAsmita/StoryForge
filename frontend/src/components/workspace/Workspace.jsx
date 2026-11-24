import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BookOpen, Images, FlaskConical, BarChart3, Heart, Pencil, RefreshCw, Trash2 } from 'lucide-react'
import { api } from '../../api'
import { useApp } from '../../lib/AppContext'
import { STRATEGY_LABELS } from '../../lib/options'
import { Badge, Button, ErrorBanner, Tabs } from '../ui'
import SceneImage from './SceneImage'
import StoryTab from './StoryTab'
import ScenesTab from './ScenesTab'
import PromptLabTab from './PromptLabTab'
import EvaluationTab from './EvaluationTab'

const TABS = [
  { id: 'story', label: 'Story', icon: BookOpen },
  { id: 'scenes', label: 'Scenes', icon: Images },
  { id: 'lab', label: 'Prompt Lab', icon: FlaskConical },
  { id: 'evaluation', label: 'Evaluation', icon: BarChart3 },
]

/** Full view of one generated story; used on the Create page and when opening a story from the Library. */
export default function Workspace({ story, setStory, onRegenerated }) {
  const [tab, setTab] = useState('story')
  const [busy, setBusy] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [error, setError] = useState('')
  const { loadIntoCreate, setCurrentStoryId } = useApp()
  const navigate = useNavigate()
  const ready = story.scenes.filter((s) => s.status === 'ready').length

  const act = async (name, fn) => {
    setBusy(name); setError('')
    try { await fn() } catch (e) { setError(e.message) } finally { setBusy('') }
  }
  const toggleFavorite = () => act('fav', async () => setStory(await api.updateStory(story.id, { favorite: !story.favorite })))
  const regenerate = () => act('regen', async () => {
    const s = await api.generate({ idea: story.idea, plot: story.plot, sampling: story.sampling, strategy: story.strategy })
    onRegenerated?.(s)
  })
  const edit = () => { loadIntoCreate(story); navigate('/') }
  const remove = () => act('delete', async () => {
    await api.deleteStory(story.id)
    setCurrentStoryId(null)
    navigate('/library')
  })

  return (
    <div className="flex flex-col gap-5">
      <div className="relative">
        <SceneImage scene={story.scenes[0]} className="w-full aspect-[16/7] min-h-48" />
        {ready < story.scenes.length && (
          <span className="absolute top-3 left-3"><Badge tone="amber">Illustrating {ready} of {story.scenes.length} panels</Badge></span>
        )}
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="font-serif text-4xl text-white leading-tight">{story.title}</h2>
          <p className="mt-1 text-sm text-muted">
            {story.genre} · {STRATEGY_LABELS[story.strategy]} · {new Date(story.created_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}
            {story.provider === 'mock' && <> · <span className="text-amber-300">Demo output</span></>}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={toggleFavorite} loading={busy === 'fav'} aria-pressed={story.favorite}>
            <Heart size={15} className={story.favorite ? 'fill-rose-400 text-rose-400' : ''} /> {story.favorite ? 'Favorited' : 'Favorite'}
          </Button>
          <Button onClick={edit}><Pencil size={15} /> Edit inputs</Button>
          <Button onClick={regenerate} loading={busy === 'regen'}><RefreshCw size={15} /> Regenerate</Button>
          {confirmDelete
            ? <Button variant="danger" onClick={remove} loading={busy === 'delete'}>Confirm delete</Button>
            : <Button variant="danger" onClick={() => setConfirmDelete(true)} aria-label="Delete story"><Trash2 size={15} /></Button>}
        </div>
      </div>
      <p className="text-slate-300 leading-relaxed italic">{story.output.logline}</p>
      <ErrorBanner message={error} onClose={() => setError('')} />

      <Tabs tabs={TABS} value={tab} onChange={setTab} />
      <div>
        {tab === 'story' && <StoryTab story={story} onShowScenes={() => setTab('scenes')} />}
        {tab === 'scenes' && <ScenesTab story={story} setStory={setStory} />}
        {tab === 'lab' && <PromptLabTab story={story} />}
        {tab === 'evaluation' && <EvaluationTab story={story} setStory={setStory} />}
      </div>
    </div>
  )
}
