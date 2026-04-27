'use client'
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface ClientPrincipal {
  userId: string
  userRoles: string[]
  claims: any[]
  identityProvider: string
  userDetails: string
}

interface AuthCtx {
  user: ClientPrincipal | null
  loading: boolean
}

const Ctx = createContext<AuthCtx | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<ClientPrincipal | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function checkAuth() {
      try {
        const res = await fetch('/.auth/me')
        const data = await res.json()
        setUser(data.clientPrincipal)
      } catch (e) {
        setUser(null)
      } finally {
        setLoading(false)
      }
    }
    checkAuth()
  }, [])

  return (
    <Ctx.Provider value={{ user, loading }}>
      {children}
    </Ctx.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
