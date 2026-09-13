import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

const API_URL = import.meta.env.VITE_API_URL

export interface User {
  id: string
  email: string
  created_at: string
}

interface AuthContextValue {
  user: User | null
  loading: boolean
  signup: (email: string, password: string) => Promise<void>
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

async function parseJson(response: Response) {
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail || `Request failed (${response.status})`)
  }
  return response.json()
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_URL}/auth/me`, { credentials: 'include' })
      .then(response => (response.ok ? response.json() : null))
      .then(setUser)
      .finally(() => setLoading(false))
  }, [])

  async function signup(email: string, password: string): Promise<void> {
    const response = await fetch(`${API_URL}/auth/signup`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    setUser(await parseJson(response))
  }

  async function login(email: string, password: string): Promise<void> {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    setUser(await parseJson(response))
  }

  async function logout(): Promise<void> {
    await fetch(`${API_URL}/auth/logout`, { method: 'POST', credentials: 'include' })
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, signup, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
