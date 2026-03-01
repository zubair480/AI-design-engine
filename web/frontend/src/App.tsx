import { useState, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import PromptInput from './components/PromptInput'
import AgentTimeline from './components/AgentTimeline'
import SimulationDashboard from './components/SimulationDashboard'
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

  const { events, isConnected, lastEvent, connect } = useWebSocket()

  // Poll for results as fallback (in case WebSocket misses the done event)
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
      } catch {}
    }, 5000) // poll every 5 seconds
    return () => clearInterval(interval)
  }, [sessionId, phase])

  // Watch for pipeline completion via WebSocket
  useEffect(() => {
    if (lastEvent?.event === 'done' || lastEvent?.event === 'pipeline_complete') {
      // Fetch full results
      if (sessionId) {
        fetchResults(sessionId)
      }
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
    } catch (err) {
      console.error('Failed to fetch results:', err)
      // Retry after a delay
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
        try {
          const errData = await res.json()
          detail = errData?.detail ? ` - ${errData.detail}` : ''
        } catch {}
        throw new Error(`Server error: ${res.status}${detail}`)
      }

      const data = await res.json()
      setSessionId(data.session_id)

      // Connect WebSocket for real-time updates
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
        try {
          const errData = await res.json()
          detail = errData?.detail ? ` - ${errData.detail}` : ''
        } catch {}
        throw new Error(`Server error: ${res.status}${detail}`)
      }

      // Reconnect WebSocket for follow-up events
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
              key="input"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex items-center justify-center min-h-[60vh]"
            >
              <PromptInput onSubmit={handleSubmit} isLoading={isLoading} />
            </motion.div>
          )}

          {phase === 'running' && (
            <motion.div
              key="running"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              <div className="grid md:grid-cols-2 gap-6">
                <AgentTimeline events={events} />
                <SimulationDashboard events={events} />
              </div>

              {/* Loading indicator */}
              <div className="text-center py-4">
                <div className="inline-flex items-center gap-2 text-gray-400 text-sm">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Pipeline running... Watch the agent activity above.
                </div>
              </div>
            </motion.div>
          )}

          {phase === 'complete' && (
            <motion.div
              key="complete"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              {/* Show timeline summary at top */}
              <div className="grid md:grid-cols-3 gap-6">
                <div className="md:col-span-1">
                  <AgentTimeline events={events} />
                </div>
                <div className="md:col-span-2">
                  <ResultsPanel results={results} onFollowup={handleFollowup} />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800/50 px-6 py-4 mt-auto">
        <div className="max-w-7xl mx-auto text-center text-xs text-gray-600">
          Built with Modal &bull; Qwen 2.5 &bull; Monte Carlo Simulation &bull; Multi-Agent Architecture
        </div>
      </footer>
    </div>
  )
}
