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
  setAuth: (userId: string, email: string, name: string, token: string) => void
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
      setAuth: (userId, email, name, accessToken) => {
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', accessToken)
          localStorage.setItem('user_id', userId)
        }
        set({ userId, email, name, accessToken })
      },
      setProfile: ({ gender, preferredModalities }) => {
        set((s) => ({
          gender: gender !== undefined ? gender : s.gender,
          preferredModalities: preferredModalities !== undefined ? preferredModalities : s.preferredModalities,
        }))
      },
      clear: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token')
          localStorage.removeItem('user_id')
        }
        set({ userId: null, email: null, name: null, gender: null, preferredModalities: [], accessToken: null })
      },
    }),
    { name: 'vytal-auth' }
  )
)
