import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useCart } from '../cart/CartContext.ts'
import type { CartResult } from '../cart/CartContext.ts'
import type { ProductDetail, SizeStock } from '../types.ts'

const LOW_STOCK = 5
const MAX_PER_LINE = 10

function stockLabel({ quantity }: SizeStock): string {
  if (quantity === 0) return 'Sold out'
  if (quantity <= LOW_STOCK) return `Only ${quantity} left`
  return 'In stock'
}

function chipClass(size: SizeStock, selected: boolean): string {
  const classes = ['size-chip']
  if (size.quantity === 0) classes.push('sold-out')
  else if (size.quantity <= LOW_STOCK) classes.push('low')
  if (selected) classes.push('selected')
  return classes.join(' ')
}

/** Size picker, quantity, and Add to cart for the single-item page. Stock rules are checked again by the backend. */
export default function AddToCart({ product }: { product: ProductDetail }) {
  const { add, cart } = useCart()
  const [size, setSize] = useState<string | null>(null)
  const [quantity, setQuantity] = useState(1)
  const [result, setResult] = useState<CartResult | null>(null)
  const [busy, setBusy] = useState(false)

  const selected = product.sizes.find((s) => s.size === size)
  const inCart = cart.lines.find((l) => l.product_id === product.product_id && l.size === size)?.quantity ?? 0
  const maxQuantity = Math.max(1, Math.min((selected?.quantity ?? 1) - inCart, MAX_PER_LINE - inCart))
  const canAdd = !!selected && selected.quantity > inCart && inCart < MAX_PER_LINE

  function choose(next: SizeStock) {
    setSize(next.size)
    setQuantity(1)
    setResult(null)
  }

  async function handleAdd() {
    if (!selected) {
      setResult({ ok: false, message: 'Pick a size first.' })
      return
    }
    setBusy(true)
    setResult(await add(product.product_id, selected.size, quantity))
    setBusy(false)
  }

  return (
    <div className="add-to-cart">
      <ul className="size-grid" aria-label="Choose a size">
        {product.sizes.map((s) => (
          <li key={s.size}>
            <button
              type="button"
              className={chipClass(s, s.size === size)}
              disabled={s.quantity === 0}
              aria-pressed={s.size === size}
              onClick={() => choose(s)}
            >
              <span className="size-name">{s.size}</span>
              <span className="size-stock">{stockLabel(s)}</span>
            </button>
          </li>
        ))}
      </ul>

      <div className="cart-controls">
        <label className="qty-control">
          <span>Qty</span>
          <select
            value={quantity}
            onChange={(event) => setQuantity(Number(event.target.value))}
            disabled={!canAdd}
          >
            {Array.from({ length: maxQuantity }, (_, i) => i + 1).map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="btn btn-primary add-button" onClick={() => void handleAdd()} disabled={busy}>
          {busy ? 'Adding…' : size ? `Add ${size} to cart` : 'Choose a size'}
        </button>
      </div>

      {selected && inCart > 0 && !result && (
        <p className="muted small">
          You already have {inCart} in {selected.size} in your cart.
        </p>
      )}
      {result && (
        <p className={result.ok ? 'notice' : 'notice notice-error'} role="status">
          {result.message} {result.ok && <Link to="/cart">View cart →</Link>}
        </p>
      )}
    </div>
  )
}
