import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
// Self-hosted fonts (latin subsets): Caslon for headlines and prices, Inter for text, Barlow Condensed for labels.
import '@fontsource/libre-caslon-display/latin-400.css'
import '@fontsource/libre-caslon-text/latin-400.css'
import '@fontsource/libre-caslon-text/latin-700.css'
import '@fontsource-variable/inter'
import '@fontsource/barlow-condensed/latin-600.css'
import './index.css'
import './storefront.css'
import App from './App.tsx'
import AuthProvider from './auth/AuthProvider.tsx'
import CartProvider from './cart/CartProvider.tsx'
import ChatPageProvider from './chat/ChatPageProvider.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <CartProvider>
          <ChatPageProvider>
            <App />
          </ChatPageProvider>
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
