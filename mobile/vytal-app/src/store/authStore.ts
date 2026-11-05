import create from 'zustand'
import * as SecureStore from 'expo-secure-store'
import { AuthSession, UserProfile, profileFromResponse } from '../types/auth'
export type { UserProfile } from '../types/auth'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  userProfile: UserProfile | null
  isAuthenticated: boolean
  userId: string | null
  isConnected: boolean
  setSession: (session: AuthSession) => Promise<void>
  setTokens: (access: string, refresh: string) => void
  setProfile: (profile: UserProfile) => void
  logout: () => void
  reset: () => void
  initFromStorage: () => Promise<void>
}

const SESSION_KEY = 'vytal_session'
const LEGACY_KEYS = ['vytal_access_token', 'vytal_refresh_token', 'vytal_user_profile']
const isWeb = typeof window !== 'undefined' && typeof document !== 'undefined'
const secureGet = (key: string) => isWeb
  ? Promise.resolve(localStorage.getItem(key)) : SecureStore.getItemAsync(key)
const secureSet = (key: string, value: string) => isWeb
  ? Promise.resolve(localStorage.setItem(key, value)) : SecureStore.setItemAsync(key, value)
const secureDelete = (key: string) => isWeb
  ? Promise.resolve(localStorage.removeItem(key)) : SecureStore.deleteItemAsync(key)

// Serialize writes so a slow login/refresh cannot restore storage after logout.
let pendingWrite: Promise<void> = Promise.resolve()
function persist(session: AuthSession | null): Promise<void> {
  const operation = pendingWrite.then(async () => {
    if (session) await secureSet(SESSION_KEY, JSON.stringify(session))
    else await secureDelete(SESSION_KEY)
    await Promise.all(LEGACY_KEYS.map(secureDelete))
  })
  pendingWrite = operation.catch(() => {
    console.warn('Não foi possível atualizar o armazenamento seguro da sessão.')
  })
  return operation
}

const signedOut = {
  accessToken: null, refreshToken: null, userProfile: null,
  userId: null, isAuthenticated: false, isConnected: false,
}
let generation = 0

export const useAuthStore = create<AuthState>((set, get) => ({
  ...signedOut,

  setSession: async (session) => {
    const profile = profileFromResponse(session.userProfile)
    if (!session.accessToken?.trim() || !session.refreshToken?.trim()) throw new Error('Sessão inválida.')
    const version = ++generation
    try {
      await persist({ ...session, userProfile: profile })
    } catch (error) {
      if (version === generation) get().logout()
      throw error
    }
    if (version !== generation) throw new Error('A sessão mudou. Entre novamente.')
    // Publish identity and credentials together; never retain the previous profile.
    set({ ...session, userProfile: profile, userId: profile.user_id,
      isAuthenticated: true, isConnected: true })
  },

  setTokens: (access, refresh) => {
    if (!access?.trim() || !refresh?.trim()) throw new Error('Sessão inválida.')
    set({ accessToken: access, refreshToken: refresh })
    const profile = get().userProfile
    if (profile) void persist({ accessToken: access, refreshToken: refresh, userProfile: profile }).catch(() => {})
  },

  setProfile: (value) => {
    const profile = profileFromResponse(value)
    const state = get()
    if (!state.isAuthenticated || profile.user_id !== state.userId) throw new Error('A sessão mudou.')
    set({ userProfile: profile })
    void persist({ accessToken: state.accessToken!, refreshToken: state.refreshToken!,
      userProfile: profile }).catch(() => {})
  },

  logout: () => {
    ++generation
    set(signedOut)
    void persist(null).catch(() => {})
  },
  reset: () => get().logout(),

  initFromStorage: async () => {
    const version = generation
    try {
      const stored = await secureGet(SESSION_KEY)
      // Legacy profile is deliberately ignored: backend /me establishes ownership.
      const session = stored ? JSON.parse(stored) : {
        accessToken: await secureGet(LEGACY_KEYS[0]),
        refreshToken: await secureGet(LEGACY_KEYS[1]),
      }
      if (version !== generation) return
      if (typeof session?.accessToken !== 'string' || !session.accessToken.trim()
          || typeof session?.refreshToken !== 'string' || !session.refreshToken.trim()) {
        get().logout()
        return
      }
      set({ ...signedOut, accessToken: session.accessToken, refreshToken: session.refreshToken })
      const { api } = await import('../services/api')
      const { data } = await api.get('/users/me')
      if (version !== generation) return
      await get().setSession({ accessToken: get().accessToken!, refreshToken: get().refreshToken!,
        userProfile: profileFromResponse(data) })
    } catch {
      if (version === generation) get().logout()
    }
  },
}))
