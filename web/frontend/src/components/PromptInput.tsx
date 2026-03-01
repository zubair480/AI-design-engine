import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FadeIn, GlassCard } from './ui'

interface PromptInputProps {
  onSubmit: (prompt: string) => void
  isLoading: boolean
  prompt: string
  onPromptChange: (p: string) => void
}

const EXAMPLE_PROMPTS = [
  { label: '🏠 Atlanta Rental', prompt: 'I want to invest in a rental property in Atlanta, GA targeting cash flow' },
  { label: '🏘️ Austin Multi-Family', prompt: 'Analyze a multi-family investment in Austin, TX with a $400k budget' },
  { label: '📈 Charlotte Growth', prompt: 'Best neighborhoods in Charlotte, NC for property appreciation with $300k' },
  { label: '💰 Tampa Cash Flow', prompt: 'Where in Tampa, FL can I get the best cash-on-cash return with $200k?' },
  { label: '🏢 Denver Condo', prompt: 'Should I buy a condo in Denver, CO as a rental investment?' },
  { label: '🌴 Phoenix Market', prompt: 'Analyze the Phoenix, AZ real estate market for a $350k single-family investment' },
]

export default function PromptInput({ onSubmit, isLoading, prompt, onPromptChange }: PromptInputProps) {
  const [isFocused, setIsFocused] = useState(false)
  const [showNudge, setShowNudge] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (prompt.trim() && !isLoading) {
      setShowNudge(false)
      onSubmit(prompt.trim())
    } else if (!prompt.trim()) {
      setShowNudge(true)
    }
  }

  const handleExample = (p: string) => {
    onPromptChange(p)
    setShowNudge(false)
    if (!isLoading) onSubmit(p)
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[75vh] w-full max-w-2xl mx-auto px-4">
      {/* Ambient background glow */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-teal/5 rounded-full blur-[120px] animate-pulse-slow" />
        <div className="absolute top-1/2 left-1/3 w-[400px] h-[400px] bg-secondary/5 rounded-full blur-[100px] animate-float" />
      </div>

      <FadeIn delay={0} className="relative z-10">
        <div className="text-center mb-12">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="inline-flex items-center gap-2.5 bg-teal/10 border border-teal/20 text-teal-bright px-5 py-2 rounded-full text-xs font-bold mb-8 tracking-wide"
          >
            <span className="w-2 h-2 rounded-full bg-teal-bright animate-pulse-dot" />
            EstateAgent AI
          </motion.div>

          <motion.h1
            className="text-5xl font-extrabold tracking-tight mb-4 leading-[1.1]"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.6 }}
          >
            <span className="text-ink">Find your next</span>
            <br />
            <span className="gradient-text-hero">investment property.</span>
          </motion.h1>

          <motion.p
            className="text-muted text-lg max-w-lg mx-auto leading-relaxed"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            Multi-agent AI analyzes markets in parallel — <span className="text-teal font-semibold">ROI, risk & cash flow</span> in seconds.
          </motion.p>
        </div>
      </FadeIn>

      <FadeIn delay={0.2} className="w-full relative z-10">
        <motion.div
          animate={isFocused ? { boxShadow: '0 0 40px rgba(114,155,121,0.15)' } : { boxShadow: '0 0 0px rgba(114,155,121,0)' }}
          transition={{ duration: 0.3 }}
          className="rounded-2xl"
        >
          <GlassCard className={`!p-0 transition-all duration-300 ${isFocused ? '!border-teal/30' : ''} ${showNudge ? '!border-warning/40' : ''}`}>
            <form onSubmit={handleSubmit}>
              <textarea
                value={prompt}
                onChange={(e) => { onPromptChange(e.target.value); setShowNudge(false) }}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                placeholder="Tell us about your investment — include the city/region you're interested in…"
                className="w-full bg-transparent border-0 text-ink text-base
                           placeholder-muted/40 focus:outline-none resize-none leading-relaxed
                           p-6 pb-3"
                rows={4}
                disabled={isLoading}
              />
              <div className="flex items-center justify-between px-6 py-4 border-t border-border/50">
                <div className="flex items-center gap-2">
                  {['Multi-Agent', 'Parallel Analysis', 'Real-Time'].map((t) => (
                    <span key={t} className="text-[10px] text-muted/60 bg-surface-2 px-2.5 py-1 rounded-lg font-semibold border border-border/50">{t}</span>
                  ))}
                </div>
                <motion.button
                  type="submit"
                  disabled={isLoading}
                  whileHover={!isLoading ? { scale: 1.03 } : {}}
                  whileTap={!isLoading ? { scale: 0.97 } : {}}
                  className="gradient-accent text-white px-7 py-2.5 rounded-xl text-sm font-bold
                             shadow-glow-teal hover:shadow-glow-lg transition-all duration-300
                             disabled:opacity-30 disabled:cursor-not-allowed disabled:shadow-none
                             flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                      Analyzing…
                    </>
                  ) : (
                    <>
                      Analyze
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></svg>
                    </>
                  )}
                </motion.button>
              </div>
            </form>
          </GlassCard>
        </motion.div>

        {/* Nudge message when user tries to submit empty */}
        <AnimatePresence>
          {showNudge && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="mt-4 text-center"
            >
              <div className="inline-flex items-center gap-2 bg-warning/10 border border-warning/25 text-warning px-5 py-3 rounded-xl text-sm font-medium">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
                Type a location & investment goal above, or pick a sample prompt below
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </FadeIn>

      <FadeIn delay={0.4} className="mt-10 w-full relative z-10">
        <p className="text-center text-xs text-muted/40 font-bold uppercase tracking-widest mb-4">
          {showNudge ? '👇 Pick one to get started' : 'Quick start'}
        </p>
        <div className="flex flex-wrap gap-2.5 justify-center">
          {EXAMPLE_PROMPTS.map((ex) => (
            <motion.button
              key={ex.label}
              onClick={() => handleExample(ex.prompt)}
              disabled={isLoading}
              whileHover={{ scale: 1.04, y: -2 }}
              whileTap={{ scale: 0.97 }}
              animate={showNudge ? { scale: [1, 1.03, 1] } : {}}
              transition={showNudge ? { duration: 1.5, repeat: Infinity } : {}}
              className={`bg-surface/80 backdrop-blur-sm border text-ink/80 hover:text-ink px-5 py-2.5 rounded-xl text-sm font-medium
                         transition-all duration-200 hover:shadow-glow
                         disabled:opacity-30 disabled:cursor-not-allowed
                         ${showNudge ? 'border-teal/30 shadow-glow' : 'border-border hover:border-teal/30'}`}
            >
              {ex.label}
            </motion.button>
          ))}
        </div>
      </FadeIn>
    </div>
  )
}
