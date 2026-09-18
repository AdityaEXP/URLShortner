import { useCallback, useState } from 'react'
import { useLocalStorage } from './hooks/useLocalStorage'
import AuthView from './components/AuthView'
import Dashboard from './components/Dashboard'
import Toast from './components/Toast'

export default function App() {
  const [token, setToken] = useLocalStorage('token', null)
  const [toast, setToast] = useState(null)

  const showToast = useCallback((message, type) => {
    setToast({ message, type })
  }, [])

  function handleLogout() {
    setToken(null)
  }

  return (
    <>
      <Toast toast={toast} onClear={() => setToast(null)} />
      {token ? (
        <Dashboard
          token={token}
          onLogout={handleLogout}
          showToast={showToast}
        />
      ) : (
        <AuthView onAuthenticated={setToken} showToast={showToast} />
      )}
    </>
  )
}
