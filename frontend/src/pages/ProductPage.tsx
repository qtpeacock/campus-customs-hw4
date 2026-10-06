import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice } from '../api.ts'
import { categoryByKind } from '../catalog.ts'
import AddToCart from '../components/AddToCart.tsx'
import ProductGallery from '../components/ProductGallery.tsx'
import { useChatPage } from '../chat/ChatPageContext.ts'
import type { ProductDetail } from '../types.ts'

interface ProductResult {
  id: string
  status: 'ready' | 'not-found' | 'error'
  product?: ProductDetail
}

export default function ProductPage() {
  const { productId = '' } = useParams()
  // If the chat put results on the Products page, the way back says so.
  const { results: chatResults, setViewing } = useChatPage()
  const backLabel = chatResults ? `Back to ${chatResults.title}` : 'Back to all products'
  // Tagged with the id it belongs to, so switching products shows "loading" until the new one arrives.
  const [result, setResult] = useState<ProductResult | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchProduct(productId)
      .then((product) => !cancelled && setResult({ id: productId, status: 'ready', product }))
      .catch(
        (error: Error) =>
          !cancelled &&
          setResult({ id: productId, status: error.message === 'not-found' ? 'not-found' : 'error' }),
      )
    return () => {
      cancelled = true
    }
  }, [productId])

  // Tell the chat which product this page is about (it shows "Looking at …" and the agent gets it as context).
  const viewedName = result?.id === productId ? result.product?.name : undefined
  useEffect(() => {
    if (viewedName) setViewing({ product_id: productId, name: viewedName })
    return () => setViewing(null)
  }, [productId, viewedName, setViewing])

  if (!result || result.id !== productId) {
    return <p className="section container muted">Loading product…</p>
  }

  const { status, product } = result
  if (status !== 'ready' || !product) {
    return (
      <section className="section container">
        <h1>{status === 'not-found' ? "We couldn't find that one" : 'Something went wrong'}</h1>
        <p className="muted">
          {status === 'not-found'
            ? 'That product may have moved or no longer exists.'
            : "We couldn't load this product right now. Please try again in a moment."}
        </p>
        <Link to="/products" className="btn btn-primary">
          Back to all products
        </Link>
      </section>
    )
  }

  const inStockSizes = product.sizes.filter((s) => s.quantity > 0).length
  const category = categoryByKind(product.kind)

  return (
    <section className="section container">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        {chatResults ? (
          <Link to="/products">{chatResults.title}</Link>
        ) : (
          <>
            <Link to="/products?category=all">Products</Link>
            {category && (
              <>
                <span aria-hidden="true"> / </span>
                <Link to={`/products?category=${category.slug}`}>{category.label}</Link>
              </>
            )}
          </>
        )}
        <span aria-hidden="true"> / </span>
        <span aria-current="page">{product.name}</span>
      </nav>

      <div className="product-detail">
        {/* Keyed by product so it starts on the product photo each time. */}
        <ProductGallery
          key={product.product_id}
          name={product.name}
          image={product.image_url}
          extras={product.extra_images}
        />

        <div className="product-detail-info">
          <p className="product-card-type">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="product-detail-price">{formatPrice(product.price)}</p>
          <p className="product-detail-desc">{product.description}</p>

          <h2 className="detail-heading">Colors</h2>
          <p>{product.colors.join(', ')}</p>

          <h2 className="detail-heading">Choose a size</h2>
          {product.sizes.length > 0 ? (
            <>
              {/* Keyed by product so the chosen size resets when moving to another item. */}
              <AddToCart key={product.product_id} product={product} />
              <p className="muted small">
                {inStockSizes === product.sizes.length
                  ? 'Every size is in stock right now.'
                  : inStockSizes === 0
                    ? 'This one is sold out in every size right now.'
                    : `${inStockSizes} of ${product.sizes.length} sizes in stock right now.`}
              </p>
            </>
          ) : (
            <p className="muted">Size info isn't available for this product yet.</p>
          )}

          <h2 className="detail-heading">Good to know</h2>
          <ul className="detail-list">
            <li>Officially licensed Yale merchandise.</li>
            <li>Returns within 30 days of shipping, unworn with the tags on.</li>
          </ul>

          <Link to="/products" className="text-link">
            ← {backLabel}
          </Link>
        </div>
      </div>
    </section>
  )
}
