import { useState } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice, setCartEmails } from '../api.ts'
import { useAuth } from '../auth/AuthContext.ts'
import { useCart } from '../cart/CartContext.ts'
import type { CartLine } from '../types.ts'

const MAX_PER_LINE = 10

function CartRow({ line }: { line: CartLine }) {
  const { setQuantity, remove } = useCart()
  const [busy, setBusy] = useState(false)
  const unavailable = line.status === 'sold_out' || line.status === 'unavailable'
  const max = Math.min(line.in_stock, MAX_PER_LINE)

  async function change(quantity: number) {
    setBusy(true)
    await setQuantity(line.product_id, line.size, quantity)
    setBusy(false)
  }

  return (
    <li className={unavailable ? 'cart-row unavailable' : 'cart-row'}>
      <Link to={`/products/${line.product_id}`} className="cart-row-image">
        <img src={line.image_url} alt={line.name} />
      </Link>
      <div className="cart-row-info">
        <Link to={`/products/${line.product_id}`} className="cart-row-name">
          {line.name}
        </Link>
        <p className="muted small">
          Size {line.size} · {formatPrice(line.price)} each
        </p>
        {line.note && <p className={unavailable ? 'cart-note bad' : 'cart-note'}>{line.note}</p>}
        <button
          type="button"
          className="link-button"
          onClick={() => void remove(line.product_id, line.size)}
          disabled={busy}
        >
          Remove
        </button>
      </div>
      <div className="cart-row-qty">
        {!unavailable && (
          <div className="stepper" aria-label={`Quantity of ${line.name}, size ${line.size}`}>
            <button
              type="button"
              onClick={() => void change(line.quantity - 1)}
              disabled={busy}
              aria-label="One fewer"
            >
              −
            </button>
            <span aria-live="polite">{line.quantity}</span>
            <button
              type="button"
              onClick={() => void change(line.quantity + 1)}
              disabled={busy || line.quantity >= max}
              aria-label="One more"
            >
              +
            </button>
          </div>
        )}
      </div>
      <p className="cart-row-total">{unavailable ? '—' : formatPrice(line.line_total)}</p>
    </li>
  )
}

export default function CartPage() {
  const { user, updateUser } = useAuth()
  const { cart, ready } = useCart()
  const [savingPref, setSavingPref] = useState(false)

  async function toggleReminders(enabled: boolean) {
    setSavingPref(true)
    try {
      updateUser(await setCartEmails(enabled))
    } finally {
      setSavingPref(false)
    }
  }

  if (!ready) {
    return <p className="section container muted">Loading your cart…</p>
  }

  if (cart.lines.length === 0) {
    return (
      <section className="section container cart-empty">
        <h1>Your cart is empty</h1>
        <p className="muted">Find something you like and tap Add to cart, or ask the chat for ideas.</p>
        <Link to="/products?category=all" className="btn btn-primary">
          Shop all products
        </Link>
      </section>
    )
  }

  return (
    <section className="section container">
      <div className="page-head">
        <h1>Your cart</h1>
        <p className="muted">
          {user
            ? 'Saved to your account, so it’ll be here next time you log in.'
            : 'Saved in this browser. Log in to keep it with your account.'}
        </p>
      </div>

      <div className="cart-layout">
        <ul className="cart-list">
          {cart.lines.map((line) => (
            <CartRow key={`${line.product_id}-${line.size}`} line={line} />
          ))}
        </ul>

        <aside className="cart-summary">
          <h2>Summary</h2>
          <p className="cart-summary-row">
            <span>
              {cart.item_count} {cart.item_count === 1 ? 'item' : 'items'}
            </span>
            <strong>{formatPrice(cart.subtotal)}</strong>
          </p>
          <p className="muted small">Prices and stock are checked live. Shipping and tax are added at checkout.</p>
          {cart.has_problems && (
            <p className="notice notice-error">Some items changed since you added them. Check the notes above.</p>
          )}
          <button type="button" className="btn btn-primary btn-block" disabled>
            Checkout coming soon
          </button>
          <p className="muted small">
            Ready to order now? Email{' '}
            <a href="mailto:orderdept@campuscustoms.com">orderdept@campuscustoms.com</a>, call (475) 301-4205, or
            stop by 57 Broadway.
          </p>

          {user ? (
            <label className="reminder-toggle">
              <input
                type="checkbox"
                checked={user.cart_emails}
                disabled={savingPref}
                onChange={(event) => void toggleReminders(event.target.checked)}
              />
              <span>Email me a reminder if I leave items in my cart.</span>
            </label>
          ) : (
            <p className="muted small">
              <Link to="/login">Log in</Link> to save your cart and get a reminder if you leave something behind.
            </p>
          )}
        </aside>
      </div>
    </section>
  )
}
