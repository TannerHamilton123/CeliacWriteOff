import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import ReCAPTCHA from 'react-google-recaptcha'
import { useAuth } from '../context/AuthContext'
import { passwordIssues } from '../utils/passwordPolicy'
import './Pages.css'

const RECAPTCHA_SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY

function Signup() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [recaptchaToken, setRecaptchaToken] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const issues = passwordIssues(password)
  const passwordsMatch = password.length > 0 && password === confirmPassword

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    if (issues.length > 0) {
      setError('Password does not meet the requirements below')
      return
    }
    if (!passwordsMatch) {
      setError('Passwords do not match')
      return
    }
    if (RECAPTCHA_SITE_KEY && !recaptchaToken) {
      setError('Please complete the CAPTCHA')
      return
    }

    setSubmitting(true)
    try {
      await signup(fullName, email, password, confirmPassword, recaptchaToken ?? '')
      navigate('/add-items')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign up failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page auth-page">
      <h1>Sign up</h1>
      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Full name
          <input
            type="text"
            value={fullName}
            onChange={e => setFullName(e.target.value)}
            required
            autoComplete="name"
          />
        </label>
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
            autoComplete="new-password"
          />
        </label>
        {password.length > 0 && (
          <ul className="password-hints">
            {issues.map(issue => (
              <li key={issue} className="password-hint-unmet">✗ {issue}</li>
            ))}
            {issues.length === 0 && <li className="password-hint-met">✓ Strong password</li>}
          </ul>
        )}
        <label>
          Confirm password
          <input
            type="password"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            required
            autoComplete="new-password"
          />
        </label>
        {RECAPTCHA_SITE_KEY && (
          <div className="recaptcha-wrap">
            <ReCAPTCHA sitekey={RECAPTCHA_SITE_KEY} onChange={setRecaptchaToken} />
          </div>
        )}
        {error && <p className="error-text">{error}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Signing up…' : 'Sign up'}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  )
}

export default Signup
