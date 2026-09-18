import { LogOut, Link2 } from 'lucide-react'
import ApiKeyCard from './ApiKeyCard'
import CreateLinkForm from './CreateLinkForm'
import LinksList from './LinksList'
import AnalyticsPanel from './AnalyticsPanel'

export default function Dashboard({ token, links, setLinks, onLogout, showToast }) {
  function handleCreated(link) {
    setLinks([link, ...links])
  }

  function handleDelete(code) {
    setLinks(links.filter((link) => link.short_code !== code))
  }

  return (
    <div className="min-h-screen px-4 py-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
              <Link2 className="text-indigo-400" size={20} />
            </div>
            <h1 className="text-lg font-semibold text-white">URL Shortener</h1>
          </div>
          <button
            onClick={onLogout}
            className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-red-400 transition-colors"
          >
            <LogOut size={15} />
            Log Out
          </button>
        </div>

        <ApiKeyCard token={token} showToast={showToast} />
        <CreateLinkForm token={token} onCreated={handleCreated} showToast={showToast} />
        <LinksList token={token} links={links} onDelete={handleDelete} showToast={showToast} />
        <AnalyticsPanel />
      </div>
    </div>
  )
}
