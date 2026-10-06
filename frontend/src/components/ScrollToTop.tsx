import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/** Start each new page at the top instead of keeping the old scroll position. */
export default function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}
