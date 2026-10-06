import type { CatalogueFilters, ProductMatches } from '../types.ts'
import ProductCard from './ProductCard.tsx'

function dollars(amount: number): string {
  return amount.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: Number.isInteger(amount) ? 0 : 2,
  })
}

/** Turn the agent's search filters into readable chips, e.g. ["hoodie", "navy", "Under $70"]. */
function filterChips(filters: CatalogueFilters): string[] {
  const chips: string[] = []
  if (filters.query) chips.push(`“${filters.query}”`)
  if (filters.kind) chips.push(filters.kind)
  if (filters.color) chips.push(filters.color)
  if (filters.max_price !== null) chips.push(`Under ${dollars(filters.max_price)}`)
  if (filters.size) chips.push(`${filters.size} in stock`)
  return chips
}

function SparkIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 2l1.9 5.6L19.5 9.5l-5.6 1.9L12 17l-1.9-5.6L4.5 9.5l5.6-1.9L12 2Zm6.5 11 .9 2.6 2.6.9-2.6.9-.9 2.6-.9-2.6-2.6-.9 2.6-.9.9-2.6Z"
      />
    </svg>
  )
}

interface ChatResultsProps {
  results: ProductMatches
  resultsKey: number
  onClear: () => void
  onRefine: () => void
}

/** Search results the chat agent put on the page, rendered as product cards. */
export default function ChatResults({ results, resultsKey, onClear, onRefine }: ChatResultsProps) {
  const { title, total_matches: total, products, price_min: min, price_max: max } = results
  const chips = filterChips(results.filters)
  const priceRange = min === max ? dollars(min) : `${dollars(min)}–${dollars(max)}`

  return (
    <section className="chat-results" aria-labelledby="chat-results-title">
      {/* Keyed so the banner and cards replay their entrance when new results arrive. */}
      <div className="chat-results-banner" key={`banner-${resultsKey}`}>
        <div className="container chat-results-inner">
          <p className="chat-results-eyebrow">
            <SparkIcon /> From your chat
          </p>
          <h1 id="chat-results-title">{title}</h1>
          <p className="chat-results-meta">
            {total} {total === 1 ? 'match' : 'matches'} · {priceRange}
            {products.length < total && ` · showing the first ${products.length}`}
          </p>
          {chips.length > 0 && (
            <ul className="chat-results-chips" aria-label="Search filters">
              {chips.map((chip) => (
                <li key={chip}>{chip}</li>
              ))}
            </ul>
          )}
          <div className="chat-results-actions">
            <button type="button" className="btn btn-light" onClick={onRefine}>
              Refine in chat
            </button>
            <button type="button" className="btn btn-outline-light" onClick={onClear}>
              Show all products
            </button>
          </div>
        </div>
      </div>

      <p className="visually-hidden" role="status">
        {`${total} ${title} now showing on the page.`}
      </p>

      <div className="section container">
        <div className="product-grid" key={`grid-${resultsKey}`}>
          {products.map((product, index) => (
            <ProductCard
              key={product.product_id}
              product={product}
              info={product.short_description}
              sizesInStock={product.sizes_in_stock}
              fromChat
              index={index}
            />
          ))}
        </div>
      </div>
    </section>
  )
}
