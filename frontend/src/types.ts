// Shapes returned by the FastAPI backend (backend/main.py).

export interface Product {
  product_id: string
  name: string
  garment_type: string
  /** hoodie, crewneck, t-shirt, quarter-zip, jacket, or long-sleeve (see catalog.ts). */
  kind: string
  description: string
  colors: string[]
  search_tags: string[]
  price: number
  image_url: string
  /** Shop-by collections: colleges, sports, family, schools, classics (see catalog.ts). */
  collections: string[]
  /** Extra photos, e.g. someone wearing it; shown on hover and in the product page gallery. */
  extra_images: string[]
  /** Units in stock per size (list endpoint only), for card badges and quick add. */
  stock?: Record<string, number>
}

export interface SizeStock {
  size: string
  quantity: number
}

export interface ProductDetail extends Product {
  sizes: SizeStock[]
}

// Never includes the password hash; the backend doesn't send it.
export interface User {
  id: number
  first_name: string
  last_name: string
  name: string
  email: string
  /** Opted in to a reminder email about items left in the cart. */
  cart_emails: boolean
}

export interface RegisterDetails {
  first_name: string
  last_name: string
  email: string
  password: string
  cart_emails: boolean
}

// A product card shown under a chat reply (built by the backend from the database).
export interface ChatProduct {
  product_id: string
  name: string
  garment_type: string
  price: number
  image_url: string
}

// ---------- Chat search results shown on the page (POST /api/chat -> page_results) ----------

/** The catalogue search the agent ran; the backend re-runs it to fill the page. */
export interface CatalogueFilters {
  query: string
  kind: string | null
  color: string | null
  max_price: number | null
  size: string | null
}

/** One product card on the page: image, name, price, and short info. */
export interface ProductMatch {
  product_id: string
  name: string
  garment_type: string
  kind: string
  price: number
  image_url: string
  short_description: string
  colors: string[]
  sizes_in_stock: string[]
}

export interface ProductMatches {
  title: string
  filters: CatalogueFilters
  total_matches: number
  products: ProductMatch[]
  price_min: number
  price_max: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  products?: ChatProduct[]
  /** Results this reply put on the page (kept so the chip can bring them back). */
  pageResults?: ProductMatches
}

export interface ChatReply {
  reply: string
  products: ChatProduct[]
  page_results: ProductMatches | null
  /** True when the agent added to or removed from the cart. */
  cart_changed: boolean
}

// ---------- Shopping cart (backend/tools.py, cart section) ----------

export interface CartLine {
  product_id: string
  name: string
  size: string
  quantity: number
  price: number
  line_total: number
  image_url: string
  in_stock: number
  status: 'ok' | 'low_stock' | 'exceeds_stock' | 'sold_out' | 'unavailable'
  note: string
}

export interface CartView {
  lines: CartLine[]
  item_count: number
  subtotal: number
  has_problems: boolean
}

export interface CartChange {
  ok: boolean
  message: string
  cart: CartView
}

/** A guest's cart item, kept in the browser until they log in. */
export interface CartItem {
  product_id: string
  size: string
  quantity: number
}

export interface OutboxEmail {
  id: number
  user_id: number
  kind: string
  to_email: string
  subject: string
  body: string
  status: string
  created_at: string
}

/** Sent with every chat message so the agent knows what the shopper is looking at. */
export interface PageContext {
  path: string
  product_id: string | null
  results_title: string | null
}

/** GET /api/chat/history: a logged-in shopper's saved conversation. */
export interface ChatHistory {
  logged_in: boolean
  messages: Array<{
    role: 'user' | 'assistant'
    content: string
    products: ChatProduct[]
    page_results: ProductMatches | null
    created_at: string
  }>
}
