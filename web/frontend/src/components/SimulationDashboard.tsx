import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { AgentEvent } from '../hooks/useWebSocket'
import { FadeIn, GlassCard } from './ui'

interface SimulationDashboardProps {
  events: AgentEvent[]
}

export default function SimulationDashboard({ events }: SimulationDashboardProps) {
  const sim = useMemo(() => {
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

  if (!sim.started) return null

  const pct = sim.total > 0 ? (sim.completed / sim.total) * 100 : 0

  return (
    <FadeIn>
      <GlassCard className="space-y-6">
        {/* Heading */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg gradient-accent flex items-center justify-center shadow-glow-teal">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
                <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
              </svg>
            </div>
            <h3 className="text-base font-bold text-ink tracking-title">Monte Carlo Simulation</h3>
          </div>
          {sim.done ? (
            <motion.span
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="text-[11px] font-bold text-teal-bright bg-teal/15 border border-teal/25 px-3 py-1 rounded-lg"
            >
              ✓ Complete
            </motion.span>
          ) : (
            <span className="flex items-center gap-2 text-[11px] text-warning font-bold bg-warning/10 border border-warning/20 px-3 py-1 rounded-lg">
              <span className="w-2 h-2 rounded-full bg-warning animate-pulse-dot" />
              Running
            </span>
          )}
        </div>

        {/* Metrics row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <MiniMetric
            label="Scenarios"
            value={sim.completed.toLocaleString()}
            sub={`/ ${sim.total.toLocaleString()}`}
            highlight={sim.done}
          />
          <MiniMetric
            label="Containers"
            value={sim.numContainers.toString()}
            sub="parallel"
            highlight={false}
          />
          <MiniMetric
            label="Elapsed"
            value={sim.done ? `${sim.elapsed}s` : '…'}
            sub={sim.done ? 'completed' : 'running'}
            highlight={sim.done}
          />
          <MiniMetric
            label="Throughput"
            value={sim.elapsed > 0 ? `${Math.round(sim.completed / sim.elapsed)}/s` : '…'}
            sub="scenarios/sec"
            highlight={sim.elapsed > 0}
          />
        </div>

        {/* Progress bar */}
        <div>
          <div className="flex justify-between text-xs text-muted mb-2">
            <span className="font-medium">Progress</span>
            <span className="font-bold text-ink">{pct.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-surface-2 rounded-full h-3 overflow-hidden border border-border/50">
            <motion.div
              className="h-full rounded-full gradient-accent relative"
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            >
              {!sim.done && (
                <div className="absolute inset-0 rounded-full progress-glow" />
              )}
            </motion.div>
          </div>
        </div>

        {/* Completion banner */}
        {sim.done && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="bg-teal/8 border border-teal/20 rounded-xl p-5 text-center"
          >
            <p className="text-sm text-teal-bright font-semibold">
              🎯 {sim.completed.toLocaleString()} simulations completed in <span className="font-bold">{sim.elapsed}s</span> across {sim.numContainers} containers
            </p>
          </motion.div>
        )}
      </GlassCard>
    </FadeIn>
  )
}

function MiniMetric({ label, value, sub, highlight }: { label: string; value: string; sub: string; highlight: boolean }) {
  return (
    <motion.div
      className={`rounded-xl p-3.5 text-center border transition-all duration-300 ${highlight ? 'bg-teal/8 border-teal/20' : 'bg-surface-2 border-border/50'
        }`}
      whileHover={{ scale: 1.02 }}
    >
      <div className="text-[10px] text-muted uppercase tracking-wider font-bold mb-1">{label}</div>
      <div className={`text-xl font-bold ${highlight ? 'text-teal-bright' : 'text-ink'}`}>{value}</div>
      <div className="text-[10px] text-muted/60">{sub}</div>
    </motion.div>
  )
}
