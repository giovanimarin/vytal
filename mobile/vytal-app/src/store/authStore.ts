import create from 'zustand'
import * as SecureStore from 'expo-secure-store'

export interface UserProfile {
  user_id: string
  email: string
  name: string
  birth_date: string | null
  weight_kg: number | null
  height_cm: number | null
  goal: string | null
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  userProfile: UserProfile | null
  isAuthenticated: boolean
  // computed compat
  userId: string | null
  isConnected: boolean // keep for backward compat with existing code
  // actions
  setTokens: (access: string, refresh: string) => void
  setProfile: (profile: UserProfile) => void
  logout: () => void
  // old compat actions (used by connect.tsx and other screens)
  setUserId: (id: string) => void
  setConnected: (value: boolean) => void
  reset: () => void
  // init: load tokens from SecureStore on app start
  initFromStorage: () => Promise<void>
}

const SECURE_KEY_ACCESS = 'vytal_access_token'
const SECURE_KEY_REFRESH = 'vytal_refresh_token'
const SECURE_KEY_PROFILE = 'vytal_user_profile'

// Helper: check if we're in a web environment where SecureStore isn't available
const isWeb = typeof window !== 'undefined' && typeof document !== 'undefined'

async function secureGet(key: string): Promise<string | null> {
  if (isWeb) return localStorage.getItem(key)
  return SecureStore.getItemAsync(key)
}

async function secureSet(key: string, value: string): Promise<void> {
  if (isWeb) {
    localStorage.setItem(key, value)
    return
  }
  return SecureStore.setItemAsync(key, value)
}

async function secureDelete(key: string): Promise<void> {
  if (isWeb) {
    localStorage.removeItem(key)
    return
  }
  return SecureStore.deleteItemAsync(key)
}

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  refreshToken: null,
  userProfile: null,
  isAuthenticated: false,
  userId: null,
  isConnected: false,

  setTokens: (access, refresh) => {
    set({ accessToken: access, refreshToken: refresh, isAuthenticated: true, isConnected: true })
    secureSet(SECURE_KEY_ACCESS, access)
    secureSet(SECURE_KEY_REFRESH, refresh)
  },

  setProfile: (profile) => {
    set({ userProfile: profile, userId: profile.user_id })
    secureSet(SECURE_KEY_PROFILE, JSON.stringify(profile))
  },

  logout: () => {
    set({
      accessToken: null,
      refreshToken: null,
      userProfile: null,
      isAuthenticated: false,
      isConnected: false,
      userId: null,
    })
    secureDelete(SECURE_KEY_ACCESS)
    secureDelete(SECURE_KEY_REFRESH)
    secureDelete(SECURE_KEY_PROFILE)
  },

  // Backward compat stubs
  setUserId: (id) => set({ userId: id }),
  setConnected: (value) => set({ isConnected: value, isAuthenticated: value }),
  reset: () => get().logout(),

  initFromStorage: async () => {
    const access = await secureGet(SECURE_KEY_ACCESS)
    const refresh = await secureGet(SECURE_KEY_REFRESH)
    const profileStr = await secureGet(SECURE_KEY_PROFILE)
    if (access && refresh) {
      const profile = profileStr ? JSON.parse(profileStr) : null
      set({
        accessToken: access,
        refreshToken: refresh,
        userProfile: profile,
        userId: profile?.user_id ?? null,
        isAuthenticated: true,
        isConnected: true,
      })
    }
  },
}))
