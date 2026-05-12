import { Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from './store/useAuthStore'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import MainPage from './pages/MainPage'
import ClosetPage from './pages/ClosetPage'
import AddClothesPage from './pages/AddClothesPage'
import ClothesDetailPage from './pages/ClothesDetailPage'
import OOTDPage from './pages/OOTDPage'
import OOTDResultPage from './pages/OOTDResultPage'
import ProfilePage from './pages/ProfilePage'

function ProtectedRoute({ children }) {
  const { isLoggedIn } = useAuthStore()
  return isLoggedIn ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/" element={<ProtectedRoute><MainPage /></ProtectedRoute>} />
      <Route path="/closet" element={<ProtectedRoute><ClosetPage /></ProtectedRoute>} />
      <Route path="/closet/add" element={<ProtectedRoute><AddClothesPage /></ProtectedRoute>} />
      <Route path="/closet/:id" element={<ProtectedRoute><ClothesDetailPage /></ProtectedRoute>} />
      <Route path="/ootd" element={<ProtectedRoute><OOTDPage /></ProtectedRoute>} />
      <Route path="/ootd/result" element={<ProtectedRoute><OOTDResultPage /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
