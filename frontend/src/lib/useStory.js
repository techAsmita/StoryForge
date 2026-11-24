import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'

const busy = (story) => story?.scenes?.some((s) => s.status === 'pending' || s.status === 'rendering')

/** Loads a story and keeps polling while its images are still being rendered. */
export function useStory(id) {
  const [story, setStory] = useState(null)
  const [error, setError] = useState('')

  const reload = useCallback(() => {
    if (!id) return Promise.resolve()
    return api.getStory(id).then(setStory).catch((e) => setError(e.message))
  }, [id])

  useEffect(() => { setStory(null); setError(''); reload() }, [reload])

  useEffect(() => {
    if (!busy(story)) return
    const t = setInterval(reload, 4000)
    return () => clearInterval(t)
  }, [story, reload])

  return { story, setStory, error, reload }
}
