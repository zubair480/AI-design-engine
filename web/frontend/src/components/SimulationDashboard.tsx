import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { AgentEvent } from '../hooks/useWebSocket'

interface SimulationDashboardProps {
  events: AgentEvent[]
}

export default function SimulationDashboard({ events }: SimulationDashboardProps) {
  // Extract simulation state from events
  const simState = useMemo(() => {
    let started = false
    let completed = 0
    let total = 0
    let numContainers = 0
    let elapsed = 0
    let done = false
    let meanProfit = 0
    let probLoss = 0

    for (const e of events) {
      if (e.event === 'simulation_started') {
        started = true
        total = e.total_scenarios || 5000
        numContainers = e.num_containers || 100
      }
      if (e.event === 'simulation_progress') {
        completed = e.completed || completed
        total = e.total || total
      }
      if (e.event === 'simulation_complete') {
        done = true
        completed = e.total_scenarios || completed
        elapsed = e.elapsed_seconds || 0
        meanProfit = e.mean_profit || 0
        probLoss = e.prob_loss || 0
      }
    }

    return { started, completed, total, numContainers, elapsed, done, meanProfit, probLoss }
  }, [events])

  if (!simState.started) {
    return null
  }

  const pct = simState.total > 0 ? (simState.completed / simState.total) * 100 : 0

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 card-glow"
    >
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <span className="text-orange-400">🔥</span> Monte Carlo Simulation
      </h2>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <MetricCard
          label="Scenarios"
          value={simState.completed.toLocaleString()}
          subtext={`/ ${simState.total.toLocaleString()}`}
          color="text-cyan-400"
        />
        <MetricCard
          label="Containers"
          value={simState.numContainers.toString()}
          subtext="parallel"
          color="text-orange-400"
        />
        <MetricCard
          label="Elapsed"
          value={simState.done ? `${simState.elapsed}s` : '...'}
          subtext={simState.done ? 'completed' : 'running'}
          color="text-green-400"
        />
        <MetricCard
          label="Speed"
          value={simState.elapsed > 0 ? `${Math.round(simState.completed / simState.elapsed)}/s` : '...'}
          subtext="scenarios/sec"
          color="text-purple-400"
        />
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-400 mb-1">
          <span>Progress</span>
          <span>{pct.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-brand-600 to-cyan-400"
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
      </div>

      {/* Completion banner */}
      {simState.done && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-green-900/30 border border-green-800/50 rounded-lg p-4 text-center"
        >
          <p className="text-green-300 font-medium">
            ✅ {simState.completed.toLocaleString()} simulations completed in {simState.elapsed}s
            across {simState.numContainers} parallel containers
          </p>
        </motion.div>
      )}
    </motion.div>
  )
}

function MetricCard({ label, value, subtext, color }: {
  label: string
  value: string
  subtext: string
  color: string
}) {
  return (
    <div className="bg-gray-800/50 rounded-lg p-3 text-center">
      <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-gray-500">{subtext}</div>
    </div>
  )
}
