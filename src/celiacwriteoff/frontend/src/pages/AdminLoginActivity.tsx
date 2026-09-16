import { useEffect, useState } from 'react'
import './Pages.css'

const API_URL = import.meta.env.VITE_API_URL
const PAGE_SIZE = 25

interface LoginAttempt {
  id: string
  email: string
  user_id: string | null
  success: boolean
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

function AdminLoginActivity() {
  const [attempts, setAttempts] = useState<LoginAttempt[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [emailFilter, setEmailFilter] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const params = new URLSearchParams({
      limit: String(PAGE_SIZE),
      offset: String(offset),
    })
    if (emailFilter) params.set('email', emailFilter)

    setLoading(true)
    fetch(`${API_URL}/admin/login-attempts?${params}`, { credentials: 'include' })
      .then(async response => {
        if (!response.ok) {
          const body = await response.json().catch(() => null)
          throw new Error(body?.detail || `Request failed (${response.status})`)
        }
        return response.json()
      })
      .then(data => {
        setAttempts(data.attempts)
        setTotal(data.total)
        setError(null)
      })
      .catch(err => setError(err instanceof Error ? err.message : 'Failed to load login activity'))
      .finally(() => setLoading(false))
  }, [offset, emailFilter])

  return (
    <div className="page">
      <h1>Login activity</h1>
      <label>
        Filter by email
        <input
          type="text"
          value={emailFilter}
          onChange={e => {
            setEmailFilter(e.target.value)
            setOffset(0)
          }}
          placeholder="user@example.com"
        />
      </label>
      {error && <p className="error-text">{error}</p>}
      {loading ? (
        <p>Loading…</p>
      ) : (
        <>
          <div className="line-items-table-wrap">
            <table className="line-items-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Email</th>
                  <th>Result</th>
                  <th>IP address</th>
                  <th>User agent</th>
                </tr>
              </thead>
              <tbody>
                {attempts.map(attempt => (
                  <tr key={attempt.id}>
                    <td>{attempt.created_at}</td>
                    <td>{attempt.email}</td>
                    <td>{attempt.success ? 'Success' : 'Failed'}</td>
                    <td>{attempt.ip_address ?? '—'}</td>
                    <td>{attempt.user_agent ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="item-actions">
            <button
              type="button"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              Previous
            </button>
            <button
              type="button"
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Next
            </button>
            <span>
              {total === 0 ? 0 : offset + 1}-{Math.min(offset + PAGE_SIZE, total)} of {total}
            </span>
          </div>
        </>
      )}
    </div>
  )
}

export default AdminLoginActivity
