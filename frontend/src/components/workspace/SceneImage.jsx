import { useState } from 'react'
import { ImageOff, LoaderCircle } from 'lucide-react'

/** One storyboard image with its render state (images are rendered in the background). */
export default function SceneImage({ scene, className = '', label = true }) {
  const [broken, setBroken] = useState(false)
  if (!scene) return <div className={`shimmer rounded-xl ${className}`} />
  if (scene.status === 'ready' && !broken) {
    return <img src={scene.image_url} alt={scene.caption} loading="lazy" onError={() => setBroken(true)}
      className={`object-cover rounded-xl ${className}`} />
  }
  const failed = scene.status === 'failed' || broken
  return (
    <div className={`${failed ? 'bg-white/5' : 'shimmer'} rounded-xl grid place-items-center text-center ${className}`}>
      {label && (
        <div className="px-3 text-xs text-slate-300">
          {failed ? <ImageOff className="mx-auto mb-1.5 text-rose-300" size={20} /> : <LoaderCircle className="mx-auto mb-1.5 animate-spin text-violet-300" size={20} />}
          {failed ? 'Image failed' : scene.status === 'rendering' ? 'Illustrating…' : 'Queued'}
        </div>
      )}
    </div>
  )
}
