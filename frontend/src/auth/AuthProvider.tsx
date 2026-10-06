import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { fetchCurrentUser, logIn, logOut, registerAccount } from '../api.ts'
import type { User } from '../types.ts'
import { AuthContext } from './AuthContext.ts'
import type { AuthState } from './AuthContext.ts'

export default function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)

  // The session lives in an HttpOnly cookie the page can't read, so ask the backend.
  useEffect(() => {
    fetchCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setReady(true))
  }, [])

  const value = useMemo<AuthState>(
    () => ({
      user,
      ready,
      login: async (email, password) => {
        const loggedIn = await logIn(email, password)
        setUser(loggedIn)
        return loggedIn
      },
      register: async (details) => {
        const created = await registerAccount(details)
        setUser(created)
        return created
      },
      logout: async () => {
        await logOut()
        setUser(null)
      },
      updateUser: setUser,
    }),
    [user, ready],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
