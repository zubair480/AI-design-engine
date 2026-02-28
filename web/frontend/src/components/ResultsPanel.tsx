import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell
} from 'recharts'

interface ResultsPanelProps {
  results: any
  onFollowup: (prompt: string) => void
}

export default function ResultsPanel({ results, onFollowup }: ResultsPanelProps) {
  const [followupPrompt, setFollowupPrompt] = useState('')

  if (!results) return null

  const evaluation = results.evaluation || results.data?.evaluation || results
  const metrics = evaluation?.quantitative_metrics || {}
  const analysis = evaluation?.llm_analysis || {}
  const histogram = evaluation?.histogram || {}
  const simSummary = evaluation?.simulation_summary || {}

  // Build histogram chart data
  const histogramData = (histogram.counts || []).map((count: number, i: number) => ({
    name: histogram.bin_labels?.[i] || `Bin ${i}`,
    count,
    isNegative: (histogram.bin_edges?.[i] || 0) < 0,
  }))

  const handleFollowup = (e: React.FormEvent) => {
    e.preventDefault()
    if (followupPrompt.trim()) {
      onFollowup(followupPrompt.trim())
      setFollowupPrompt('')
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Key Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <BigMetricCard
          label="Expected Annual Profit"
          value={`$${(metrics.expected_annual_profit || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
          color="text-green-400"
          bgColor="bg-green-900/20"
          borderColor="border-green-800/50"
        />
        <BigMetricCard
          label="Mean ROI"
          value={`${(metrics.mean_roi_pct || 0).toFixed(1)}%`}
          color="text-cyan-400"
          bgColor="bg-cyan-900/20"
          borderColor="border-cyan-800/50"
        />
        <BigMetricCard
          label="Probability of Loss"
          value={`${(metrics.probability_of_loss_pct || 0).toFixed(1)}%`}
          color={metrics.probability_of_loss_pct > 30 ? 'text-red-400' : 'text-yellow-400'}
          bgColor={metrics.probability_of_loss_pct > 30 ? 'bg-red-900/20' : 'bg-yellow-900/20'}
          borderColor={metrics.probability_of_loss_pct > 30 ? 'border-red-800/50' : 'border-yellow-800/50'}
        />
        <BigMetricCard
          label="Break-even"
          value={`${metrics.break_even_months || '—'} months`}
          color="text-purple-400"
          bgColor="bg-purple-900/20"
          borderColor="border-purple-800/50"
        />
      </div>

      {/* Profit Distribution Histogram */}
      {histogramData.length > 0 && (
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 card-glow">
          <h3 className="text-lg font-semibold text-white mb-4">
            📊 Profit Distribution ({simSummary.total_scenarios?.toLocaleString()} scenarios)
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={histogramData} margin={{ top: 5, right: 20, bottom: 60, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="name"
                tick={{ fill: '#9ca3af', fontSize: 9 }}
                angle={-45}
                textAnchor="end"
                height={70}
              />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                labelStyle={{ color: '#fff' }}
                itemStyle={{ color: '#9ca3af' }}
              />
              <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                {histogramData.map((entry: any, index: number) => (
                  <Cell key={index} fill={entry.isNegative ? '#ef4444' : '#0ea5e9'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-6 mt-2 text-xs text-gray-500">
            <span>P10: ${(metrics.p10_profit_worst_case || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
            <span>Median: ${(metrics.median_annual_profit || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
            <span>P90: ${(metrics.p90_profit_best_case || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
          </div>
        </div>
      )}

      {/* Detailed Metrics */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Revenue & Cost */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 card-glow">
          <h3 className="text-lg font-semibold text-white mb-3">💰 Revenue & Cost</h3>
          <div className="space-y-2 text-sm">
            <MetricRow label="Expected Annual Revenue" value={`$${(metrics.expected_annual_revenue || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
            <MetricRow label="Expected Annual Cost" value={`$${(metrics.expected_annual_cost || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
            <MetricRow label="Initial Investment" value={`$${(metrics.initial_investment || 0).toLocaleString()}`} />
            <MetricRow label="Sharpe Ratio" value={(metrics.sharpe_ratio || 0).toFixed(3)} />
            <MetricRow label="Prob. of 20% ROI" value={`${(metrics.prob_20pct_roi || 0).toFixed(1)}%`} />
          </div>
        </div>

        {/* Risk Metrics */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 card-glow">
          <h3 className="text-lg font-semibold text-white mb-3">⚠️ Risk Analysis</h3>
          <div className="space-y-2 text-sm">
            <MetricRow label="Value at Risk (P10)" value={`$${(metrics.value_at_risk_p10 || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
            <MetricRow label="Worst Case (P10) Profit" value={`$${(metrics.p10_profit_worst_case || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
            <MetricRow label="Best Case (P90) Profit" value={`$${(metrics.p90_profit_best_case || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
            <MetricRow label="Profit Std Dev" value={`$${(metrics.profit_std || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
          </div>
        </div>
      </div>

      {/* LLM Analysis */}
      {analysis.executive_summary && (
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 card-glow">
          <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            🧠 AI Strategic Analysis
            {analysis.recommendation && (
              <span className={`text-xs px-2 py-1 rounded-full ${
                analysis.recommendation === 'strong_go' ? 'bg-green-900/50 text-green-400' :
                analysis.recommendation === 'cautious_go' ? 'bg-yellow-900/50 text-yellow-400' :
                analysis.recommendation === 'conditional' ? 'bg-orange-900/50 text-orange-400' :
                'bg-red-900/50 text-red-400'
              }`}>
                {analysis.recommendation?.replace(/_/g, ' ').toUpperCase()}
              </span>
            )}
          </h3>

          <p className="text-gray-300 text-sm leading-relaxed mb-4 whitespace-pre-line">
            {analysis.executive_summary}
          </p>

          {analysis.key_findings && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-400 mb-2">Key Findings</h4>
              <ul className="space-y-1">
                {analysis.key_findings.map((finding: string, i: number) => (
                  <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                    <span className="text-brand-400 mt-0.5">•</span>
                    {finding}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {analysis.risk_mitigation && (
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-2">Risk Mitigation</h4>
              <ul className="space-y-1">
                {analysis.risk_mitigation.map((risk: string, i: number) => (
                  <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                    <span className="text-yellow-400 mt-0.5">⚡</span>
                    {risk}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Performance Banner */}
      <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-4 text-center">
        <p className="text-gray-400 text-sm">
          ⚡ {simSummary.total_scenarios?.toLocaleString()} Monte Carlo simulations completed in{' '}
          <span className="text-brand-400 font-medium">{simSummary.elapsed_seconds}s</span> across{' '}
          <span className="text-brand-400 font-medium">{simSummary.num_containers}</span> parallel containers on Modal
        </p>
      </div>

      {/* Follow-up Input */}
      <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 card-glow">
        <h3 className="text-lg font-semibold text-white mb-3">🔄 Ask a Follow-up</h3>
        <p className="text-gray-400 text-sm mb-3">
          The system remembers all prior research. Only simulation + evaluation will re-run.
        </p>
        <form onSubmit={handleFollowup} className="flex gap-3">
          <input
            type="text"
            value={followupPrompt}
            onChange={(e) => setFollowupPrompt(e.target.value)}
            placeholder="What if rent increases 20%?"
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white 
                       placeholder-gray-500 focus:outline-none focus:border-brand-500 text-sm"
          />
          <button
            type="submit"
            disabled={!followupPrompt.trim()}
            className="bg-brand-600 hover:bg-brand-500 disabled:bg-gray-700 
                       disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium"
          >
            Re-analyze
          </button>
        </form>
      </div>
    </motion.div>
  )
}

function BigMetricCard({ label, value, color, bgColor, borderColor }: {
  label: string; value: string; color: string; bgColor: string; borderColor: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`${bgColor} border ${borderColor} rounded-xl p-4 text-center`}
    >
      <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </motion.div>
  )
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-1 border-b border-gray-800/50">
      <span className="text-gray-400">{label}</span>
      <span className="text-white font-medium">{value}</span>
    </div>
  )
}
