import { createContext, useContext } from 'react'
import type { CartView } from '../types.ts'

export interface CartResult {
  ok: boolean
  message: string
}

export interface CartState {
  /** Priced and stock-checked by the backend, for guests and logged-in shoppers alike. */
  cart: CartView
  ready: boolean
  add: (productId: string, size: string, quantity: number) => Promise<CartResult>
  setQuantity: (productId: string, size: string, quantity: number) => Promise<CartResult>
  remove: (productId: string, size: string) => Promise<CartResult>
  /** Re-read the cart (e.g. after the chat agent changed it). */
  refresh: () => Promise<void>
}

export const EMPTY_CART: CartView = { lines: [], item_count: 0, subtotal: 0, has_problems: false }

export const CartContext = createContext<CartState | null>(null)

export function useCart(): CartState {
  const state = useContext(CartContext)
  if (!state) throw new Error('useCart must be used inside <CartProvider>')
  return state
}
