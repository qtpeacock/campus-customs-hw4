import { Link } from 'react-router-dom'
import { Seal } from './Logo.tsx'

const YEAR = new Date().getFullYear()

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="varsity-stripe" aria-hidden="true" />
      <div className="container footer-grid">
        <div className="footer-brand-col">
          <Seal size={92} light />
          <p className="footer-brand">Campus Customs</p>
          <p>
            57 Broadway
            <br />
            New Haven, CT 06511
          </p>
        </div>
        <div>
          <p className="footer-heading">Shop</p>
          <ul>
            <li>
              <Link to="/products">All products</Link>
            </li>
            <li>
              <Link to="/about">About us</Link>
            </li>
            <li>
              <Link to="/create-account">Create an account</Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="footer-heading">Questions</p>
          <ul>
            <li>
              <a href="mailto:orderdept@campuscustoms.com">orderdept@campuscustoms.com</a>
            </li>
            <li>
              <a href="tel:+14753014205">(475) 301-4205</a>
            </li>
            <li>Returns within 30 days, unworn with tags</li>
          </ul>
        </div>
      </div>
      <div className="container footer-bottom">
        <p>© {YEAR} Campus Customs. Officially licensed Yale merchandise.</p>
      </div>
    </footer>
  )
}
