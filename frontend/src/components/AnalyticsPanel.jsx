import { useCallback, useEffect, useState } from 'react'
import { RefreshCw, TrendingUp } from 'lucide-react'
import * as api from '../api'

export default function AnalyticsPanel() {
  const [topLinks, setTopLinks] = useState([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.fetchAnalytics()
      setTopLinks(data)
    } catch {
      setTopLinks([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const maxClicks = Math.max(1, ...topLinks.map((item) => item.click_count))

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TrendingUp size={18} className="text-indigo-400" />
          <h2 className="font-semibold text-white">Top 5 Links</h2>
        </div>
        <button
          onClick={load}
          className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {topLinks.length === 0 ? (
        <p className="text-sm text-gray-600 py-4 text-center">No clicks yet</p>
      ) : (
        <div className="space-y-3">
          {topLinks.map((item) => (
            <div key={item.short_code}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-300">{item.short_code}</span>
                <span className="text-gray-500">{item.click_count} clicks</span>
              </div>
              <div className="h-1.5 rounded-full bg-gray-800 overflow-hidden">
                <div
                  className="h-full bg-indigo-500 rounded-full transition-all"
                  style={{ width: `${(item.click_count / maxClicks) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
