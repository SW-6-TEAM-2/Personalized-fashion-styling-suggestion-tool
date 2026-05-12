import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useAuthStore = create(
  persist(
    (set) => ({
      isLoggedIn: false,
      user: null,
      token: null,

      login: (userData, token) => set({
        isLoggedIn: true,
        user: userData,
        token,
      }),

      logout: () => set({
        isLoggedIn: false,
        user: null,
        token: null,
      }),

      updateUser: (userData) => set((state) => ({
        user: { ...state.user, ...userData },
      })),
    }),
    { name: 'auth-storage' }
  )
)

export default useAuthStore
