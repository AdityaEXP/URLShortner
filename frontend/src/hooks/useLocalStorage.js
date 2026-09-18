import { useEffect, useState } from 'react'

export function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(() => {
    const stored = localStorage.getItem(key)
    if (stored === null) return initialValue
    try {
      return JSON.parse(stored)
    } catch {
      return stored
    }
  })

  useEffect(() => {
    if (value === null || value === undefined) {
      localStorage.removeItem(key)
    } else {
      localStorage.setItem(key, typeof value === 'string' ? value : JSON.stringify(value))
    }
  }, [key, value])

  return [value, setValue]
}
