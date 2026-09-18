import { useEffect } from 'react'
import { CheckCircle2, XCircle } from 'lucide-react'

export default function Toast({ toast, onClear }) {
  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(onClear, 3500)
    return () => clearTimeout(timer)
  }, [toast, onClear])

  if (!toast) return null

  const isError = toast.type === 'error'

  return (
    <div
      className={`fixed top-5 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-3 rounded-xl border shadow-lg backdrop-blur-sm text-sm font-medium ${
        isError
          ? 'bg-red-950/90 border-red-800 text-red-200'
          : 'bg-emerald-950/90 border-emerald-800 text-emerald-200'
      }`}
    >
      {isError ? <XCircle size={18} /> : <CheckCircle2 size={18} />}
      {toast.message}
    </div>
  )
}
