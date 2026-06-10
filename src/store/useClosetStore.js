import { create } from 'zustand'

const useClosetStore = create((set) => ({
  clothes: [],
  selectedCategory: '전체',

  setClothes: (clothes) => set({ clothes }),

  addCloth: (item) => set((state) => ({
    clothes: [...state.clothes, item],
  })),

  removeCloth: (id) => set((state) => ({
    clothes: state.clothes.filter((c) => c.id !== id),
  })),

  setCategory: (category) => set({ selectedCategory: category }),

  getFiltered: (state) => {
    if (state.selectedCategory === '전체') return state.clothes
    return state.clothes.filter((c) => c.category === state.selectedCategory)
  },
}))

export default useClosetStore
