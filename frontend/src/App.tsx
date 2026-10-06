import { Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/AuthContext.ts'
import ChatWidget from './components/ChatWidget.tsx'
import Footer from './components/Footer.tsx'
import NavBar from './components/NavBar.tsx'
import ScrollToTop from './components/ScrollToTop.tsx'
import AboutPage from './pages/AboutPage.tsx'
import CartPage from './pages/CartPage.tsx'
import CreateAccountPage from './pages/CreateAccountPage.tsx'
import HomePage from './pages/HomePage.tsx'
import LoginPage from './pages/LoginPage.tsx'
import NotFoundPage from './pages/NotFoundPage.tsx'
import OutboxPage from './pages/OutboxPage.tsx'
import ProductPage from './pages/ProductPage.tsx'
import ProductsPage from './pages/ProductsPage.tsx'

export default function App() {
  const { user } = useAuth()

  return (
    <div className="app">
      <ScrollToTop />
      <NavBar />
      <main className="main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/products/:productId" element={<ProductPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/create-account" element={<CreateAccountPage />} />
          <Route path="/cart" element={<CartPage />} />
          {/* Staff page for drafted cart reminder emails; not linked in the nav. */}
          <Route path="/outbox" element={<OutboxPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <Footer />
      {/* Lives outside <Routes> so the conversation survives page changes; keyed by
          shopper so logging in or out starts a fresh conversation. */}
      <ChatWidget key={user?.id ?? 'guest'} />
    </div>
  )
}
