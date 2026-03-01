import { useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AgentEvent } from '../hooks/useWebSocket'
import { GlassCard } from './ui'

interface PipelineProgressProps {
  events: AgentEvent[]
}

/* ── Pipeline stage weights (sum = 100) ── */
const STAGE_WEIGHTS = {
  planning: 12,   // pipeline_started → plan_complete
  analysts: 63,   // plan_complete → all analyst_complete
  conclusion: 20, // conclusion_started → conclusion_complete
  done: 5,        // pipeline_complete
}

interface PipelineState {
  pct: number
  stage: string
  stageLabel: string
  numRegions: number
  completedRegions: number
  regions: string[]
  completedRegionNames: string[]
  isDone: boolean
}

function derivePipelineState(events: AgentEvent[]): PipelineState {
  let stage = 'waiting'
  let stageLabel = 'Initializing…'
  let numRegions = 0
  let completedRegions = 0
  let regions: string[] = []
  let completedRegionNames: string[] = []
  let pct = 0
  let isDone = false

  for (const e of events) {
    switch (e.event) {
      case 'pipeline_started':
        stage = 'planning'
        stageLabel = 'Planning investment strategy…'
        pct = 2
        break
      case 'plan_complete':
        stage = 'analysts'
        numRegions = e.num_regions || 3
        regions = e.regions || []
        stageLabel = `Analyzing ${numRegions} markets…`
        pct = STAGE_WEIGHTS.planning
        break
      case 'analyst_started': {
        stage = 'analysts'
        const region = e.region || 'region'
        stageLabel = `Analyzing ${region}…`
        break
      }
      case 'analyst_complete': {
        const region = e.region || ''
        if (region && !completedRegionNames.includes(region)) {
          completedRegionNames.push(region)
          completedRegions = completedRegionNames.length
        }
        const analystProgress = numRegions > 0
          ? (completedRegions / numRegions) * STAGE_WEIGHTS.analysts
          : 0
        pct = STAGE_WEIGHTS.planning + analystProgress
        stageLabel = `${completedRegions}/${numRegions} markets complete`
        break
      }
      case 'conclusion_started':
        stage = 'conclusion'
        stageLabel = 'Generating investment advisory…'
        pct = STAGE_WEIGHTS.planning + STAGE_WEIGHTS.analysts
        break
      case 'conclusion_complete':
        stage = 'finishing'
        stageLabel = 'Finalizing report…'
        pct = STAGE_WEIGHTS.planning + STAGE_WEIGHTS.analysts + STAGE_WEIGHTS.conclusion
        break
      case 'pipeline_complete':
      case 'done':
        stage = 'done'
        stageLabel = 'Analysis complete'
        pct = 100
        isDone = true
        break
    }
  }

  return { pct: Math.min(pct, 100), stage, stageLabel, numRegions, completedRegions, regions, completedRegionNames, isDone }
}

/* ── Animated SVG circular progress ring ── */
function ProgressRing({ pct, isDone }: { pct: number; isDone: boolean }) {
  const size = 180
  const strokeWidth = 8
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (pct / 100) * circumference

  return (
    <div className="relative" style={{ width: size, height: size }}>
      {/* Ambient glow behind */}
      <motion.div
        className="absolute inset-0 rounded-full"
        animate={{
          boxShadow: isDone
            ? '0 0 60px rgba(114,155,121,0.35), 0 0 120px rgba(114,155,121,0.15)'
            : [
                '0 0 30px rgba(114,155,121,0.15), 0 0 60px rgba(114,155,121,0.05)',
                '0 0 50px rgba(114,155,121,0.25), 0 0 80px rgba(114,155,121,0.10)',
                '0 0 30px rgba(114,155,121,0.15), 0 0 60px rgba(114,155,121,0.05)',
              ],
        }}
        transition={isDone ? {} : { duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
      />

      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(51,51,64,0.5)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Progress arc */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="url(#progressGradient)"
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
        />
        {/* Gradient definition */}
        <defs>
          <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#729B79" />
            <stop offset="50%" stopColor="#8BC49A" />
            <stop offset="100%" stopColor="#BACDB0" />
          </linearGradient>
        </defs>
      </svg>

      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          key={Math.round(pct)}
          initial={{ opacity: 0.6, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`text-4xl font-black tracking-tight ${isDone ? 'text-teal-bright' : 'text-ink'}`}
        >
          {Math.round(pct)}%
        </motion.span>
        {isDone ? (
          <motion.span
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            className="text-xs text-teal-bright font-bold mt-1"
          >
            ✓ Complete
          </motion.span>
        ) : (
          <span className="text-[10px] text-muted font-medium mt-1">processing</span>
        )}
      </div>
    </div>
  )
}

/* ── Pipeline stage indicators ── */
const STAGES = [
  { key: 'planning', label: 'Planning', icon: '📋' },
  { key: 'analysts', label: 'Market Analysis', icon: '🔬' },
  { key: 'conclusion', label: 'Advisory', icon: '📊' },
  { key: 'done', label: 'Complete', icon: '✅' },
]

function StageTracker({ currentStage, completedRegions, numRegions }: { currentStage: string; completedRegions: number; numRegions: number }) {
  const stageOrder = ['planning', 'analysts', 'conclusion', 'finishing', 'done']
  const currentIdx = stageOrder.indexOf(currentStage)

  return (
    <div className="flex items-center gap-2 justify-center">
      {STAGES.map((s, i) => {
        const sIdx = stageOrder.indexOf(s.key)
        const isActive = currentStage === s.key || (s.key === 'conclusion' && currentStage === 'finishing')
        const isComplete = currentIdx > sIdx || (s.key === 'done' && currentStage === 'done')
        const isPending = currentIdx < sIdx

        return (
          <div key={s.key} className="flex items-center gap-2">
            <motion.div
              animate={isActive ? { scale: [1, 1.05, 1] } : {}}
              transition={isActive ? { duration: 1.5, repeat: Infinity } : {}}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all duration-300 ${
                isComplete
                  ? 'bg-teal/15 text-teal-bright border border-teal/25'
                  : isActive
                    ? 'bg-teal/10 text-teal-bright border border-teal/30 shadow-neon'
                    : 'bg-surface-2 text-muted/40 border border-border/50'
              }`}
            >
              <span className="text-sm">{s.icon}</span>
              <span>{s.label}</span>
              {s.key === 'analysts' && numRegions > 0 && (isActive || isComplete) && (
                <span className="text-[9px] bg-surface-2 px-1.5 py-0.5 rounded font-bold ml-0.5">
                  {completedRegions}/{numRegions}
                </span>
              )}
            </motion.div>
            {i < STAGES.length - 1 && (
              <div className={`w-4 h-px transition-all duration-500 ${
                isComplete ? 'bg-teal' : 'bg-border/50'
              }`} />
            )}
          </div>
        )
      })}
    </div>
  )
}

/* ── Region chips — show which markets are being/have been analyzed ── */
function RegionChips({ regions, completedRegionNames }: { regions: string[]; completedRegionNames: string[] }) {
  if (regions.length === 0) return null

  return (
    <div className="flex flex-wrap gap-2 justify-center mt-4">
      <AnimatePresence>
        {regions.map((region) => {
          const isDone = completedRegionNames.includes(region)
          return (
            <motion.span
              key={region}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-semibold transition-all duration-300 ${
                isDone
                  ? 'bg-teal/12 text-teal-bright border border-teal/20'
                  : 'bg-surface-2 text-muted border border-border/50 animate-pulse'
              }`}
            >
              {isDone && <span className="text-[9px]">✓</span>}
              {region}
            </motion.span>
          )
        })}
      </AnimatePresence>
    </div>
  )
}

/* ── Main component ── */
export default function PipelineProgress({ events }: PipelineProgressProps) {
  const state = useMemo(() => derivePipelineState(events), [events])

  return (
    <div className="space-y-8">
      {/* Progress ring */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="flex flex-col items-center gap-6"
      >
        <ProgressRing pct={state.pct} isDone={state.isDone} />

        {/* Current stage label */}
        <motion.p
          key={state.stageLabel}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm text-muted font-medium text-center"
        >
          {state.stageLabel}
        </motion.p>
      </motion.div>

      {/* Stage tracker */}
      <StageTracker
        currentStage={state.stage}
        completedRegions={state.completedRegions}
        numRegions={state.numRegions}
      />

      {/* Region chips */}
      <RegionChips
        regions={state.regions}
        completedRegionNames={state.completedRegionNames}
      />
    </div>
  )
}
