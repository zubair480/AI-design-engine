import { motion, AnimatePresence } from 'framer-motion'
import { AgentEvent } from '../hooks/useWebSocket'

interface AgentTimelineProps {
  events: AgentEvent[]
}

const EVENT_CONFIG: Record<string, { label: string; color: string; bg: string; glow: boolean }> = {
  pipeline_started: { label: 'Pipeline Started', color: 'text-teal-bright', bg: 'bg-teal', glow: true },
  plan_complete: { label: 'Plan Generated', color: 'text-sage', bg: 'bg-sage', glow: true },
  analyst_started: { label: 'Analyst Running', color: 'text-warning', bg: 'bg-warning', glow: true },
  analyst_complete: { label: 'Analyst Complete', color: 'text-teal-bright', bg: 'bg-teal', glow: true },
  conclusion_started: { label: 'Conclusion Generating', color: 'text-sage', bg: 'bg-sage', glow: true },
  conclusion_complete: { label: 'Conclusion Ready', color: 'text-teal-bright', bg: 'bg-teal', glow: true },
  pipeline_complete: { label: 'Pipeline Complete', color: 'text-teal-bright', bg: 'bg-teal', glow: true },
  status_update: { label: 'Status Update', color: 'text-muted/60', bg: 'bg-muted/30', glow: false },
  followup_started: { label: 'Follow-up Started', color: 'text-teal-bright', bg: 'bg-teal', glow: true },
  followup_complete: { label: 'Follow-up Complete', color: 'text-teal-bright', bg: 'bg-teal', glow: true },
  done: { label: 'Done', color: 'text-teal-bright', bg: 'bg-teal', glow: true },
}

function getEventDescription(event: AgentEvent): string {
  switch (event.event) {
    case 'pipeline_started':
      return `Analyzing: "${(event.prompt || '').slice(0, 50)}…"`
    case 'plan_complete':
      return `${event.num_regions || 0} regions: ${(event.regions || []).join(', ').slice(0, 60)}${(event.regions || []).join(', ').length > 60 ? '…' : ''}`
    case 'analyst_started':
      return `Analyzing ${event.region || 'region'}…`
    case 'analyst_complete':
      return `${event.region || '?'} — score ${event.score || '?'}/100`
    case 'conclusion_started':
      return 'Synthesizing final advisory…'
    case 'conclusion_complete':
      return `${(event.recommendation || '').replace(/_/g, ' ')} → ${event.recommended_region || ''}`
    case 'pipeline_complete':
      return `${event.elapsed_seconds}s total`
    case 'status_update':
      return event.message || ''
    default:
      return ''
  }
}

export default function AgentTimeline({ events }: AgentTimelineProps) {
  const meaningful = events.filter(e => e.event !== 'status_update')
  const isRunning = meaningful.length > 0 && !meaningful.some(e => e.event === 'pipeline_complete' || e.event === 'done')

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-xs font-bold text-ink uppercase tracking-wide">Agent Activity</h3>
        {isRunning && (
          <motion.span
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-2 text-[11px] text-teal-bright font-bold bg-teal/10 border border-teal/20 px-2.5 py-1 rounded-lg"
          >
            <span className="w-2 h-2 rounded-full bg-teal-bright animate-pulse-dot" />
            LIVE
          </motion.span>
        )}
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto space-y-0 pr-1 -mr-1">
        <AnimatePresence>
          {meaningful.map((event, idx) => {
            const config = EVENT_CONFIG[event.event] || { label: event.event, color: 'text-muted', bg: 'bg-muted/30', glow: false }
            const desc = getEventDescription(event)
            const isComplete = event.event.includes('complete') || event.event === 'done'

            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -12, scale: 0.95 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                transition={{ duration: 0.35, delay: 0.05, ease: [0.25, 0.46, 0.45, 0.94] }}
                className="flex items-start gap-3.5 py-3 group relative"
              >
                {/* Dot + connecting line */}
                <div className="flex flex-col items-center pt-1 flex-shrink-0 relative">
                  <div className={`relative`}>
                    <div className={`w-2.5 h-2.5 rounded-full ${config.bg} transition-all duration-300`} />
                    {config.glow && (
                      <div className={`absolute inset-0 w-2.5 h-2.5 rounded-full ${config.bg} animate-pulse-dot opacity-40`} />
                    )}
                  </div>
                  {idx < meaningful.length - 1 && (
                    <div className="w-px flex-1 bg-border/60 mt-1 min-h-[16px]" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 -mt-0.5">
                  <div className="flex items-center gap-2">
                    <p className={`text-xs font-bold ${config.color} leading-tight`}>
                      {config.label}
                    </p>
                    {isComplete && (
                      <span className="text-[9px] text-teal bg-teal/10 px-1.5 py-0.5 rounded font-bold">✓</span>
                    )}
                  </div>
                  {desc && (
                    <p className="text-[11px] text-muted/70 mt-1 truncate leading-snug">
                      {desc}
                    </p>
                  )}
                </div>

                {/* Timestamp */}
                {event.timestamp && (
                  <span className="text-[9px] text-muted/30 flex-shrink-0 pt-0.5 font-mono">
                    {new Date(event.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </span>
                )}
              </motion.div>
            )
          })}
        </AnimatePresence>

        {meaningful.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <motion.div
              animate={{ opacity: [0.3, 0.6, 0.3] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="w-12 h-12 rounded-xl bg-surface-2 border border-border flex items-center justify-center mb-4"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8B8B9E" strokeWidth="1.5" strokeLinecap="round">
                <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
              </svg>
            </motion.div>
            <p className="text-xs text-muted/40 font-medium">Waiting for activity…</p>
            <p className="text-[10px] text-muted/25 mt-1">Start an analysis to see agent events</p>
          </div>
        )}
      </div>

      {/* Event count */}
      {meaningful.length > 0 && (
        <div className="pt-3 border-t border-border/50 mt-2">
          <p className="text-[10px] text-muted/40 text-center font-mono">
            {meaningful.length} events
          </p>
        </div>
      )}
    </div>
  )
}
