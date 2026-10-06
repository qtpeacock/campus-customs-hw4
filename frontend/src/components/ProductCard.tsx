import { useState } from 'react'
import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice } from '../api.ts'
import { useCart } from '../cart/CartContext.ts'

const SIZE_ORDER = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
const LOW_STOCK = 3 // badge threshold on cards ("Only 2 left in M")

/** The fields every card needs; catalogue products and chat matches both have them. */
interface CardProduct {
  product_id: string
  name: string
  garment_type: string
  price: number
  image_url: string
  extra_images?: string[]
  /** Units per size; when present the card shows a stock badge and offers Quick add. */
  stock?: Record<string, number>
}

interface ProductCardProps {
  product: CardProduct
  /** Short text under the price (clamped to two lines). */
  info: string
  /** When given, shows the sizes in stock as small chips. */
  sizesInStock?: string[]
  /** Cards the chat just put on the page animate in, staggered by position. */
  fromChat?: boolean
  index?: number
}

/** One honest badge from live stock, most urgent first. */
function stockBadge(stock: Record<string, number> | undefined): string | null {
  if (!stock) return null
  const sizes = SIZE_ORDER.filter((size) => size in stock)
  const inStock = sizes.filter((size) => stock[size] > 0)
  if (sizes.length && inStock.length === 0) return 'Sold out'
  const lowest = inStock.reduce<string | null>((low, size) => (low === null || stock[size] < stock[low] ? size : low), null)
  if (lowest && stock[lowest] <= LOW_STOCK) return `Only ${stock[lowest]} left in ${lowest}`
  const soldOut = sizes.filter((size) => stock[size] === 0)
  if (soldOut.length > 2) return 'Limited sizes'
  if (soldOut.length) return `Sold out in ${soldOut.join(', ')}`
  return null
}

function QuickAdd({ product }: { product: CardProduct }) {
  const { add } = useCart()
  const [open, setOpen] = useState(false)
  const [state, setState] = useState<{ ok: boolean; text: string } | null>(null)
  const sizes = SIZE_ORDER.filter((size) => (product.stock?.[size] ?? 0) > 0)
  if (!sizes.length) return null

  async function addSize(size: string) {
    const result = await add(product.product_id, size, 1)
    setState({ ok: result.ok, text: result.ok ? `Added ${size} ✓` : result.message })
    setOpen(false)
    window.setTimeout(() => setState(null), 2200)
  }

  return (
    <div className={open ? 'quick-add open' : 'quick-add'}>
      {state ? (
        <p className={state.ok ? 'quick-add-done' : 'quick-add-done error'} role="status">
          {state.text}
        </p>
      ) : open ? (
        <div className="quick-add-sizes" role="group" aria-label={`Choose a size of ${product.name}`}>
          {sizes.map((size) => (
            <button key={size} type="button" onClick={() => void addSize(size)}>
              {size}
            </button>
          ))}
          <button type="button" className="quick-add-close" onClick={() => setOpen(false)} aria-label="Close sizes">
            ×
          </button>
        </div>
      ) : (
        <button type="button" className="quick-add-button" onClick={() => setOpen(true)}>
          Quick add <span aria-hidden="true">+</span>
        </button>
      )}
    </div>
  )
}

export default function ProductCard({ product, info, sizesInStock, fromChat = false, index = 0 }: ProductCardProps) {
  const style = fromChat ? ({ '--delay': `${Math.min(index, 14) * 45}ms` } as CSSProperties) : undefined
  const badge = stockBadge(product.stock)
  const altImage = product.extra_images?.[0]
  const classes = ['product-card', fromChat && 'from-chat', altImage && 'has-alt'].filter(Boolean).join(' ')

  return (
    <div className={classes} style={style}>
      {/* Every card, including ones the chat adds, opens the same single-item page. */}
      <Link to={`/products/${product.product_id}`} className="product-card-link">
        <div className="product-card-image">
          <img src={product.image_url} alt={product.name} loading="lazy" className="card-img primary" />
          {/* Loaded up front (only a couple of products have one) so the hover swap is instant. */}
          {altImage && <img src={altImage} alt="" className="card-img alt" aria-hidden="true" />}
          {badge && <span className={badge.startsWith('Only') ? 'card-badge urgent' : 'card-badge'}>{badge}</span>}
          {altImage && <span className="card-badge worn">Worn on campus</span>}
        </div>
        <div className="product-card-body">
          <p className="product-card-type">{product.garment_type}</p>
          <h3 className="product-card-name">{product.name}</h3>
          <p className="product-card-price">{formatPrice(product.price)}</p>
          <p className="product-card-desc">{info}</p>
          {sizesInStock && (
            <div className="card-sizes" aria-label={`Sizes in stock: ${sizesInStock.join(', ') || 'none'}`}>
              {sizesInStock.length > 0 ? (
                sizesInStock.map((size) => (
                  <span key={size} className="card-size">
                    {size}
                  </span>
                ))
              ) : (
                <span className="card-size sold-out">Sold out</span>
              )}
            </div>
          )}
        </div>
      </Link>
      {product.stock && <QuickAdd product={product} />}
    </div>
  )
}

/** Gray shimmering stand-in shown while products load. */
export function ProductCardSkeleton() {
  return (
    <div className="product-card skeleton" aria-hidden="true">
      <div className="product-card-image shimmer" />
      <div className="product-card-body">
        <span className="shimmer line short" />
        <span className="shimmer line" />
        <span className="shimmer line tiny" />
        <span className="shimmer line" />
      </div>
    </div>
  )
}
