import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FadeIn, StepIndicator } from './ui'

interface SidebarProps {
    onSubmit: (prompt: string) => void
    isLoading: boolean
    phase: 'input' | 'running' | 'complete'
    isConnected: boolean
    sessionId: string | null
    onReset: () => void
    prompt: string
    onPromptChange: (p: string) => void
}

const PROPERTY_TYPES = [
    { label: 'Single Family', value: 'single-family home' },
    { label: 'Duplex', value: 'duplex' },
    { label: 'Multi-Family', value: 'multi-family property' },
    { label: 'Condo', value: 'condo' },
    { label: 'Commercial', value: 'commercial property' },
    { label: 'Townhouse', value: 'townhouse' },
    { label: 'Land / Lot', value: 'land' },
]

const WORKFLOW_STEPS = ['Configure', 'Plan', 'Analyze', 'Results']

export default function Sidebar({ onSubmit, isLoading, phase, isConnected, sessionId, onReset, prompt, onPromptChange }: SidebarProps) {
    const [budget, setBudget] = useState('250000')
    const [propertyType, setPropertyType] = useState('single-family home')

    const currentStep = phase === 'input' ? 0 : phase === 'running' ? 2 : 3

    const handleAnalyze = () => {
        if (isLoading || !prompt.trim()) return
        const budgetStr = `$${parseInt(budget).toLocaleString()}`
        const lower = prompt.toLowerCase()
        const extras: string[] = []
        if (!lower.includes('$') && !lower.match(/\d{3,}/) && !lower.includes('budget')) {
            extras.push(`budget ${budgetStr}`)
        }
        if (!lower.includes(propertyType) && !lower.includes('property') && !lower.includes('home') && !lower.includes('house') && !lower.includes('condo') && !lower.includes('duplex') && !lower.includes('commercial') && !lower.includes('townhouse') && !lower.includes('land') && !lower.includes('multi')) {
            extras.push(propertyType)
        }
        const finalPrompt = extras.length > 0
            ? `${prompt.trim()} (${extras.join(', ')})`
            : prompt.trim()
        onSubmit(finalPrompt)
    }

    return (
        <aside className="w-80 flex-shrink-0 h-screen sticky top-0 flex flex-col bg-base-2 border-r border-border/50">
            {/* Logo */}
            <div className="px-6 py-6 border-b border-border/50">
                <div className="flex items-center gap-3">
                    <motion.div
                        className="w-10 h-10 rounded-xl gradient-accent flex items-center justify-center shadow-glow-teal"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9z" /><polyline points="9 22 9 12 15 12 15 22" />
                        </svg>
                    </motion.div>
                    <div>
                        <h1 className="text-base font-bold text-ink tracking-title">EstateAgent AI</h1>
                        <p className="text-xs text-muted font-medium">Intelligent Investment Analysis</p>
                    </div>
                </div>
            </div>

            {/* Workflow progress */}
            <div className="px-6 py-4 border-b border-border/50">
                <StepIndicator steps={WORKFLOW_STEPS} currentStep={currentStep} />
            </div>

            {/* Controls */}
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-7">
                {/* Property Type */}
                <FadeIn delay={0.05}>
                    <label className="block text-xs font-bold text-muted uppercase tracking-wide mb-2.5">
                        <span className="inline-flex items-center gap-2">
                            <span className="w-5 h-5 rounded-lg bg-teal/15 flex items-center justify-center">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#729B79" strokeWidth="2.5" strokeLinecap="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>
                            </span>
                            Property Type
                        </span>
                    </label>
                    <select
                        value={propertyType}
                        onChange={e => setPropertyType(e.target.value)}
                        className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-ink
                       focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal/40
                       transition-all appearance-none cursor-pointer hover:border-teal/30"
                    >
                        {PROPERTY_TYPES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                    </select>
                </FadeIn>

                {/* Budget */}
                <FadeIn delay={0.1}>
                    <label className="block text-xs font-bold text-muted uppercase tracking-wide mb-2.5">
                        <span className="inline-flex items-center gap-2">
                            <span className="w-5 h-5 rounded-lg bg-teal/15 flex items-center justify-center">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#729B79" strokeWidth="2.5" strokeLinecap="round"><line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>
                            </span>
                            Budget
                        </span>
                    </label>
                    <div className="relative">
                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-teal text-sm font-bold">$</span>
                        <input
                            type="text"
                            value={parseInt(budget).toLocaleString()}
                            onChange={e => setBudget(e.target.value.replace(/[^0-9]/g, ''))}
                            className="w-full rounded-xl border border-border bg-surface pl-8 pr-4 py-3 text-sm text-ink font-semibold
                         focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal/40 transition-all hover:border-teal/30"
                        />
                    </div>
                </FadeIn>

                {/* Tip */}
                <FadeIn delay={0.15}>
                    <div className="bg-surface/60 border border-border/50 rounded-xl p-4">
                        <p className="text-xs text-muted leading-relaxed">
                            <span className="text-teal-bright font-semibold">Tip:</span> Type any city or region in the prompt area — you're not limited to preset locations.
                            The AI will research whatever market you ask about.
                        </p>
                    </div>
                </FadeIn>
            </div>

            {/* Bottom actions */}
            <div className="px-6 py-5 border-t border-border/50 space-y-3">
                {/* Connection indicator */}
                <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                        {isConnected ? (
                            <>
                                <span className="w-2 h-2 rounded-full bg-teal-bright pulse-ring" />
                                <span className="text-teal-bright font-semibold">Connected</span>
                            </>
                        ) : (
                            <>
                                <span className="w-2 h-2 rounded-full bg-muted/30" />
                                <span className="text-muted/50">Idle</span>
                            </>
                        )}
                    </div>
                    {sessionId && (
                        <span className="text-muted/40 font-mono text-[11px] bg-surface px-2 py-0.5 rounded">{sessionId.slice(0, 8)}</span>
                    )}
                </div>

                <motion.button
                    onClick={handleAnalyze}
                    disabled={isLoading || !prompt.trim()}
                    whileHover={!isLoading && prompt.trim() ? { scale: 1.02 } : {}}
                    whileTap={!isLoading && prompt.trim() ? { scale: 0.98 } : {}}
                    className="w-full gradient-accent text-white rounded-xl py-3.5 text-sm font-bold
                     shadow-glow-teal hover:shadow-glow-lg transition-all duration-300
                     disabled:opacity-40 disabled:cursor-not-allowed
                     flex items-center justify-center gap-2.5"
                >
                    {isLoading ? (
                        <>
                            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            Analyzing…
                        </>
                    ) : !prompt.trim() ? (
                        <>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" /><polyline points="10 17 15 12 10 7" /><line x1="15" y1="12" x2="3" y2="12" /></svg>
                            Type a prompt first →
                        </>
                    ) : (
                        <>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><polygon points="5 3 19 12 5 21 5 3" /></svg>
                            Run Analysis
                        </>
                    )}
                </motion.button>

                <AnimatePresence>
                    {phase !== 'input' && (
                        <motion.button
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            onClick={onReset}
                            className="w-full text-muted hover:text-ink text-xs font-semibold py-2 transition-colors
                         border border-border rounded-xl hover:border-teal/20"
                        >
                            ← Start New Analysis
                        </motion.button>
                    )}
                </AnimatePresence>
            </div>
        </aside>
    )
}
