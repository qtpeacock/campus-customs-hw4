import { createContext, useContext } from 'react'
import type { ProductMatches } from '../types.ts'

/** Shared between the chat widget (which receives search results) and the pages that show them. */
export interface ChatPageState {
  /** The latest chat search results to show on the Products page, or null for the normal catalogue. */
  results: ProductMatches | null
  /** Changes every time new results arrive, so the cards replay their entrance animation. */
  resultsKey: number
  showResults: (results: ProductMatches) => void
  clearResults: () => void
  chatOpen: boolean
  setChatOpen: (open: boolean) => void
  /** The product page the shopper is on (set by ProductPage), so the chat can show what "this" means. */
  viewing: { product_id: string; name: string } | null
  setViewing: (product: { product_id: string; name: string } | null) => void
}

export const ChatPageContext = createContext<ChatPageState | null>(null)

export function useChatPage(): ChatPageState {
  const state = useContext(ChatPageContext)
  if (!state) throw new Error('useChatPage must be used inside <ChatPageProvider>')
  return state
}
