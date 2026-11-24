import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api } from '../api'
import { EMPTY_IDEA } from './options'

const AppContext = createContext(null)

const DEFAULT_DRAFT = {
  idea: EMPTY_IDEA,
  plot: { tone: 30, conflict: 80, romance: 45, action: 85, length: 60 },
  sampling: { temperature: 0.9, top_p: 0.95, top_k: 40, max_output_tokens: 4096 },
  strategy: 'direct',
}

export function AppProvider({ children }) {
  const [health, setHealth] = useState(null)
  const [healthError, setHealthError] = useState('')
  const [settings, setSettings] = useState(null)
  const [draft, setDraft] = useState(DEFAULT_DRAFT)
  const [currentStoryId, setCurrentStoryId] = useState(null)

  const refreshHealth = useCallback(() => {
    api.health().then((h) => { setHealth(h); setHealthError('') }).catch((e) => setHealthError(e.message))
  }, [])

  useEffect(() => {
    refreshHealth()
    api.getSettings().then((s) => {
      setSettings(s)
      // Fresh form starts from the saved defaults.
      setDraft((d) => ({
        ...d,
        idea: { ...d.idea, genre: s.default_genre },
        plot: { ...s.plot, tone: s.default_tone },
        sampling: s.sampling,
        strategy: s.strategy,
      }))
    }).catch(() => {})
  }, [refreshHealth])

  /** Load a starter idea or an existing story's inputs into the Create form. */
  const loadIntoCreate = (src) => {
    setDraft({
      idea: { ...EMPTY_IDEA, ...src.idea, genre: src.genre ?? src.idea.genre },
      plot: src.plot ?? draft.plot,
      sampling: src.sampling ?? draft.sampling,
      strategy: src.strategy ?? draft.strategy,
    })
    setCurrentStoryId(null)
  }

  return (
    <AppContext.Provider value={{
      health, healthError, refreshHealth, settings, setSettings,
      draft, setDraft, currentStoryId, setCurrentStoryId, loadIntoCreate,
    }}>
      {children}
    </AppContext.Provider>
  )
}

export const useApp = () => useContext(AppContext)
