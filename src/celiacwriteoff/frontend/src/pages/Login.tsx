import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import ReCAPTCHA from 'react-google-recaptcha'
import { useAuth } from '../context/AuthContext'
import './Pages.css'

const RECAPTCHA_SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY

function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const successMessage = (location.state as { message?: string } | null)?.message
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [recaptchaToken, setRecaptchaToken] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    if (RECAPTCHA_SITE_KEY && !recaptchaToken) {
      setError('Please complete the CAPTCHA')
      return
    }

    setSubmitting(true)
    try {
      await login(email, password, recaptchaToken ?? '')
      navigate('/add-items')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page auth-page">
      <h1>Log in</h1>
      {successMessage && <p>{successMessage}</p>}
      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </label>
        {RECAPTCHA_SITE_KEY && (
          <div className="recaptcha-wrap">
            <ReCAPTCHA sitekey={RECAPTCHA_SITE_KEY} onChange={setRecaptchaToken} />
          </div>
        )}
        {error && <p className="error-text">{error}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Logging in…' : 'Log in'}
        </button>
      </form>
      <p>
        Don't have an account? <Link to="/signup">Sign up</Link>
      </p>
      <p>
        <Link to="/forgot-password">Forgot your password?</Link>
      </p>
    </div>
  )
}

export default Login
