import { useState } from 'react'
import { Link2, Loader2 } from 'lucide-react'
import * as api from '../api'

export default function AuthView({ onAuthenticated, showToast }) {
  const [mode, setMode] = useState('login')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ username: '', email: '', password: '' })

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)

    try {
      const data =
        mode === 'login'
          ? await api.login(form.email, form.password)
          : await api.signup(form.username, form.email, form.password)

      onAuthenticated(data.access_token)
      showToast(mode === 'login' ? 'Logged in' : 'Account created', 'success')
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-2 mb-8">
          <div className="p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
            <Link2 className="text-indigo-400" size={28} />
          </div>
          <h1 className="text-2xl font-semibold text-white">URL Shortener</h1>
          <p className="text-sm text-gray-500">Shorten, track, and manage your links</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl shadow-black/20">
          <div className="flex p-1 mb-6 rounded-xl bg-gray-800/70">
            <button
              type="button"
              onClick={() => setMode('login')}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                mode === 'login' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              Log In
            </button>
            <button
              type="button"
              onClick={() => setMode('signup')}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                mode === 'signup' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              Sign Up
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            {mode === 'signup' && (
              <input
                type="text"
                required
                placeholder="Username"
                value={form.username}
                onChange={(e) => updateField('username', e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-gray-800 border border-gray-700 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            )}
            <input
              type="email"
              required
              placeholder="Email"
              value={form.email}
              onChange={(e) => updateField('email', e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg bg-gray-800 border border-gray-700 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <input
              type="password"
              required
              placeholder={mode === 'signup' ? 'Password (min 8 chars)' : 'Password'}
              value={form.password}
              onChange={(e) => updateField('password', e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg bg-gray-800 border border-gray-700 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white text-sm font-medium transition-colors"
            >
              {loading && <Loader2 size={16} className="animate-spin" />}
              {mode === 'login' ? 'Log In' : 'Create Account'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
