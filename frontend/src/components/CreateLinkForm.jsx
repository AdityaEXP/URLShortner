import { useState } from 'react'
import { Loader2, Plus } from 'lucide-react'
import * as api from '../api'

export default function CreateLinkForm({ token, onCreated, showToast }) {
  const [loading, setLoading] = useState(false)
  const [url, setUrl] = useState('')
  const [alias, setAlias] = useState('')
  const [expiry, setExpiry] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)

    try {
      const link = await api.createShortLink(token, { url, alias, expiresInMinutes: expiry })
      onCreated(link)
      setUrl('')
      setAlias('')
      setExpiry('')
      showToast('Short link created', 'success')
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <h2 className="font-semibold text-white mb-4">Create Short Link</h2>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="url"
          required
          placeholder="https://example.com/very/long/url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="w-full px-3 py-2.5 rounded-lg bg-gray-800 border border-gray-700 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
        <div className="flex gap-3">
          <input
            type="text"
            placeholder="Custom alias (optional)"
            value={alias}
            onChange={(e) => setAlias(e.target.value)}
            className="flex-1 px-3 py-2.5 rounded-lg bg-gray-800 border border-gray-700 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <input
            type="number"
            min="1"
            placeholder="Expires (min)"
            value={expiry}
            onChange={(e) => setExpiry(e.target.value)}
            className="w-36 px-3 py-2.5 rounded-lg bg-gray-800 border border-gray-700 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white text-sm font-medium transition-colors"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
          Shorten
        </button>
      </form>
    </div>
  )
}
