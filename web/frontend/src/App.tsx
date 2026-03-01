import { useState, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import Sidebar from './components/Sidebar'
import PromptInput from './components/PromptInput'
import AgentTimeline from './components/AgentTimeline'
import PipelineProgress from './components/PipelineProgress'
import ResultsPanel from './components/ResultsPanel'
import { useWebSocket } from './hooks/useWebSocket'
import { API_BASE } from './config'

type AppPhase = 'input' | 'running' | 'complete'

export default function App() {
  const [phase, setPhase] = useState<AppPhase>('input')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [results, setResults] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [prompt, setPrompt] = useState('')

  const { events, isConnected, lastEvent, connect } = useWebSocket()

  /* ── Poll fallback ── */
  useEffect(() => {
    if (!sessionId || phase !== 'running') return
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/results/${sessionId}`)
        if (res.ok) {
          const data = await res.json()
          setResults(data)
          setPhase('complete')
          setIsLoading(false)
        }
      } catch { }
    }, 5000)
    return () => clearInterval(interval)
  }, [sessionId, phase])

  /* ── WebSocket completion ── */
  useEffect(() => {
    if (lastEvent?.event === 'done' || lastEvent?.event === 'pipeline_complete') {
      if (sessionId) fetchResults(sessionId)
    }
  }, [lastEvent, sessionId])

  const fetchResults = async (sid: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/results/${sid}`)
      if (res.ok) {
        const data = await res.json()
        setResults(data)
        setPhase('complete')
        setIsLoading(false)
      }
    } catch {
      setTimeout(() => fetchResults(sid), 2000)
    }
  }

  const handleSubmit = async (prompt: string) => {
    setIsLoading(true)
    setError(null)
    setResults(null)
    setPhase('running')

    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      })
      if (!res.ok) {
        let detail = ''
        try { const e = await res.json(); detail = e?.detail ? ` — ${e.detail}` : '' } catch { }
        throw new Error(`Server error: ${res.status}${detail}`)
      }
      const data = await res.json()
      setSessionId(data.session_id)
      connect(data.session_id)
    } catch (err: any) {
      setError(err.message)
      setIsLoading(false)
      setPhase('input')
    }
  }

  const handleFollowup = async (prompt: string) => {
    if (!sessionId) return
    setIsLoading(true)
    setPhase('running')
    try {
      const res = await fetch(`${API_BASE}/api/followup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, prompt }),
      })
      if (!res.ok) {
        let detail = ''
        try { const e = await res.json(); detail = e?.detail ? ` — ${e.detail}` : '' } catch { }
        throw new Error(`Server error: ${res.status}${detail}`)
      }
      connect(sessionId)
    } catch (err: any) {
      setError(err.message)
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setPhase('input')
    setSessionId(null)
    setResults(null)
    setIsLoading(false)
    setError(null)
    setPrompt('')
  }

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Top bar */}
      <header className="border-b border-gray-800/50 px-6 py-3">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span className="text-xl">🧠</span>
            <span className="text-white font-semibold text-sm">EstateAgent AI</span>
          </div>
          <div className="flex items-center gap-4">
            {sessionId && (
              <span className="text-xs text-gray-500 font-mono">
                Session: {sessionId}
              </span>
            )}
            {isConnected && (
              <span className="flex items-center gap-1 text-xs text-green-400">
                <span className="w-1.5 h-1.5 bg-green-400 rounded-full pulse-ring" />
                Live
              </span>
            )}
            {phase !== 'input' && (
              <button
                onClick={handleReset}
                className="text-xs text-gray-400 hover:text-white transition-colors"
              >
                ← New Analysis
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-red-900/30 border border-red-800/50 rounded-lg p-4 mb-6 text-red-300 text-sm"
          >
            ⚠️ {error}
          </motion.div>
        )}

        <AnimatePresence mode="wait">
          {phase === 'input' && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-danger/10 border border-danger/25 rounded-2xl px-5 py-4 mb-6 text-danger text-sm font-medium"
            >
              {error}
            </motion.div>
          )}

          <AnimatePresence mode="wait">
            {/* ── Input phase ── */}
            {phase === 'input' && (
              <motion.div
                key="input"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <PromptInput onSubmit={handleSubmit} isLoading={isLoading} prompt={prompt} onPromptChange={setPrompt} />
              </motion.div>
            )}

            {/* ── Running phase ── */}
            {phase === 'running' && (
              <motion.div
                key="running"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-8"
              >
                {/* Animated progress ring with stage tracking */}
                <PipelineProgress events={events} />

                {/* Skeleton placeholders for upcoming results */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 opacity-40">
                  {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
                </div>
              </motion.div>
            )}

            {/* ── Complete phase ── */}
            {phase === 'complete' && (
              <motion.div
                key="complete"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <ResultsPanel results={results} onFollowup={handleFollowup} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* ── Right agent panel ── */}
      <AnimatePresence>
        {phase !== 'input' && (
          <motion.aside
            initial={{ x: 40, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 40, opacity: 0 }}
            transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="w-72 flex-shrink-0 h-screen sticky top-0 border-l border-border/50
                       bg-base-2 overflow-y-auto px-5 py-6"
          >
            <AgentTimeline events={events} />
          </motion.aside>
        )}
      </AnimatePresence>
    </div>
  )
}
