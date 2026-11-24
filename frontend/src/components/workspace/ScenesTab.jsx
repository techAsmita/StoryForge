import { useState } from 'react'
import { RefreshCw, Users } from 'lucide-react'
import { api } from '../../api'
import { useApp } from '../../lib/AppContext'
import { Button } from '../ui'
import SceneImage from './SceneImage'
import RelationshipMap from './RelationshipMap'

export default function ScenesTab({ story, setStory }) {
  const { health } = useApp()
  const [retrying, setRetrying] = useState(false)
  const failed = story.scenes.some((s) => s.status === 'failed')
  const waiting = story.scenes.some((s) => s.status === 'pending' || s.status === 'rendering')

  const retry = async () => {
    setRetrying(true)
    try { setStory(await api.retryImages(story.id)) } finally { setRetrying(false) }
  }

  return (
    <div className="flex flex-col gap-7">
      {(waiting || failed) && (
        <div className="card-inner px-4 py-3 text-sm text-slate-300 flex flex-wrap items-center justify-between gap-3">
          <span>
            {waiting
              ? health?.image_interval_s
                ? `Panels are rendered one at a time (about ${Math.round(health.image_interval_s)} s apart on the free image tier). You can keep working; they appear automatically.`
                : 'Panels are being illustrated. They appear automatically.'
              : 'Some panels could not be illustrated.'}
          </span>
          {failed && <Button onClick={retry} loading={retrying}><RefreshCw size={15} /> Retry images</Button>}
        </div>
      )}

      <div className="grid sm:grid-cols-2 gap-5">
        {story.scenes.map((s) => (
          <figure key={s.index} className="card-inner overflow-hidden">
            <SceneImage scene={s} className="aspect-square w-full !rounded-none" />
            <figcaption className="p-4">
              <p className="text-sm text-slate-100"><span className="text-violet-300 mr-2">Panel {s.index}</span>{s.caption}</p>
              {s.error && s.status === 'failed' && <p className="mt-1 text-xs text-rose-300">{s.error}</p>}
              <details className="mt-2 text-xs text-muted">
                <summary className="cursor-pointer text-violet-300/90">Image prompt sent to the model</summary>
                <p className="mt-2 leading-relaxed">{s.image_prompt}</p>
              </details>
            </figcaption>
          </figure>
        ))}
      </div>

      <section>
        <h3 className="flex items-center gap-2 text-sm font-medium text-slate-100"><Users size={16} className="text-violet-300" /> Characters</h3>
        <div className="mt-3 grid lg:grid-cols-[1fr_1.1fr] gap-5 items-center">
          <ul className="flex flex-col gap-2.5">
            {story.output.characters.map((c) => (
              <li key={c.name} className="card-inner px-4 py-3">
                <p className="text-sm text-slate-100">{c.name} <span className="text-xs text-muted capitalize">· {c.role}</span></p>
                <p className="text-xs text-muted mt-0.5">{c.visual_description}</p>
              </li>
            ))}
          </ul>
          <RelationshipMap characters={story.output.characters} relationships={story.output.relationships} />
        </div>
        <p className="mt-3 text-xs text-muted">The same character descriptions are added to every panel's image prompt, which keeps characters consistent across images.</p>
      </section>
    </div>
  )
}
