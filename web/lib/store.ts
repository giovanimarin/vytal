'use client'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  userId: string | null
  email: string | null
  name: string | null
  gender: string | null
  preferredModalities: string[]
  accessToken: string | null
  refreshToken: string | null
  sessionVersion: number
  setAuth: (userId: string, email: string, name: string, token: string, refresh?: string) => void
  setTokens: (token: string, refresh: string) => void
  setProfile: (profile: { gender?: string | null; preferredModalities?: string[] }) => void
  clear: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      userId: null,
      email: null,
      name: null,
      gender: null,
      preferredModalities: [],
      accessToken: null,
      refreshToken: null,
      sessionVersion: 0,
      setAuth: (userId, email, name, accessToken, refreshToken) => {
        if (!userId?.trim() || !accessToken?.trim() || !email?.trim()) throw new Error('Sessão inválida.')
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', accessToken)
          localStorage.setItem('user_id', userId)
        }
        set((s) => ({ userId, email, name, accessToken, refreshToken: refreshToken || null,
          gender: null, preferredModalities: [], sessionVersion: s.sessionVersion + 1 }))
      },
      setTokens: (accessToken, refreshToken) => {
        if (!accessToken?.trim() || !refreshToken?.trim()) throw new Error('Sessão inválida.')
        if (typeof window !== 'undefined') localStorage.setItem('access_token', accessToken)
        set({ accessToken, refreshToken })
      },
      setProfile: ({ gender, preferredModalities }) => {
        set((s) => ({
          gender: gender !== undefined ? gender : s.gender,
          preferredModalities: preferredModalities !== undefined ? preferredModalities : s.preferredModalities,
        }))
      },
      clear: () => {
        // Zustand updates memory before its persistence write. Storage denial must
        // not leave the previous account active or block the logout transition.
        let persistenceFailed = false
        try {
          set((s) => ({ userId: null, email: null, name: null, gender: null,
            preferredModalities: [], accessToken: null, refreshToken: null, sessionVersion: s.sessionVersion + 1 }))
        } catch { persistenceFailed = true }
        if (typeof window !== 'undefined') {
          for (const key of ['access_token', 'user_id', ...(persistenceFailed ? ['vytal-auth'] : [])]) {
            try { localStorage.removeItem(key) } catch { /* Memory is already signed out. */ }
          }
        }
      },
    }),
    { name: 'vytal-auth', // Do not add a persistent long-lived bearer credential to browser storage.
      partialize: ({ sessionVersion: _version, refreshToken: _refresh, ...persisted }) => persisted }
  )
)
