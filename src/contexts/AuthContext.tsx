import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi, affiliateApi, AffiliateUser } from '../lib/api'

interface AuthContextType {
  user: AffiliateUser | null
  token: string | null
  isAdmin: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (name: string, email: string, password: string, referral_code?: string) => Promise<void>
  signOut: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AffiliateUser | null>(() => {
    const stored = localStorage.getItem('wwl_mlm_user')
    return stored ? JSON.parse(stored) : null
  })
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('wwl_mlm_token'))

  useEffect(() => {
    if (token) {
      affiliateApi.getMe().then(setUser).catch(() => {
        setToken(null)
        setUser(null)
        localStorage.removeItem('wwl_mlm_token')
        localStorage.removeItem('wwl_mlm_user')
      })
    }
  }, [])

  const persist = (newToken: string, newUser: AffiliateUser) => {
    localStorage.setItem('wwl_mlm_token', newToken)
    localStorage.setItem('wwl_mlm_user', JSON.stringify(newUser))
    setToken(newToken)
    setUser(newUser)
  }

  const signIn = async (email: string, password: string) => {
    const res = await authApi.login({ email, password })
    persist(res.access_token, res.user)
  }

  const signUp = async (name: string, email: string, password: string, referral_code?: string) => {
    const res = await authApi.register({ name, email, password, referral_code })
    persist(res.access_token, res.user)
  }

  const signOut = () => {
    localStorage.removeItem('wwl_mlm_token')
    localStorage.removeItem('wwl_mlm_user')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, isAdmin: user?.is_admin ?? false, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
