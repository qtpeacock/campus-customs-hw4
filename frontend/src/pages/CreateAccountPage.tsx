import { useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.ts'

const MIN_PASSWORD = 8

export default function CreateAccountPage() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ firstName: '', lastName: '', email: '', password: '', confirm: '' })
  const [cartEmails, setCartEmails] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function update(field: keyof typeof form) {
    return (event: ChangeEvent<HTMLInputElement>) => setForm({ ...form, [field]: event.target.value })
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (form.password.length < MIN_PASSWORD) {
      setError(`Your password needs at least ${MIN_PASSWORD} characters.`)
      return
    }
    if (form.password !== form.confirm) {
      setError("Those passwords don't match.")
      return
    }
    setError('')
    setSubmitting(true)
    try {
      await register({
        first_name: form.firstName,
        last_name: form.lastName,
        email: form.email,
        password: form.password,
        cart_emails: cartEmails,
      })
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (user) {
    return (
      <section className="section container auth-wrap">
        <div className="auth-card">
          <h1>You already have an account</h1>
          <p className="muted">
            You're logged in as {user.first_name} ({user.email}).
          </p>
          <Link to="/products" className="btn btn-primary">
            Keep shopping
          </Link>
        </div>
      </section>
    )
  }

  return (
    <section className="section container auth-wrap">
      <div className="auth-card">
        <h1>Create an account</h1>
        <p className="muted">It takes a minute, and the chat will remember you next time.</p>

        <form className="form" onSubmit={handleSubmit}>
          <div className="form-row">
            <div>
              <label htmlFor="signup-first">First name</label>
              <input
                id="signup-first"
                autoComplete="given-name"
                required
                maxLength={50}
                value={form.firstName}
                onChange={update('firstName')}
              />
            </div>
            <div>
              <label htmlFor="signup-last">Last name</label>
              <input
                id="signup-last"
                autoComplete="family-name"
                required
                maxLength={50}
                value={form.lastName}
                onChange={update('lastName')}
              />
            </div>
          </div>

          <label htmlFor="signup-email">Email</label>
          <input
            id="signup-email"
            type="email"
            autoComplete="email"
            required
            value={form.email}
            onChange={update('email')}
          />

          <label htmlFor="signup-password">Password</label>
          <input
            id="signup-password"
            type="password"
            autoComplete="new-password"
            required
            minLength={MIN_PASSWORD}
            maxLength={128}
            aria-describedby="password-hint"
            value={form.password}
            onChange={update('password')}
          />
          <p id="password-hint" className="hint">
            At least {MIN_PASSWORD} characters.
          </p>

          <label htmlFor="signup-confirm">Confirm password</label>
          <input
            id="signup-confirm"
            type="password"
            autoComplete="new-password"
            required
            maxLength={128}
            value={form.confirm}
            onChange={update('confirm')}
          />

          <label className="reminder-toggle">
            <input type="checkbox" checked={cartEmails} onChange={(event) => setCartEmails(event.target.checked)} />
            <span>Email me a reminder if I leave something in my cart. (Optional; you can turn it off anytime.)</span>
          </label>

          {error && (
            <p className="notice notice-error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? 'Creating your account…' : 'Create account'}
          </button>
        </form>

        <p className="muted small">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </section>
  )
}
