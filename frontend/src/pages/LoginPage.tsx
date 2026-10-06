import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.ts'

export default function LoginPage() {
  const { user, login, logout } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(email, password)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
      setPassword('')
    } finally {
      setSubmitting(false)
    }
  }

  if (user) {
    return (
      <section className="section container auth-wrap">
        <div className="auth-card">
          <h1>You're logged in</h1>
          <p className="muted">
            Signed in as {user.first_name} {user.last_name} ({user.email}).
          </p>
          <div className="auth-actions">
            <Link to="/products" className="btn btn-primary">
              Keep shopping
            </Link>
            <button type="button" className="btn btn-outline" onClick={() => void logout()}>
              Log out
            </button>
          </div>
        </div>
      </section>
    )
  }

  return (
    <section className="section container auth-wrap">
      <div className="auth-card">
        <h1>Log in</h1>
        <p className="muted">Welcome back. Log in to pick up your chat where you left off.</p>

        <form className="form" onSubmit={handleSubmit}>
          <label htmlFor="login-email">Email</label>
          <input
            id="login-email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />

          <label htmlFor="login-password">Password</label>
          <input
            id="login-password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          {error && (
            <p className="notice notice-error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? 'Logging in…' : 'Log in'}
          </button>
        </form>

        <p className="muted small">
          New here? <Link to="/create-account">Create an account</Link>
        </p>
      </div>
    </section>
  )
}
