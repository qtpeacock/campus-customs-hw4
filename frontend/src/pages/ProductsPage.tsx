import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { fetchProducts } from '../api.ts'
import {
  CATEGORIES,
  COLLECTIONS,
  SORT_OPTIONS,
  categoryBySlug,
  collectionBySlug,
  sortKey,
  sortProducts,
} from '../catalog.ts'
import type { SortKey } from '../catalog.ts'
import { useChatPage } from '../chat/ChatPageContext.ts'
import ChatResults from '../components/ChatResults.tsx'
import ProductCard, { ProductCardSkeleton } from '../components/ProductCard.tsx'
import type { Product } from '../types.ts'

export default function ProductsPage() {
  const { results, resultsKey, clearResults, setChatOpen } = useChatPage()
  const [params, setParams] = useSearchParams()
  const [products, setProducts] = useState<Product[]>([])
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')

  useEffect(() => {
    fetchProducts()
      .then((data) => {
        setProducts(data)
        setStatus('ready')
      })
      .catch(() => setStatus('error'))
  }, [])

  // Browsing state lives in the URL (?category=hoodies&collection=family&sort=price-asc), so links and Back work.
  const category = categoryBySlug(params.get('category'))
  const collection = collectionBySlug(params.get('collection'))
  const sort = sortKey(params.get('sort'))
  const browsing = params.has('category') || params.has('collection') || params.has('sort')

  // Chat search results replace the catalogue until cleared, unless the shopper picked a type, collection, or sort.
  if (results && !browsing) {
    return (
      <ChatResults
        results={results}
        resultsKey={resultsKey}
        onClear={clearResults}
        onRefine={() => setChatOpen(true)}
      />
    )
  }

  function linkFor(slug: string): string {
    const next = new URLSearchParams(params)
    next.set('category', slug)
    return `/products?${next.toString()}`
  }

  function setParam(name: 'sort' | 'collection', value: string, fallback: string) {
    const next = new URLSearchParams(params)
    if (value === fallback) next.delete(name)
    else next.set(name, value)
    if (!next.has('category')) next.set('category', 'all')
    setParams(next)
  }

  const inCollection = collection ? products.filter((p) => p.collections.includes(collection.slug)) : products
  const counts = new Map(CATEGORIES.map((c) => [c.kind, inCollection.filter((p) => p.kind === c.kind).length]))
  const shown = sortProducts(category ? inCollection.filter((p) => p.kind === category.kind) : inCollection, sort)
  // "All" in Featured order is grouped by type, like a clothing store's department view.
  const grouped = !category && sort === 'featured'
  const title = [category?.label, collection?.label].filter(Boolean).join(' · ') || 'All products'

  return (
    <section className="section container">
      <div className="page-head">
        <p className="eyebrow">{collection ? 'Collection' : category ? 'Shop by type' : 'The shop'}</p>
        <h1 className="crest-heading">{title}</h1>
        <p className="muted">
          {collection
            ? collection.blurb
            : category
              ? category.blurb
              : 'Officially licensed Yale gear, sorted by type. Click anything for sizes and details, or ask the chat to find something for you.'}
        </p>
      </div>

      <nav className="category-tabs" aria-label="Product types">
        <Link
          to={linkFor('all')}
          className={!category ? 'category-tab active' : 'category-tab'}
          aria-current={!category ? 'page' : undefined}
        >
          All <span className="category-count">{inCollection.length || ''}</span>
        </Link>
        {CATEGORIES.filter((c) => !collection || counts.get(c.kind)).map((c) => (
          <Link
            key={c.slug}
            to={linkFor(c.slug)}
            className={category?.slug === c.slug ? 'category-tab active' : 'category-tab'}
            aria-current={category?.slug === c.slug ? 'page' : undefined}
          >
            {c.label} <span className="category-count">{counts.get(c.kind) || ''}</span>
          </Link>
        ))}
      </nav>

      <div className="catalog-toolbar">
        <p className="muted" aria-live="polite">
          {status === 'ready' && `${shown.length} ${shown.length === 1 ? 'item' : 'items'}`}
        </p>
        <div className="catalog-controls">
          <label className="sort-control">
            <span>Collection</span>
            <select
              value={collection?.slug ?? 'all'}
              onChange={(event) => setParam('collection', event.target.value, 'all')}
            >
              <option value="all">All collections</option>
              {COLLECTIONS.map((c) => (
                <option key={c.slug} value={c.slug}>
                  {c.label}
                </option>
              ))}
            </select>
          </label>
          <label className="sort-control">
            <span>Sort by</span>
            <select value={sort} onChange={(event) => setParam('sort', event.target.value as SortKey, 'featured')}>
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {status === 'loading' && (
        <div className="product-grid" aria-label="Loading products">
          {Array.from({ length: 8 }, (_, i) => (
            <ProductCardSkeleton key={i} />
          ))}
        </div>
      )}
      {status === 'error' && (
        <p className="notice notice-error" role="alert">
          We couldn't load the products right now. Please refresh the page in a moment.
        </p>
      )}
      {status === 'ready' && shown.length === 0 && (
        <p className="muted">Nothing here yet. Try another type or collection.</p>
      )}

      {status === 'ready' &&
        (grouped ? (
          CATEGORIES.filter((c) => counts.get(c.kind)).map((c) => (
            <section key={c.slug} className="catalog-group" aria-labelledby={`group-${c.slug}`}>
              <div className="catalog-group-head">
                <h2 id={`group-${c.slug}`}>
                  {c.label} <span className="category-count">{counts.get(c.kind)}</span>
                </h2>
                <Link to={linkFor(c.slug)} className="text-link">
                  Shop {c.label.toLowerCase()} →
                </Link>
              </div>
              <div className="product-grid">
                {shown
                  .filter((p) => p.kind === c.kind)
                  .map((product) => (
                    <ProductCard key={product.product_id} product={product} info={product.description} />
                  ))}
              </div>
            </section>
          ))
        ) : (
          <div className="product-grid">
            {shown.map((product) => (
              <ProductCard key={product.product_id} product={product} info={product.description} />
            ))}
          </div>
        ))}
    </section>
  )
}
