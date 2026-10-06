import { useEffect, useState } from 'react'
import { draftCartReminders, fetchOutbox } from '../api.ts'
import type { OutboxEmail } from '../types.ts'

const IDLE_CHOICES = [
  { hours: 0, label: 'Any idle cart (demo)' },
  { hours: 1, label: 'Idle 1+ hour' },
  { hours: 24, label: 'Idle 24+ hours' },
]

/**
 * Staff page: preview the cart reminder emails drafted in email_outbox. Nothing here is sent.
 * The backend only allows it from the shop's own computer (or with an ADMIN_TOKEN).
 */
export default function OutboxPage() {
  const [emails, setEmails] = useState<OutboxEmail[]>([])
  const [status, setStatus] = useState<'loading' | 'ready' | 'denied'>('loading')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetchOutbox()
      .then((list) => {
        setEmails(list)
        setStatus('ready')
      })
      .catch(() => setStatus('denied'))
  }, [])

  async function draft(hours: number) {
    setBusy(true)
    setMessage('')
    try {
      const drafted = await draftCartReminders(hours)
      setMessage(
        drafted.length
          ? `Drafted ${drafted.length} reminder${drafted.length === 1 ? '' : 's'}.`
          : 'No carts need a reminder right now (each cart gets one reminder until it changes).',
      )
      setEmails(await fetchOutbox())
    } catch {
      setMessage('Could not draft reminders. Is the chat model configured?')
    } finally {
      setBusy(false)
    }
  }

  if (status === 'denied') {
    return (
      <section className="section container">
        <h1>Email outbox</h1>
        <p className="notice notice-error">Staff only. This page works on the shop’s own computer.</p>
      </section>
    )
  }

  return (
    <section className="section container">
      <div className="page-head">
        <h1>Email outbox</h1>
        <p className="muted">
          Cart reminders drafted for shoppers who opted in and left items in their cart. These are drafts only;
          nothing is emailed until an email service is connected.
        </p>
      </div>

      <div className="outbox-actions">
        <span className="small">Draft reminders for:</span>
        {IDLE_CHOICES.map((choice) => (
          <button
            key={choice.hours}
            type="button"
            className="btn btn-outline"
            onClick={() => void draft(choice.hours)}
            disabled={busy}
          >
            {choice.label}
          </button>
        ))}
      </div>
      {message && (
        <p className="notice" role="status">
          {message}
        </p>
      )}

      {status === 'loading' && <p className="muted">Loading the outbox…</p>}
      {status === 'ready' && emails.length === 0 && <p className="muted">No drafts yet.</p>}
      <ul className="outbox-list">
        {emails.map((email) => (
          <li key={email.id} className="outbox-email">
            <div className="outbox-meta">
              <span className="outbox-status">{email.status}</span>
              <span>To: {email.to_email}</span>
              <span className="muted small">{email.created_at} UTC</span>
            </div>
            <p className="outbox-subject">{email.subject}</p>
            <pre className="outbox-body">{email.body}</pre>
          </li>
        ))}
      </ul>
    </section>
  )
}
