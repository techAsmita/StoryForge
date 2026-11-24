import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useStory } from '../lib/useStory'
import { ErrorBanner } from '../components/ui'
import Workspace from '../components/workspace/Workspace'

export default function StoryPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { story, setStory, error } = useStory(Number(id))

  return (
    <div className="flex flex-col gap-5">
      <Link to="/library" className="inline-flex items-center gap-2 text-sm text-violet-300 hover:text-violet-200"><ArrowLeft size={16} /> Back to Library</Link>
      <ErrorBanner message={error} />
      <section className="card p-5 sm:p-7">
        {story
          ? <Workspace story={story} setStory={setStory} onRegenerated={(s) => navigate(`/library/${s.id}`)} />
          : !error && <div className="shimmer rounded-2xl h-96" />}
      </section>
    </div>
  )
}
