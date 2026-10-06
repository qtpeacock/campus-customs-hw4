import { createContext, useContext } from 'react'
import type { RegisterDetails, User } from '../types.ts'

export interface AuthState {
  /** The logged-in shopper, or null for visitors. */
  user: User | null
  /** False until the backend has said who (if anyone) is logged in. */
  ready: boolean
  login: (email: string, password: string) => Promise<User>
  register: (details: RegisterDetails) => Promise<User>
  logout: () => Promise<void>
  /** Replace the stored user after a profile change (e.g. the cart email opt-in). */
  updateUser: (user: User) => void
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth(): AuthState {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('useAuth must be used inside <AuthProvider>')
  return auth
}
