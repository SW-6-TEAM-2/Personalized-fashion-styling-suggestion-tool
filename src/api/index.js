import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const stored = localStorage.getItem('auth-storage')
  if (stored) {
    const { state } = JSON.parse(stored)
    if (state?.token) {
      config.headers.Authorization = `Bearer ${state.token}`
    }
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth-storage')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  signup: (name, email, password) => api.post('/auth/signup', { name, email, password }),
  getProfile: () => api.get('/auth/me'),
}

export const closetAPI = {
  getAll: () => api.get('/closet'),
  getOne: (id) => api.get(`/closet/${id}`),
  add: (formData) => api.post('/closet', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  delete: (id) => api.delete(`/closet/${id}`),
  removeBackground: (formData) => api.post('/closet/remove-bg', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
}

export const ootdAPI = {
  recommend: (keywords) => api.post('/ootd/recommend', { keywords }),
  refresh: (category) => api.post('/ootd/refresh', { category }),
}

export default api
