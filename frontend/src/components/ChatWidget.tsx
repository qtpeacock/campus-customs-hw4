import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { clearChatHistory, fetchChatHistory, formatPrice, sendChatMessage } from '../api.ts'
import { useAuth } from '../auth/AuthContext.ts'
import { useCart } from '../cart/CartContext.ts'
import { useChatPage } from '../chat/ChatPageContext.ts'
import type { ChatMessage, ChatProduct, PageContext, ProductMatches } from '../types.ts'

// On narrow screens the panel covers the page, so it tucks away when results land.
const NARROW_SCREEN = '(max-width: 720px)'
const PRODUCT_PATH = /^\/products\/([^/]+)$/

function ChatProductCards({ products }: { products: ChatProduct[] }) {
  return (
    <ul className="chat-products">
      {products.map((product) => (
        <li key={product.product_id}>
          <Link to={`/products/${product.product_id}`} className="chat-product">
            <img src={product.image_url} alt="" loading="lazy" />
            <span className="chat-product-text">
              <span className="chat-product-name">{product.name}</span>
              <span className="chat-product-price">{formatPrice(product.price)}</span>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  )
}

/** Older saved replies used **bold** markdown; the chat shows plain text. */
function plain(text: string): string {
  return text.replace(/\*\*(.+?)\*\*/g, '$1')
}

// Keyed by shopper in App.tsx, so logging in or out mounts a fresh widget.
export default function ChatWidget() {
  const { user } = useAuth()
  const { chatOpen: open, setChatOpen: setOpen, showResults, results, viewing } = useChatPage()
  const { refresh: refreshCart } = useCart()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [history, setHistory] = useState<'loading' | 'ready' | 'error'>(user ? 'loading' : 'ready')
  const [returning, setReturning] = useState(false)
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Logged-in shoppers pick up their saved conversation from the database.
  useEffect(() => {
    if (!user) return
    fetchChatHistory()
      .then((saved) => {
        setMessages(saved)
        setReturning(saved.length > 0)
        setHistory('ready')
      })
      .catch(() => setHistory('error'))
  }, [user])

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages, sending, open, history])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  // What the shopper is looking at, sent with every message so "this" and "these" make sense.
  const productId = PRODUCT_PATH.exec(pathname)?.[1]
  const page: PageContext = {
    path: pathname,
    product_id: productId ? decodeURIComponent(productId) : null,
    results_title: pathname === '/products' ? (results?.title ?? null) : null,
  }
  const viewingName = viewing && viewing.product_id === page.product_id ? viewing.name : null

  const welcome = !user
    ? 'Hey! Looking for something? Ask me about hoodies, crewnecks, tees, sizes, or stock. Log in and I’ll remember our chat for next time.'
    : returning
      ? `Welcome back, ${user.first_name}! Here’s where we left off.`
      : `Hey ${user.first_name}! Looking for something? Ask me about hoodies, crewnecks, tees, sizes, or stock.`

  /** Show a chat search on the Products page (navigating there if needed). */
  function putResultsOnPage(next: ProductMatches) {
    showResults(next)
    if (pathname !== '/products') navigate('/products')
    else window.scrollTo({ top: 0, behavior: 'smooth' })
    if (window.matchMedia(NARROW_SCREEN).matches) setOpen(false)
  }

  async function startNewChat() {
    if (user) {
      try {
        await clearChatHistory()
      } catch {
        return
      }
    }
    setMessages([])
    setReturning(false)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || sending || history === 'loading') return

    const earlier = messages
    setMessages([...earlier, { role: 'user', content: text }])
    setDraft('')
    setSending(true)
    try {
      const { reply, products, page_results, cart_changed } = await sendChatMessage(text, earlier, page)
      if (cart_changed) void refreshCart()
      setMessages((current) => [
        ...current,
        { role: 'assistant', content: reply, products, pageResults: page_results ?? undefined },
      ])
      if (page_results) putResultsOnPage(page_results)
    } catch (err) {
      const content = err instanceof Error ? err.message : 'Sorry, something went wrong. Please try again.'
      setMessages((current) => [...current, { role: 'assistant', content }])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="chat-widget">
      {open && (
        <section id="chat-panel" className="chat-panel" aria-label="Campus Customs chat">
          <header className="chat-header">
            <div>
              <p className="chat-title">Campus Customs Chat</p>
              <p className="chat-subtitle">
                {user ? 'Your chat is saved to your account.' : 'Real prices and stock, straight from the shop.'}
              </p>
            </div>
            <div className="chat-header-actions">
              {messages.length > 0 && (
                <button type="button" className="chat-new" onClick={() => void startNewChat()}>
                  New chat
                </button>
              )}
              <button type="button" className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
                ×
              </button>
            </div>
          </header>

          <div className="chat-messages" ref={listRef} aria-live="polite">
            <div className="chat-bubble assistant">{welcome}</div>
            {history === 'loading' && <div className="chat-bubble assistant typing">Loading your chat…</div>}
            {history === 'error' && (
              <div className="chat-bubble assistant">I couldn’t load your earlier chat, but you can keep going.</div>
            )}
            {messages.map((message, index) => (
              <div key={index} className={`chat-turn ${message.role}`}>
                <div className={`chat-bubble ${message.role}`}>{plain(message.content)}</div>
                {message.pageResults && (
                  <button
                    type="button"
                    className="chat-page-chip"
                    onClick={() => putResultsOnPage(message.pageResults!)}
                  >
                    <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">
                      <path fill="currentColor" d="M3 3h8v8H3V3Zm10 0h8v8h-8V3ZM3 13h8v8H3v-8Zm10 0h8v8h-8v-8Z" />
                    </svg>
                    {message.pageResults.total_matches} on the page: {message.pageResults.title}
                    <span aria-hidden="true">→</span>
                  </button>
                )}
                {message.products && message.products.length > 0 && (
                  <ChatProductCards products={message.products} />
                )}
              </div>
            ))}
            {sending && <div className="chat-bubble assistant typing">Typing…</div>}
          </div>

          {viewingName && (
            <p className="chat-context">
              <span className="visually-hidden">Page context: </span>
              Looking at <strong>{viewingName}</strong>. Ask “do you have this in M?”
            </p>
          )}

          <form className="chat-form" onSubmit={handleSubmit}>
            <label htmlFor="chat-input" className="visually-hidden">
              Message
            </label>
            <input
              id="chat-input"
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={viewingName ? 'Ask about this item…' : 'Ask about a product…'}
              autoComplete="off"
              maxLength={1000}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!draft.trim() || sending || history === 'loading'}
            >
              Send
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        className="chat-launcher"
        aria-expanded={open}
        aria-controls="chat-panel"
        onClick={() => setOpen(!open)}
      >
        <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
          <path
            fill="currentColor"
            d="M4 3h16a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H9l-5 4v-4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"
          />
        </svg>
        <span>{open ? 'Close chat' : 'Chat with us'}</span>
      </button>
    </div>
  )
}
