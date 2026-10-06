import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts } from '../api.ts'
import { COLLECTIONS } from '../catalog.ts'
import { useChatPage } from '../chat/ChatPageContext.ts'
import HeroCarousel from '../components/HeroCarousel.tsx'
import { Seal } from '../components/Logo.tsx'
import ProductCard, { ProductCardSkeleton } from '../components/ProductCard.tsx'
import type { Product } from '../types.ts'

// A small hand-picked mix: a classic hoodie, The Game, an SOM tee, and a crewneck.
const FEATURED_IDS = [
  'basic-hoodie-big-yale',
  '2025-yale-vs-harvard-t-shirt',
  'school-of-management-crest-t-shirt',
  'champion-reverse-weave-crewneck',
]

export default function HomePage() {
  const { clearResults } = useChatPage()
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

  const featured = FEATURED_IDS.map((id) => products.find((p) => p.product_id === id)).filter(
    (p): p is Product => p !== undefined,
  )
  const byId = new Map(products.map((p) => [p.product_id, p]))

  return (
    <>
      <HeroCarousel>
        <p className="eyebrow">Yale Bulldog Blue by Campus Customs</p>
        <h1>Yale gear you'll actually wear.</h1>
        <p className="hero-copy">
          Hoodies, crewnecks, quarter-zips, and tees for game days, finals week, and everything in
          between. All of it officially licensed, from a family shop right across the street from
          campus.
        </p>
        <div className="hero-actions">
          <Link to="/products" className="btn btn-light">
            Shop everything
          </Link>
          <Link to="/about" className="btn btn-outline-light">
            Our story
          </Link>
        </div>
        <div className="hero-seal">
          <Seal size={128} light />
        </div>
      </HeroCarousel>
      <div className="varsity-stripe" aria-hidden="true" />

      <section className="section container">
        <div className="section-head">
          <div>
            <p className="eyebrow">Shop by collection</p>
            <h2 className="crest-heading">Find your corner of Yale</h2>
          </div>
          <Link to="/products?category=all" className="text-link">
            Shop all products →
          </Link>
        </div>
        <div className="collection-grid">
          {COLLECTIONS.map((collection) => {
            const cover = byId.get(collection.coverProduct)
            const count = products.filter((p) => p.collections.includes(collection.slug)).length
            return (
              <Link
                key={collection.slug}
                to={`/products?collection=${collection.slug}`}
                className="collection-tile"
                onClick={clearResults}
              >
                <span className="collection-image">
                  {cover ? <img src={cover.image_url} alt="" loading="lazy" /> : <span className="shimmer" />}
                </span>
                <span className="collection-text">
                  <span className="collection-name">{collection.label}</span>
                  <span className="collection-blurb">{collection.blurb}</span>
                  <span className="collection-cta">
                    {count ? `Shop ${count} styles` : 'Shop now'} <span aria-hidden="true">→</span>
                  </span>
                </span>
              </Link>
            )
          })}
        </div>
      </section>

      <section className="section container">
        <div className="section-head">
          <div>
            <p className="eyebrow">Staff picks</p>
            <h2 className="crest-heading">A few favorites</h2>
            <p className="muted">Not sure where to start? Start here.</p>
          </div>
          <Link to="/products" className="text-link">
            See all products →
          </Link>
        </div>
        {status === 'error' ? (
          <p className="muted">
            Our favorites didn't load. You can always browse <Link to="/products">all products</Link>.
          </p>
        ) : (
          <div className="product-grid">
            {status === 'loading'
              ? FEATURED_IDS.map((id) => <ProductCardSkeleton key={id} />)
              : featured.map((product) => (
                  <ProductCard key={product.product_id} product={product} info={product.description} />
                ))}
          </div>
        )}
      </section>

      <section className="section section-alt">
        <div className="container value-grid">
          <div className="value">
            <h3>The real deal</h3>
            <p>Everything here is officially licensed by Yale. No knockoffs, no guessing.</p>
          </div>
          <div className="value">
            <h3>For the whole Yale family</h3>
            <p>
              Students, alums, parents, grandparents, your residential college, your team. There's
              something for whoever you're shopping for.
            </p>
          </div>
          <div className="value">
            <h3>Easy returns</h3>
            <p>Changed your mind? Send it back unworn with the tags on within 30 days of shipping.</p>
          </div>
        </div>
      </section>

      <section className="section container chat-callout">
        <h2>Got a question?</h2>
        <p className="muted">
          Open the chat in the bottom-right corner and ask about a product, a size, or what to get
          someone.
        </p>
      </section>
    </>
  )
}
