import { motion } from 'framer-motion'
import type { ReactNode } from 'react'

/* ──────────────────────────────────────────────
   Staggered fade-in wrapper
   ────────────────────────────────────────────── */
export function FadeIn({
    children,
    delay = 0,
    className = '',
    direction = 'up',
}: {
    children: ReactNode
    delay?: number
    className?: string
    direction?: 'up' | 'down' | 'left' | 'right'
}) {
    const offsets = {
        up: { y: 20 },
        down: { y: -20 },
        left: { x: 20 },
        right: { x: -20 },
    }
    return (
        <motion.div
            initial={{ opacity: 0, ...offsets[direction] }}
            animate={{ opacity: 1, x: 0, y: 0 }}
            transition={{ duration: 0.5, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
            className={className}
        >
            {children}
        </motion.div>
    )
}

/* ──────────────────────────────────────────────
   Glass Card — dark glass container
   ────────────────────────────────────────────── */
export function GlassCard({
    children,
    className = '',
    hover = false,
    glow = false,
}: {
    children: ReactNode
    className?: string
    hover?: boolean
    glow?: boolean
}) {
    return (
        <div
            className={`
        glass rounded-2xl p-6 shadow-card relative overflow-hidden
        transition-all duration-300
        ${hover ? 'hover:glass-hover hover:shadow-glow hover:-translate-y-1 cursor-pointer' : ''}
        ${glow ? 'animate-glow-pulse' : ''}
        ${className}
      `}
        >
            {children}
        </div>
    )
}

/* ──────────────────────────────────────────────
   Metric Card — stat display with optional glow
   ────────────────────────────────────────────── */
export function MetricCard({
    label,
    value,
    sub,
    icon,
    accent = false,
    delay = 0,
}: {
    label: string
    value: string
    sub?: string
    icon?: string
    accent?: boolean
    delay?: number
}) {
    return (
        <FadeIn delay={delay}>
            <div
                className={`
          rounded-2xl p-5 transition-all duration-300 relative overflow-hidden
          hover:-translate-y-1
          ${accent
                        ? 'gradient-accent text-white shadow-glow-teal'
                        : 'glass shadow-soft hover:shadow-card'
                    }
        `}
            >
                {accent && (
                    <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent pointer-events-none" />
                )}
                {icon && <span className="text-xl mb-2 block relative z-10">{icon}</span>}
                <p className={`text-[11px] font-semibold uppercase tracking-wide mb-1 relative z-10 ${accent ? 'text-white/70' : 'text-muted'}`}>
                    {label}
                </p>
                <p className={`text-2xl font-bold tracking-tight relative z-10 ${accent ? 'text-white' : 'text-ink'}`}>
                    {value}
                </p>
                {sub && (
                    <p className={`text-xs mt-1 relative z-10 ${accent ? 'text-white/60' : 'text-muted/70'}`}>
                        {sub}
                    </p>
                )}
            </div>
        </FadeIn>
    )
}

/* ──────────────────────────────────────────────
   Shimmer Skeleton — dark loading placeholder
   ────────────────────────────────────────────── */
export function Skeleton({
    className = '',
    rows = 1,
}: {
    className?: string
    rows?: number
}) {
    return (
        <div className={`space-y-3 ${className}`}>
            {Array.from({ length: rows }).map((_, i) => (
                <div
                    key={i}
                    className="shimmer rounded-xl h-5"
                    style={{ width: `${85 - i * 12}%` }}
                />
            ))}
        </div>
    )
}

export function SkeletonCard() {
    return (
        <div className="glass rounded-2xl p-6 space-y-4 shadow-soft">
            <div className="shimmer rounded-lg h-4 w-24" />
            <div className="shimmer rounded-lg h-8 w-32" />
            <div className="shimmer rounded-lg h-3 w-20" />
        </div>
    )
}

/* ──────────────────────────────────────────────
   Badge — status pill with dark contrast
   ────────────────────────────────────────────── */
export function Badge({
    children,
    variant = 'default',
}: {
    children: ReactNode
    variant?: 'default' | 'success' | 'warning' | 'danger'
}) {
    const styles = {
        default: 'bg-surface-2 text-muted border border-border',
        success: 'bg-teal/15 text-teal-bright border border-teal/25',
        warning: 'bg-warning/15 text-warning border border-warning/25',
        danger: 'bg-danger/15 text-danger border border-danger/25',
    }
    return (
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${styles[variant]}`}>
            {children}
        </span>
    )
}

/* ──────────────────────────────────────────────
   Section heading — dark theme
   ────────────────────────────────────────────── */
export function SectionTitle({
    children,
    sub,
}: {
    children: ReactNode
    sub?: string
}) {
    return (
        <div className="mb-5">
            <h2 className="text-lg font-bold text-ink tracking-title">{children}</h2>
            {sub && <p className="text-sm text-muted mt-0.5">{sub}</p>}
        </div>
    )
}

/* ──────────────────────────────────────────────
   Step indicator — workflow progress
   ────────────────────────────────────────────── */
export function StepIndicator({
    steps,
    currentStep,
}: {
    steps: string[]
    currentStep: number
}) {
    return (
        <div className="flex items-center gap-1">
            {steps.map((step, i) => (
                <div key={step} className="flex items-center gap-1">
                    <div className={`
            flex items-center justify-center w-7 h-7 rounded-full text-[10px] font-bold transition-all duration-500
            ${i < currentStep
                            ? 'bg-teal text-white shadow-neon'
                            : i === currentStep
                                ? 'bg-teal/20 text-teal border border-teal/40 animate-glow-pulse'
                                : 'bg-surface-2 text-muted/50 border border-border'
                        }
          `}>
                        {i < currentStep ? '✓' : i + 1}
                    </div>
                    {i < steps.length - 1 && (
                        <div className={`w-6 h-0.5 rounded-full transition-all duration-500 ${i < currentStep ? 'bg-teal' : 'bg-border'
                            }`} />
                    )}
                </div>
            ))}
        </div>
    )
}
