import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import useAuthStore from '../store/useAuthStore'

export default function ProfilePage() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#111111' }}>
      <Navbar />

      <div className="max-w-xl mx-auto px-6 py-10">
        <h2 className="text-white text-lg font-semibold mb-8">프로필</h2>

        <div
          className="rounded-2xl p-6 mb-4"
          style={{ backgroundColor: '#1C1C1C', border: '1px solid #2A2A2A' }}
        >
          {/* 아바타 */}
          <div className="flex items-center gap-4 mb-6">
            <div
              className="w-14 h-14 rounded-full flex items-center justify-center"
              style={{ backgroundColor: '#2A2A2A' }}
            >
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="8" r="4" stroke="#9CA3AF" strokeWidth="1.5" />
                <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="#9CA3AF" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </div>
            <div>
              <p className="text-white font-medium">{user?.name || '사용자'}</p>
              <p className="text-gray-500 text-sm">{user?.email || ''}</p>
            </div>
          </div>

          {/* 정보 */}
          {[
            { label: '이름', value: user?.name },
            { label: '이메일', value: user?.email },
          ].map(({ label, value }) => (
            <div
              key={label}
              className="flex justify-between py-3"
              style={{ borderBottom: '1px solid #2A2A2A' }}
            >
              <span className="text-gray-500 text-sm">{label}</span>
              <span className="text-white text-sm">{value || '-'}</span>
            </div>
          ))}
        </div>

        <button
          onClick={handleLogout}
          className="w-full py-3 rounded-xl text-red-400 font-medium text-sm cursor-pointer hover:opacity-80 transition-opacity"
          style={{ backgroundColor: 'transparent', border: '1px solid #2A2A2A' }}
        >
          로그아웃
        </button>
      </div>
    </div>
  )
}
