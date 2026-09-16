import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

const API_URL = import.meta.env.VITE_API_URL

export interface User {
  id: string
  email: string
  full_name: string
  is_admin: boolean
  created_at: string
}

interface AuthContextValue {
  user: User | null
  loading: boolean
  signup: (
    fullName: string,
    email: string,
    password: string,
    confirmPassword: string,
    recaptchaToken: string,
  ) => Promise<void>
  login: (email: string, password: string, recaptchaToken: string) => Promise<void>
  logout: () => Promise<void>
  forgotPassword: (email: string) => Promise<string>
  resetPassword: (token: string, newPassword: string, confirmPassword: string) => Promise<string>
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

  async function signup(
    fullName: string,
    email: string,
    password: string,
    confirmPassword: string,
    recaptchaToken: string,
  ): Promise<void> {
    const response = await fetch(`${API_URL}/auth/signup`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        full_name: fullName,
        email,
        password,
        confirm_password: confirmPassword,
        recaptcha_token: recaptchaToken,
      }),
    })
    setUser(await parseJson(response))
  }

  async function login(email: string, password: string, recaptchaToken: string): Promise<void> {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, recaptcha_token: recaptchaToken }),
    })
    setUser(await parseJson(response))
  }

  async function logout(): Promise<void> {
    await fetch(`${API_URL}/auth/logout`, { method: 'POST', credentials: 'include' })
    setUser(null)
  }

  async function forgotPassword(email: string): Promise<string> {
    const response = await fetch(`${API_URL}/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })
    const body = await parseJson(response)
    return body.message
  }

  async function resetPassword(
    token: string,
    newPassword: string,
    confirmPassword: string,
  ): Promise<string> {
    const response = await fetch(`${API_URL}/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token,
        new_password: newPassword,
        confirm_password: confirmPassword,
      }),
    })
    const body = await parseJson(response)
    return body.message
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, signup, login, logout, forgotPassword, resetPassword }}
    >
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
