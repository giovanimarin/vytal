import create from 'zustand'

interface AuthState {
  userId: string | null
  isConnected: boolean
  setUserId: (id: string) => void
  setConnected: (value: boolean) => void
  reset: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  userId: null,
  isConnected: false,
  setUserId: (id) => set({ userId: id }),
  setConnected: (value) => set({ isConnected: value }),
  reset: () => set({ userId: null, isConnected: false }),
}))
