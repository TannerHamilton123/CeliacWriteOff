import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { passwordIssues } from '../utils/passwordPolicy'
import './Pages.css'

function ResetPassword() {
  const { resetPassword } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const issues = passwordIssues(newPassword)
  const passwordsMatch = newPassword.length > 0 && newPassword === confirmPassword

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

    setSubmitting(true)
    try {
      const message = await resetPassword(token, newPassword, confirmPassword)
      navigate('/login', { state: { message } })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  if (!token) {
    return (
      <div className="page auth-page">
        <h1>Reset password</h1>
        <p className="error-text">This reset link is missing its token.</p>
        <p>
          <Link to="/forgot-password">Request a new reset link</Link>
        </p>
      </div>
    )
  }

  return (
    <div className="page auth-page">
      <h1>Reset password</h1>
      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          New password
          <input
            type="password"
            value={newPassword}
            onChange={e => setNewPassword(e.target.value)}
            required
            autoComplete="new-password"
          />
        </label>
        {newPassword.length > 0 && (
          <ul className="password-hints">
            {issues.map(issue => (
              <li key={issue} className="password-hint-unmet">✗ {issue}</li>
            ))}
            {issues.length === 0 && <li className="password-hint-met">✓ Strong password</li>}
          </ul>
        )}
        <label>
          Confirm new password
          <input
            type="password"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            required
            autoComplete="new-password"
          />
        </label>
        {error && <p className="error-text">{error}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Resetting…' : 'Reset password'}
        </button>
      </form>
    </div>
  )
}

export default ResetPassword
