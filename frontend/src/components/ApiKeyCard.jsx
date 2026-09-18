import { useState } from 'react'
import { KeyRound, Copy, Check } from 'lucide-react'
import * as api from '../api'

export default function ApiKeyCard({ token, showToast }) {
  const [apiKey, setApiKey] = useState(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  async function handleGenerate() {
    setLoading(true)
    try {
      const data = await api.generateApiKey(token)
      setApiKey(data.api_key)
      setCopied(false)
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  function handleCopy() {
    navigator.clipboard.writeText(apiKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-1">
        <KeyRound size={18} className="text-indigo-400" />
        <h2 className="font-semibold text-white">API Key</h2>
      </div>
      <p className="text-sm text-gray-500 mb-4">
        Only needed for deleting links from a script instead of this dashboard.
      </p>

      <button
        onClick={handleGenerate}
        disabled={loading}
        className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white text-sm font-medium transition-colors"
      >
        Generate New Key
      </button>

      {apiKey && (
        <div className="mt-4 flex items-center justify-between gap-3 p-3 rounded-lg bg-yellow-500/5 border border-yellow-600/30">
          <div>
            <p className="text-xs text-yellow-500 mb-1">Save this now, it won't be shown again</p>
            <code className="text-sm text-yellow-200 break-all">{apiKey}</code>
          </div>
          <button
            onClick={handleCopy}
            className="shrink-0 p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors"
          >
            {copied ? <Check size={16} className="text-emerald-400" /> : <Copy size={16} />}
          </button>
        </div>
      )}
    </div>
  )
}
