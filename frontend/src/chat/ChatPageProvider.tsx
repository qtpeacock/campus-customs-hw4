import { useCallback, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { ProductMatches } from '../types.ts'
import { ChatPageContext } from './ChatPageContext.ts'
import type { ChatPageState } from './ChatPageContext.ts'

// Kept for the browser tab's lifetime, so results survive a refresh or a trip to a product page.
const STORAGE_KEY = 'cc_chat_results'

function loadSaved(): ProductMatches | null {
  try {
    const saved = sessionStorage.getItem(STORAGE_KEY)
    return saved ? (JSON.parse(saved) as ProductMatches) : null
  } catch {
    return null
  }
}

export default function ChatPageProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ProductMatches | null>(loadSaved)
  const [resultsKey, setResultsKey] = useState(0)
  const [chatOpen, setChatOpen] = useState(false)
  const [viewing, setViewing] = useState<{ product_id: string; name: string } | null>(null)

  const showResults = useCallback((next: ProductMatches) => {
    setResults(next)
    setResultsKey((key) => key + 1)
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  }, [])

  const clearResults = useCallback(() => {
    setResults(null)
    sessionStorage.removeItem(STORAGE_KEY)
  }, [])

  const value = useMemo<ChatPageState>(
    () => ({ results, resultsKey, showResults, clearResults, chatOpen, setChatOpen, viewing, setViewing }),
    [results, resultsKey, showResults, clearResults, chatOpen, viewing],
  )

  return <ChatPageContext.Provider value={value}>{children}</ChatPageContext.Provider>
}
