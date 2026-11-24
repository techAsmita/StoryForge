import { LayoutGrid, ListOrdered, BookOpen } from 'lucide-react'
import SceneImage from './SceneImage'

export default function StoryTab({ story, onShowScenes }) {
  const { output, scenes } = story
  return (
    <div className="flex flex-col gap-7">
      <section>
        <div className="flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-sm font-medium text-slate-100"><LayoutGrid size={16} className="text-violet-300" /> Storyboard ({scenes.length} panels)</h3>
          <button onClick={onShowScenes} className="text-xs text-violet-300 hover:text-violet-200">View all →</button>
        </div>
        <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {scenes.map((s) => (
            <figure key={s.index} className="relative">
              <SceneImage scene={s} className="aspect-[4/3] w-full" />
              <figcaption className="absolute inset-x-0 bottom-0 rounded-b-xl bg-gradient-to-t from-black/85 to-transparent px-2.5 pb-2 pt-6 text-xs text-white">
                {s.caption}
              </figcaption>
            </figure>
          ))}
        </div>
      </section>

      <section>
        <h3 className="flex items-center gap-2 text-sm font-medium text-slate-100"><ListOrdered size={16} className="text-violet-300" /> Episode beats</h3>
        <ol className="mt-3 grid sm:grid-cols-2 gap-2.5">
          {output.beats.map((b, i) => (
            <li key={i} className="card-inner px-4 py-3 flex gap-3">
              <span className="text-violet-300 text-xs font-semibold tabular-nums pt-0.5">{String(i + 1).padStart(2, '0')}</span>
              <span>
                <span className="block text-sm text-slate-100 font-medium">{b.name}</span>
                <span className="block text-xs text-muted mt-0.5 leading-relaxed">{b.summary}</span>
              </span>
            </li>
          ))}
        </ol>
      </section>

      <section>
        <h3 className="flex items-center gap-2 text-sm font-medium text-slate-100"><BookOpen size={16} className="text-violet-300" /> The story</h3>
        <article className="mt-2 max-w-3xl">
          {output.chapters.map((c, i) => (
            <div key={i} className="mt-6">
              <h4 className="font-serif text-2xl text-violet-100">Chapter {i + 1}: {c.title.replace(/^chapter\s+\w+\s*[:.\-–—]\s*/i, '')}</h4>
              <p className="mt-2 text-[15px] leading-8 text-slate-200 whitespace-pre-line">{c.text}</p>
            </div>
          ))}
        </article>
      </section>
    </div>
  )
}
