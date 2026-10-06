import { useEffect, useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.ts'
import { useCart } from '../cart/CartContext.ts'
import { CATEGORIES, COLLECTIONS } from '../catalog.ts'
import { useChatPage } from '../chat/ChatPageContext.ts'
import { ShieldMark } from './Logo.tsx'

// True statements only; they rotate gently in the black bar at the top.
const ANNOUNCEMENTS = [
  'Officially licensed Yale apparel',
  'Returns within 30 days, unworn with tags',
  '57 Broadway, right across from campus',
  'Orders are made in 5–8 business days, then shipped',
]
const ANNOUNCE_MS = 5000

function Chevron({ direction = 'down' }: { direction?: 'down' | 'right' }) {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" className={`chevron ${direction}`}>
      <path fill="currentColor" d={direction === 'down' ? 'M6 9l6 6 6-6H6Z' : 'M9 6l6 6-6 6V6Z'} />
    </svg>
  )
}

export default function NavBar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [shopOpen, setShopOpen] = useState(false)
  const [submenu, setSubmenu] = useState<'type' | 'collection' | null>(null)
  const [scrolled, setScrolled] = useState(false)
  const [announcement, setAnnouncement] = useState(0)
  const [announcePaused, setAnnouncePaused] = useState(false)
  const { user, ready, logout } = useAuth()
  const { clearResults } = useChatPage()
  const { cart } = useCart()

  // The header slims down and frosts once the page scrolls.
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Rotate the announcement bar (paused on hover, and not at all for reduced-motion visitors).
  useEffect(() => {
    if (announcePaused || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const timer = window.setInterval(() => setAnnouncement((i) => (i + 1) % ANNOUNCEMENTS.length), ANNOUNCE_MS)
    return () => window.clearInterval(timer)
  }, [announcePaused])

  const linkClass = ({ isActive }: { isActive: boolean }) => (isActive ? 'nav-link active' : 'nav-link')

  function closeShop() {
    setShopOpen(false)
    setSubmenu(null)
  }

  // Picking a type or collection means the shopper is browsing, so any chat results on the page give way.
  function pick() {
    clearResults()
    closeShop()
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur()
  }

  function toggleSubmenu(name: 'type' | 'collection') {
    setSubmenu((current) => (current === name ? null : name))
  }

  return (
    <header className={scrolled ? 'site-header scrolled' : 'site-header'}>
      <div
        className="announcement"
        onMouseEnter={() => setAnnouncePaused(true)}
        onMouseLeave={() => setAnnouncePaused(false)}
        aria-live="polite"
      >
        <span key={announcement} className="announcement-text">
          {ANNOUNCEMENTS[announcement]}
        </span>
      </div>
      <nav className="navbar container" aria-label="Main">
        <Link to="/" className="brand" aria-label="Campus Customs home">
          <ShieldMark size={34} />
          <span className="brand-text">
            <span className="brand-name">Campus Customs</span>
            <span className="brand-sub">Yale Bulldog Blue · New Haven</span>
          </span>
        </Link>

        <button
          type="button"
          className="menu-toggle"
          aria-expanded={menuOpen}
          aria-controls="nav-links"
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? 'Close' : 'Menu'}
        </button>

        {/* Any click on a link inside closes the mobile menu. */}
        <div
          id="nav-links"
          className={menuOpen ? 'nav-links open' : 'nav-links'}
          onClick={(event) => {
            if ((event.target as HTMLElement).closest('a')) setMenuOpen(false)
          }}
        >
          <NavLink to="/" end className={linkClass}>
            Home
          </NavLink>

          {/* Products, with two dropdowns inside: shop by Type and shop by Collection. */}
          <div
            className={shopOpen ? 'nav-dropdown open' : 'nav-dropdown'}
            onMouseLeave={closeShop}
            onKeyDown={(event) => event.key === 'Escape' && closeShop()}
          >
            <NavLink to="/products" className={linkClass}>
              Products
            </NavLink>
            <button
              type="button"
              className="nav-caret"
              aria-expanded={shopOpen}
              aria-controls="shop-menu"
              aria-label="Show product menu"
              onClick={() => setShopOpen((open) => !open)}
            >
              <Chevron />
            </button>
            <div id="shop-menu" className="nav-menu">
              <div
                className={submenu === 'type' ? 'nav-sub open' : 'nav-sub'}
                onPointerEnter={(event) => event.pointerType === 'mouse' && setSubmenu('type')}
              >
                <button
                  type="button"
                  className="nav-sub-toggle"
                  aria-expanded={submenu === 'type'}
                  aria-controls="shop-by-type"
                  onClick={() => toggleSubmenu('type')}
                >
                  <span>Type</span>
                  <Chevron direction="right" />
                </button>
                <ul id="shop-by-type" className="nav-submenu" aria-label="Shop by type">
                  {CATEGORIES.map((category) => (
                    <li key={category.slug}>
                      <Link to={`/products?category=${category.slug}`} onClick={pick}>
                        {category.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
              <div
                className={submenu === 'collection' ? 'nav-sub open' : 'nav-sub'}
                onPointerEnter={(event) => event.pointerType === 'mouse' && setSubmenu('collection')}
              >
                <button
                  type="button"
                  className="nav-sub-toggle"
                  aria-expanded={submenu === 'collection'}
                  aria-controls="shop-by-collection"
                  onClick={() => toggleSubmenu('collection')}
                >
                  <span>Collection</span>
                  <Chevron direction="right" />
                </button>
                <ul id="shop-by-collection" className="nav-submenu" aria-label="Shop by collection">
                  {COLLECTIONS.map((collection) => (
                    <li key={collection.slug}>
                      <Link to={`/products?collection=${collection.slug}`} onClick={pick}>
                        {collection.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
              <Link to="/products?category=all" className="nav-menu-all" onClick={pick}>
                Shop all products →
              </Link>
            </div>
          </div>

          <NavLink to="/about" className={linkClass}>
            About Us
          </NavLink>
          <NavLink
            to="/cart"
            className={({ isActive }) => (isActive ? 'nav-link nav-cart active' : 'nav-link nav-cart')}
            aria-label={`Cart, ${cart.item_count} ${cart.item_count === 1 ? 'item' : 'items'}`}
          >
            <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
              <path
                fill="currentColor"
                d="M7 4h-2a1 1 0 0 0 0 2h1.2l2.4 9.6A2 2 0 0 0 10.5 17H18a1 1 0 0 0 0-2h-7.5l-.25-1H18.3a2 2 0 0 0 1.94-1.5l1.2-4.8A1 1 0 0 0 20.5 6H8.3l-.33-1.3A1 1 0 0 0 7 4Zm3.5 15a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm7 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z"
              />
            </svg>
            <span className="nav-cart-label">Cart</span>
            {/* Keyed by count, so the badge replays its little bump whenever an item is added. */}
            {cart.item_count > 0 && (
              <span key={cart.item_count} className="cart-badge">
                {cart.item_count}
              </span>
            )}
          </NavLink>
          <span className="nav-divider" aria-hidden="true" />
          {/* Wait for the session check so logged-in shoppers don't see a flash of "Log In". */}
          {ready &&
            (user ? (
              <>
                <span className="nav-greeting">Hi, {user.first_name}</span>
                <button type="button" className="nav-link nav-button" onClick={() => void logout()}>
                  Log Out
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" className={linkClass}>
                  Log In
                </NavLink>
                <NavLink
                  to="/create-account"
                  className={({ isActive }) => (isActive ? 'nav-cta active' : 'nav-cta')}
                >
                  Create Account
                </NavLink>
              </>
            ))}
        </div>
      </nav>
    </header>
  )
}
