import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <section className="section container">
      <h1>Page not found</h1>
      <p className="muted">That page doesn't exist. Let's get you back to the good stuff.</p>
      <Link to="/products" className="btn btn-primary">
        Shop all products
      </Link>
    </section>
  )
}
