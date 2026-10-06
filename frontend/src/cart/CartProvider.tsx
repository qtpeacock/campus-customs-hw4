import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { addCartItem, fetchCart, mergeCart, previewCart, removeCartItem, updateCartItem } from '../api.ts'
import { useAuth } from '../auth/AuthContext.ts'
import type { CartItem, CartView } from '../types.ts'
import { CartContext, EMPTY_CART } from './CartContext.ts'
import type { CartResult, CartState } from './CartContext.ts'

// Guests' carts live in the browser until they log in; then they're moved into the account.
const GUEST_KEY = 'cc_cart'

function loadGuestItems(): CartItem[] {
  try {
    return JSON.parse(localStorage.getItem(GUEST_KEY) ?? '[]') as CartItem[]
  } catch {
    return []
  }
}

function saveGuestItems(view: CartView): void {
  const items = view.lines
    .filter((line) => line.status !== 'sold_out' && line.status !== 'unavailable')
    .map(({ product_id, size, quantity }) => ({ product_id, size, quantity }))
  localStorage.setItem(GUEST_KEY, JSON.stringify(items))
}

const failed = (err: unknown): CartResult => ({
  ok: false,
  message: err instanceof Error ? err.message : 'Something went wrong. Please try again.',
})

export default function CartProvider({ children }: { children: ReactNode }) {
  const { user, ready: authReady } = useAuth()
  const [cart, setCart] = useState<CartView>(EMPTY_CART)
  const [ready, setReady] = useState(false)
  const userId = user?.id ?? null

  // Load the right cart whenever the shopper logs in or out.
  useEffect(() => {
    if (!authReady) return
    let cancelled = false
    const guestItems = loadGuestItems()
    const load: Promise<CartView> = userId
      ? guestItems.length
        ? mergeCart(guestItems).then((merged) => {
            localStorage.removeItem(GUEST_KEY)
            return merged
          })
        : fetchCart()
      : previewCart(guestItems)
    load
      .then((view) => !cancelled && setCart(view))
      .catch(() => !cancelled && setCart(EMPTY_CART))
      .finally(() => !cancelled && setReady(true))
    return () => {
      cancelled = true
    }
  }, [authReady, userId])

  /** Guests: apply a change to the browser cart and let the backend price and cap it. */
  const changeGuestCart = useCallback(async (items: CartItem[], productId: string, size: string) => {
    const view = await previewCart(items)
    saveGuestItems(view)
    setCart(view)
    return view.lines.find((line) => line.product_id === productId && line.size === size)
  }, [])

  const add = useCallback(
    async (productId: string, size: string, quantity: number): Promise<CartResult> => {
      try {
        if (userId) {
          const change = await addCartItem({ product_id: productId, size, quantity })
          setCart(change.cart)
          return { ok: change.ok, message: change.message }
        }
        const before = loadGuestItems().find((i) => i.product_id === productId && i.size === size)?.quantity ?? 0
        const line = await changeGuestCart(
          [...loadGuestItems(), { product_id: productId, size, quantity }],
          productId,
          size,
        )
        if (!line || line.status === 'sold_out' || line.status === 'unavailable') {
          return { ok: false, message: line?.note || 'That size is sold out right now, so it wasn’t added.' }
        }
        if (line.quantity <= before) {
          return { ok: false, message: `Your cart already has the most available (${line.quantity}).` }
        }
        const capped = line.quantity < before + quantity ? ` That's the most available right now.` : ''
        return { ok: true, message: `Added ${line.name} (${size}) to your cart.${capped}` }
      } catch (err) {
        return failed(err)
      }
    },
    [userId, changeGuestCart],
  )

  const setQuantity = useCallback(
    async (productId: string, size: string, quantity: number): Promise<CartResult> => {
      try {
        if (userId) {
          const change = await updateCartItem({ product_id: productId, size, quantity })
          setCart(change.cart)
          return { ok: change.ok, message: change.message }
        }
        const items = loadGuestItems()
          .map((i) => (i.product_id === productId && i.size === size ? { ...i, quantity } : i))
          .filter((i) => i.quantity > 0)
        await changeGuestCart(items, productId, size)
        return { ok: true, message: 'Updated your cart.' }
      } catch (err) {
        return failed(err)
      }
    },
    [userId, changeGuestCart],
  )

  const remove = useCallback(
    async (productId: string, size: string): Promise<CartResult> => {
      try {
        if (userId) {
          const change = await removeCartItem(productId, size)
          setCart(change.cart)
          return { ok: change.ok, message: change.message }
        }
        const items = loadGuestItems().filter((i) => !(i.product_id === productId && i.size === size))
        await changeGuestCart(items, productId, size)
        return { ok: true, message: 'Removed it from your cart.' }
      } catch (err) {
        return failed(err)
      }
    },
    [userId, changeGuestCart],
  )

  const refresh = useCallback(async () => {
    try {
      setCart(userId ? await fetchCart() : await previewCart(loadGuestItems()))
    } catch {
      // Keep showing the last known cart.
    }
  }, [userId])

  const value = useMemo<CartState>(
    () => ({ cart, ready, add, setQuantity, remove, refresh }),
    [cart, ready, add, setQuantity, remove, refresh],
  )

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}
