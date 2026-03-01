import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell
} from 'recharts'
import { FadeIn, GlassCard, MetricCard, Badge, SectionTitle } from './ui'

interface ResultsPanelProps {
  results: any
  onFollowup: (prompt: string) => void
}

export default function ResultsPanel({ results, onFollowup }: ResultsPanelProps) {
  const [followupPrompt, setFollowupPrompt] = useState('')

  if (!results) return null

  // ── Extract the new 3-tier pipeline structure ──
  // API returns: { session_id, status, data: { plan, analyst_reports, conclusion, pipeline_elapsed_seconds } }
  const data = results.data || results
  const plan = data.plan || {}
  const analystReports: any[] = data.analyst_reports || []
  const conclusion = data.conclusion || {}
  const pipelineTime = data.pipeline_elapsed_seconds || 0

  // Conclusion fields
  const rankedRegions: any[] = conclusion.ranked_regions || []
  const topRegion = rankedRegions[0] || {}
  const recommendation = conclusion.recommendation || ''
  const execSummary = conclusion.executive_summary || ''
  const strategy = conclusion.recommended_strategy || ''
  const topRisks: string[] = conclusion.top_risks || []
  const nextSteps: string[] = conclusion.next_steps || []
  const memo = conclusion.full_advisory_memo || ''

  // Resolve the recommended region — match by name from ranked list,
  // fall back to the #1 ranked entry so all top-level metrics stay consistent.
  const recName = conclusion.recommended_region || ''
  const recRegion =
    rankedRegions.find((r: any) => r.region === recName) || topRegion

  // Build chart data from ranked regions
  const chartData = rankedRegions.map((r: any) => ({
    name: r.region || `#${r.rank}`,
    score: r.score || 0,
    rank: r.rank || 0,
  }))

  const handleFollowup = (e: React.FormEvent) => {
    e.preventDefault()
    if (followupPrompt.trim()) {
      onFollowup(followupPrompt.trim())
      setFollowupPrompt('')
    }
  }

  const recBadge = (rec: string) => {
    if (rec === 'strong_buy') return <Badge variant="success">Strong Buy</Badge>
    if (rec === 'buy') return <Badge variant="success">Buy</Badge>
    if (rec === 'hold') return <Badge variant="warning">Hold</Badge>
    if (rec === 'avoid') return <Badge variant="danger">Avoid</Badge>
    return <Badge>{rec.replace(/_/g, ' ')}</Badge>
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* ── Top-level Metrics ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Top Region"
          value={recRegion.region || recName || '—'}
          sub={`Score: ${recRegion.score || '—'}/100`}
          icon="🏆"
          accent
          delay={0}
        />
        <MetricCard
          label="Recommendation"
          value={recommendation.replace(/_/g, ' ').toUpperCase() || '—'}
          sub="investment verdict"
          icon="📊"
          delay={0.05}
        />
        <MetricCard
          label="Regions Analyzed"
          value={`${analystReports.length}`}
          sub={`in ${pipelineTime}s`}
          icon="🔬"
          delay={0.1}
        />
        <MetricCard
          label="Cash Flow"
          value={recRegion.monthly_cash_flow_est ? `$${recRegion.monthly_cash_flow_est.toLocaleString()}/mo` : '—'}
          sub={recRegion.five_year_return_est_pct ? `${recRegion.five_year_return_est_pct}% 5yr return` : 'top region estimate'}
          icon="💰"
          delay={0.15}
        />
      </div>

      {/* ── Region Scoreboard Chart ── */}
      {chartData.length > 0 && (
        <FadeIn delay={0.2}>
          <GlassCard>
            <SectionTitle sub={`${analystReports.length} regions analyzed by parallel AI agents`}>
              Region Scoreboard
            </SectionTitle>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, bottom: 5, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(51,51,64,0.5)" horizontal={false} />
                <XAxis
                  type="number"
                  domain={[0, 100]}
                  tick={{ fill: '#8B8B9E', fontSize: 10 }}
                  axisLine={{ stroke: 'rgba(51,51,64,0.5)' }}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fill: '#F3E8EE', fontSize: 12, fontWeight: 600 }}
                  axisLine={false}
                  tickLine={false}
                  width={140}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(30,30,36,0.95)',
                    backdropFilter: 'blur(16px)',
                    border: '1px solid rgba(51,51,64,0.6)',
                    borderRadius: '12px',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
                    fontSize: '12px',
                    color: '#F3E8EE',
                  }}
                  labelStyle={{ color: '#F3E8EE', fontWeight: 700 }}
                  formatter={(value: number) => [`${value}/100`, 'Score']}
                />
                <Bar dataKey="score" radius={[0, 6, 6, 0]} barSize={28}>
                  {chartData.map((_: any, index: number) => (
                    <Cell
                      key={index}
                      fill={index === 0 ? '#729B79' : index === 1 ? '#8BC49A' : '#475B63'}
                      opacity={0.9}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </GlassCard>
        </FadeIn>
      )}

      {/* ── Ranked Region Cards ── */}
      {rankedRegions.length > 0 && (
        <FadeIn delay={0.25}>
          <SectionTitle sub="Ranked by investment score">Region Analysis</SectionTitle>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {rankedRegions.map((r: any, i: number) => (
              <motion.div
                key={r.region || i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + i * 0.08 }}
              >
                <GlassCard hover className={i === 0 ? '!border-teal/30 shadow-glow-teal' : ''}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${i === 0 ? 'gradient-accent text-white' : 'bg-surface-2 text-muted'
                        }`}>
                        #{r.rank}
                      </span>
                      <h4 className="text-sm font-bold text-ink">{r.region}</h4>
                    </div>
                    <span className={`text-lg font-black ${i === 0 ? 'text-teal-bright' : 'text-ink'}`}>
                      {r.score}
                    </span>
                  </div>
                  {r.headline && (
                    <p className="text-xs text-muted leading-relaxed mb-3">{r.headline}</p>
                  )}
                  {r.score_breakdown && (
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="bg-surface-2 rounded-lg p-2">
                        <div className="text-[10px] text-muted font-bold uppercase">Risk</div>
                        <div className="text-sm font-bold text-ink">{r.score_breakdown.risk}/20</div>
                      </div>
                      <div className="bg-surface-2 rounded-lg p-2">
                        <div className="text-[10px] text-muted font-bold uppercase">ROI</div>
                        <div className="text-sm font-bold text-ink">{r.score_breakdown.roi_potential}/50</div>
                      </div>
                      <div className="bg-surface-2 rounded-lg p-2">
                        <div className="text-[10px] text-muted font-bold uppercase">Feas.</div>
                        <div className="text-sm font-bold text-ink">{r.score_breakdown.feasibility}/30</div>
                      </div>
                    </div>
                  )}
                  {(r.monthly_cash_flow_est || r.five_year_return_est_pct) && (
                    <div className="flex gap-4 mt-3 pt-3 border-t border-border/40">
                      {r.monthly_cash_flow_est && (
                        <div className="text-xs">
                          <span className="text-muted">Cash Flow: </span>
                          <span className="font-bold text-teal-bright">${r.monthly_cash_flow_est.toLocaleString()}/mo</span>
                        </div>
                      )}
                      {r.five_year_return_est_pct && (
                        <div className="text-xs">
                          <span className="text-muted">5yr Return: </span>
                          <span className="font-bold text-ink">{r.five_year_return_est_pct}%</span>
                        </div>
                      )}
                    </div>
                  )}
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </FadeIn>
      )}

      {/* ── Strategy & Executive Summary ── */}
      {execSummary && (
        <FadeIn delay={0.35}>
          <GlassCard>
            <div className="flex items-center gap-3 mb-5">
              <SectionTitle>Investment Recommendation</SectionTitle>
              {recommendation && recBadge(recommendation)}
            </div>

            <p className="text-sm text-ink/85 leading-relaxed mb-5">
              {execSummary}
            </p>

            {strategy && (
              <div className="bg-teal/8 border border-teal/20 rounded-xl p-4 mb-5">
                <h4 className="text-xs font-bold text-teal-bright uppercase tracking-wide mb-2">Recommended Strategy</h4>
                <p className="text-sm text-ink/80 leading-relaxed">{strategy}</p>
              </div>
            )}

            {topRisks.length > 0 && (
              <div className="mb-5">
                <h4 className="text-xs font-bold text-muted uppercase tracking-wide mb-3">Top Risks</h4>
                <ul className="space-y-2">
                  {topRisks.map((r: string, i: number) => (
                    <motion.li
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.4 + i * 0.05 }}
                      className="text-sm text-ink/70 flex items-start gap-2.5"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-danger mt-2 flex-shrink-0" />
                      {r}
                    </motion.li>
                  ))}
                </ul>
              </div>
            )}

            {nextSteps.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-muted uppercase tracking-wide mb-3">Next Steps</h4>
                <ul className="space-y-2">
                  {nextSteps.map((s: string, i: number) => (
                    <motion.li
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.5 + i * 0.05 }}
                      className="text-sm text-ink/70 flex items-start gap-2.5"
                    >
                      <span className="w-5 h-5 rounded-full bg-teal/15 flex items-center justify-center flex-shrink-0 text-[10px] font-bold text-teal">{i + 1}</span>
                      {s}
                    </motion.li>
                  ))}
                </ul>
              </div>
            )}
          </GlassCard>
        </FadeIn>
      )}

      {/* ── Full Advisory Memo ── */}
      {memo && (
        <FadeIn delay={0.4}>
          <GlassCard>
            <SectionTitle sub="Comprehensive investment advisory report">
              Advisory Memo
            </SectionTitle>
            <div className="text-sm text-ink/75 leading-relaxed whitespace-pre-line">
              {memo}
            </div>
          </GlassCard>
        </FadeIn>
      )}

      {/* ── Performance banner ── */}
      <FadeIn delay={0.45}>
        <div className="text-center py-4">
          <p className="text-xs text-muted/40 font-mono">
            {analystReports.length} regions · {pipelineTime}s · Map-Reduce pipeline on Modal
          </p>
        </div>
      </FadeIn>

      {/* ── Follow-up ── */}
      <FadeIn delay={0.5}>
        <GlassCard>
          <SectionTitle sub="Ask about different regions, budget changes, or strategies.">
            Ask a Follow-up
          </SectionTitle>
          <form onSubmit={handleFollowup} className="flex gap-3">
            <input
              type="text"
              value={followupPrompt}
              onChange={(e) => setFollowupPrompt(e.target.value)}
              placeholder="What about Decatur instead? Or re-run with $300k budget..."
              className="flex-1 bg-surface border border-border rounded-xl px-4 py-3 text-sm text-ink
                         placeholder-muted/40 focus:outline-none focus:ring-2 focus:ring-teal/25
                         focus:border-teal/30 transition-all hover:border-teal/20"
            />
            <motion.button
              type="submit"
              disabled={!followupPrompt.trim()}
              whileHover={followupPrompt.trim() ? { scale: 1.03 } : {}}
              whileTap={followupPrompt.trim() ? { scale: 0.97 } : {}}
              className="gradient-accent text-white px-6 py-3 rounded-xl text-sm font-bold
                         shadow-glow-teal hover:shadow-glow-lg transition-all duration-300
                         disabled:opacity-30 disabled:cursor-not-allowed disabled:shadow-none"
            >
              Re-analyze
            </motion.button>
          </form>
        </GlassCard>
      </FadeIn>
    </motion.div>
  )
}
