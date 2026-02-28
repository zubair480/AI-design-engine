import { useState } from 'react'
import { motion } from 'framer-motion'

interface PromptInputProps {
  onSubmit: (prompt: string) => void
  isLoading: boolean
}

const EXAMPLE_PROMPTS = [
  'Design a profitable coffee shop in Urbana, IL',
  'Evaluate a warehouse distribution center in suburban Chicago',
  'Should I open a food truck in downtown Austin?',
  'Analyze a co-working space in downtown Denver',
]

export default function PromptInput({ onSubmit, isLoading }: PromptInputProps) {
  const [prompt, setPrompt] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (prompt.trim() && !isLoading) {
      onSubmit(prompt.trim())
    }
  }

  const handleExample = (example: string) => {
    setPrompt(example)
    if (!isLoading) {
      onSubmit(example)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="max-w-3xl mx-auto"
    >
      {/* Header */}
      <div className="text-center mb-10">
        <motion.div
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-6xl mb-4"
        >
          🧠
        </motion.div>
        <h1 className="text-4xl font-bold gradient-text mb-3">
          AI Decision Engine
        </h1>
        <p className="text-gray-400 text-lg">
          Multi-agent system with Monte Carlo simulation &bull; Powered by Qwen 2.5 on Modal
        </p>
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe a business decision to analyze..."
            className="w-full bg-gray-900 border border-gray-700 rounded-xl px-5 py-4 text-white text-lg
                       placeholder-gray-500 focus:outline-none focus:border-brand-500 focus:ring-1 
                       focus:ring-brand-500 resize-none transition-all duration-200 min-h-[100px]"
            rows={3}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!prompt.trim() || isLoading}
            className="absolute bottom-4 right-4 bg-brand-600 hover:bg-brand-500 disabled:bg-gray-700 
                       disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium 
                       transition-all duration-200 flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Analyzing...
              </>
            ) : (
              <>Analyze →</>
            )}
          </button>
        </div>
      </form>

      {/* Example chips */}
      <div className="text-center">
        <p className="text-gray-500 text-sm mb-3">Try an example:</p>
        <div className="flex flex-wrap gap-2 justify-center">
          {EXAMPLE_PROMPTS.map((example) => (
            <button
              key={example}
              onClick={() => handleExample(example)}
              disabled={isLoading}
              className="bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-gray-600 
                         text-gray-300 px-4 py-2 rounded-full text-sm transition-all duration-200
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {/* Tech badges */}
      <div className="flex justify-center gap-3 mt-8">
        {['Multi-Agent', 'Monte Carlo', 'Parallel Compute', 'Persistent Memory', 'Sandboxed Execution'].map((badge) => (
          <span
            key={badge}
            className="bg-gray-800/50 border border-gray-700/50 text-gray-400 px-3 py-1 rounded-full text-xs"
          >
            {badge}
          </span>
        ))}
      </div>
    </motion.div>
  )
}
