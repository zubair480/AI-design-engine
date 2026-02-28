import { motion, AnimatePresence } from 'framer-motion'
import { AgentEvent } from '../hooks/useWebSocket'

interface AgentTimelineProps {
  events: AgentEvent[]
}

const EVENT_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  pipeline_started: { icon: '🚀', color: 'text-blue-400', label: 'Pipeline Started' },
  plan_complete: { icon: '📋', color: 'text-purple-400', label: 'Plan Generated' },
  research_started: { icon: '🔬', color: 'text-yellow-400', label: 'Research Started' },
  research_complete: { icon: '✅', color: 'text-green-400', label: 'Research Complete' },
  simulation_started: { icon: '⚡', color: 'text-orange-400', label: 'Simulation Started' },
  simulation_progress: { icon: '📊', color: 'text-cyan-400', label: 'Simulation Progress' },
  simulation_complete: { icon: '🎯', color: 'text-green-400', label: 'Simulation Complete' },
  evaluation_started: { icon: '🧠', color: 'text-indigo-400', label: 'Evaluation Started' },
  evaluation_complete: { icon: '📈', color: 'text-emerald-400', label: 'Evaluation Complete' },
  pipeline_complete: { icon: '🏆', color: 'text-yellow-300', label: 'Pipeline Complete' },
  status_update: { icon: '📡', color: 'text-gray-400', label: 'Status Update' },
  sandbox_execution: { icon: '🔒', color: 'text-red-400', label: 'Sandbox Execution' },
  code_generated: { icon: '💻', color: 'text-pink-400', label: 'Code Generated' },
  followup_started: { icon: '🔄', color: 'text-blue-400', label: 'Follow-up Started' },
  followup_complete: { icon: '✅', color: 'text-green-400', label: 'Follow-up Complete' },
  done: { icon: '🏁', color: 'text-green-300', label: 'Done' },
}

function getEventDescription(event: AgentEvent): string {
  switch (event.event) {
    case 'pipeline_started':
      return `Analyzing: "${event.prompt?.slice(0, 60)}..."`
    case 'plan_complete':
      return `Created ${event.num_tasks} tasks in ${event.num_waves} execution waves`
    case 'research_started':
      return `Running: ${event.subtask_id?.replace(/_/g, ' ')}`
    case 'research_complete':
      return `Completed: ${event.subtask_id?.replace(/_/g, ' ')}`
    case 'simulation_started':
      return `Launching ${event.num_containers} containers × ${event.batch_size} scenarios = ${event.total_scenarios?.toLocaleString()} total`
    case 'simulation_progress':
      return `${event.completed?.toLocaleString()} / ${event.total?.toLocaleString()} scenarios (${event.pct}%)`
    case 'simulation_complete':
      return `${event.total_scenarios?.toLocaleString()} scenarios in ${event.elapsed_seconds}s — Mean profit: $${(event.mean_profit || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
    case 'evaluation_complete':
      return `Recommendation: ${event.recommendation} — ROI: ${event.roi_pct?.toFixed(1)}% — Loss probability: ${event.prob_loss?.toFixed(1)}%`
    case 'pipeline_complete':
      return `Total pipeline time: ${event.elapsed_seconds}s`
    case 'status_update':
      return event.message || ''
    default:
      return JSON.stringify(event).slice(0, 100)
  }
}

export default function AgentTimeline({ events }: AgentTimelineProps) {
  // Filter out status_update noise — keep only meaningful events
  const meaningfulEvents = events.filter(e => e.event !== 'status_update')

  return (
    <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 card-glow">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <span className="text-brand-400">⚡</span> Agent Activity
      </h2>

      <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
        <AnimatePresence>
          {meaningfulEvents.map((event, idx) => {
            const config = EVENT_CONFIG[event.event] || { icon: '📌', color: 'text-gray-400', label: event.event }
            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -20, height: 0 }}
                animate={{ opacity: 1, x: 0, height: 'auto' }}
                transition={{ duration: 0.3 }}
                className="flex items-start gap-3 py-2 border-b border-gray-800/50 last:border-0"
              >
                {/* Timeline dot */}
                <div className="flex-shrink-0 mt-1">
                  <span className="text-lg">{config.icon}</span>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium ${config.color}`}>
                      {config.label}
                    </span>
                    {event.timestamp && (
                      <span className="text-xs text-gray-600">
                        {new Date(event.timestamp * 1000).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-400 truncate">
                    {getEventDescription(event)}
                  </p>
                </div>

                {/* Active indicator for in-progress events */}
                {(event.event === 'simulation_started' || event.event === 'research_started') && (
                  <div className="flex-shrink-0">
                    <div className="w-2 h-2 bg-green-400 rounded-full pulse-ring" />
                  </div>
                )}
              </motion.div>
            )
          })}
        </AnimatePresence>

        {meaningfulEvents.length === 0 && (
          <div className="text-center text-gray-600 py-8">
            Waiting for agent activity...
          </div>
        )}
      </div>
    </div>
  )
}
