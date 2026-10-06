import type {
  CartChange,
  CartItem,
  CartView,
  ChatHistory,
  ChatMessage,
  ChatReply,
  PageContext,
  OutboxEmail,
  Product,
  ProductDetail,
  RegisterDetails,
  User,
} from './types.ts'

// Vite proxies /api and /images to the FastAPI backend on port 8000, so requests
// are same-origin and the HttpOnly session cookie is sent automatically.

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

/** Turn a FastAPI error body into one readable sentence. */
async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      return String(body.detail[0].msg).replace(/^Value error, /, '')
    }
  } catch {
    // Not JSON; fall through to the generic message.
  }
  return 'Something went wrong. Please try again.'
}

async function sendJson<T>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!response.ok) {
    throw new ApiError(await errorMessage(response), response.status)
  }
  return (await response.json()) as T
}

function postJson<T>(path: string, body?: unknown): Promise<T> {
  return sendJson<T>('POST', path, body)
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(response.status === 404 ? 'not-found' : `Request failed (${response.status})`)
  }
  return (await response.json()) as T
}

export async function fetchProducts(): Promise<Product[]> {
  const data = await getJson<{ count: number; products: Product[] }>('/api/products')
  return data.products
}

export function fetchProduct(productId: string): Promise<ProductDetail> {
  return getJson<ProductDetail>(`/api/products/${encodeURIComponent(productId)}`)
}

export async function fetchCurrentUser(): Promise<User | null> {
  const data = await getJson<{ user: User | null }>('/api/auth/me')
  return data.user
}

export async function registerAccount(details: RegisterDetails): Promise<User> {
  const data = await postJson<{ user: User }>('/api/auth/register', details)
  return data.user
}

export async function logIn(email: string, password: string): Promise<User> {
  const data = await postJson<{ user: User }>('/api/auth/login', { email, password })
  return data.user
}

export async function logOut(): Promise<void> {
  await postJson('/api/auth/logout')
}

export function formatPrice(price: number): string {
  return price.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

// Guests' chats live only in the browser, so their recent turns travel with each message (the backend keeps
// the last 12). Logged-in shoppers' history is read from the database instead.
const HISTORY_SENT = 12

/** Send a message to the shop agent (POST /api/chat) with the recent conversation and the current page. */
export function sendChatMessage(message: string, history: ChatMessage[], page: PageContext): Promise<ChatReply> {
  return postJson<ChatReply>('/api/chat', {
    message,
    page,
    history: history.slice(-HISTORY_SENT).map((turn) => ({
      role: turn.role,
      content: turn.content,
      product_ids: (turn.products ?? []).map((product) => product.product_id),
      page_title: turn.pageResults?.title ?? null,
    })),
  })
}

/** The logged-in shopper's saved chat (empty for guests). */
export async function fetchChatHistory(): Promise<ChatMessage[]> {
  const data = await getJson<ChatHistory>('/api/chat/history')
  return data.messages.map((message) => ({
    role: message.role,
    content: message.content,
    products: message.products,
    pageResults: message.page_results ?? undefined,
  }))
}

/** Delete the logged-in shopper's saved chat. */
export async function clearChatHistory(): Promise<void> {
  const response = await fetch('/api/chat/history', { method: 'DELETE' })
  if (!response.ok) throw new ApiError(await errorMessage(response), response.status)
}

// ---------- Cart ----------

/** The logged-in shopper's saved cart. */
export function fetchCart(): Promise<CartView> {
  return getJson<CartView>('/api/cart')
}

export function addCartItem(item: CartItem): Promise<CartChange> {
  return postJson<CartChange>('/api/cart/items', item)
}

export function updateCartItem(item: CartItem): Promise<CartChange> {
  return sendJson<CartChange>('PATCH', '/api/cart/items', item)
}

export function removeCartItem(productId: string, size: string): Promise<CartChange> {
  return sendJson<CartChange>(
    'DELETE',
    `/api/cart/items/${encodeURIComponent(productId)}/${encodeURIComponent(size)}`,
  )
}

/** Price and stock-check a guest's browser cart (quantities come back capped at what's in stock). */
export function previewCart(items: CartItem[]): Promise<CartView> {
  return postJson<CartView>('/api/cart/preview', { items })
}

/** Move a guest's browser cart into their account after logging in. */
export function mergeCart(items: CartItem[]): Promise<CartView> {
  return postJson<CartView>('/api/cart/merge', { items })
}

export async function setCartEmails(enabled: boolean): Promise<User> {
  const data = await sendJson<{ user: User }>('PATCH', '/api/account/preferences', { cart_emails: enabled })
  return data.user
}

// ---------- Staff outbox (drafted reminder emails; works on the server's own machine) ----------

export function fetchOutbox(): Promise<OutboxEmail[]> {
  return getJson<OutboxEmail[]>('/api/staff/outbox')
}

export function draftCartReminders(idleHours: number): Promise<OutboxEmail[]> {
  return postJson<OutboxEmail[]>(`/api/staff/outbox/cart-reminders?idle_hours=${idleHours}`)
}
