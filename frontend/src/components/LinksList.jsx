import { useState } from 'react'
import { ExternalLink, BarChart3, Trash2, Link2Off } from 'lucide-react'
import * as api from '../api'

export default function LinksList({ token, links, onDelete, showToast }) {
  const [statsByCode, setStatsByCode] = useState({})
  const [deletingCode, setDeletingCode] = useState(null)

  async function handleShowStats(code) {
    try {
      const stats = await api.fetchStats(code)
      setStatsByCode((prev) => ({ ...prev, [code]: stats }))
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  async function handleDelete(code) {
    setDeletingCode(code)
    try {
      await api.deleteShortLink(token, code)
      onDelete(code)
      showToast('Link deleted', 'success')
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setDeletingCode(null)
    }
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <h2 className="font-semibold text-white mb-4">Your Links</h2>

      {links.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8 text-gray-600">
          <Link2Off size={28} />
          <p className="text-sm">No links yet, create one above</p>
        </div>
      ) : (
        <div className="space-y-2">
          {links.map((link) => {
            const stats = statsByCode[link.short_code]
            return (
              <div
                key={link.short_code}
                className="flex items-center justify-between gap-3 p-3 rounded-xl bg-gray-800/60 border border-gray-800"
              >
                <div className="min-w-0">
                  <a
                    href={link.short_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1.5 text-indigo-400 hover:text-indigo-300 text-sm font-medium truncate"
                  >
                    {link.short_url}
                    <ExternalLink size={13} className="shrink-0" />
                  </a>
                  {stats && (
                    <p className="text-xs text-gray-500 mt-1">
                      {stats.click_count} clicks · created {new Date(stats.created_at).toLocaleString()}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleShowStats(link.short_code)}
                    className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors"
                    title="Stats"
                  >
                    <BarChart3 size={15} />
                  </button>
                  <button
                    onClick={() => handleDelete(link.short_code)}
                    disabled={deletingCode === link.short_code}
                    className="p-2 rounded-lg bg-red-950 hover:bg-red-900 text-red-400 disabled:opacity-50 transition-colors"
                    title="Delete"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
