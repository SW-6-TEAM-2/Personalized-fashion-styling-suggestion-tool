import { useNavigate, useLocation } from 'react-router-dom'
import useAuthStore from '../store/useAuthStore'

export default function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuthStore()

  const isActive = (path) => location.pathname.startsWith(path)

  return (
    <nav
      className="flex items-center justify-between sticky top-0 z-50"
      style={{ backgroundColor: '#0d0d0d', borderBottom: '1px solid #282828', padding: '14px 40px' }}
    >
      {/* 로고 */}
      <span
        className="font-logo cursor-pointer"
        style={{ fontSize: 26, fontWeight: 600, color: '#f8f2f0' }}
        onClick={() => navigate('/')}
      >
        dailycloset
      </span>

      {/* 네비 */}
      <div className="flex items-center gap-8">
        <button
          onClick={() => navigate('/closet')}
          className="cursor-pointer transition-all"
          style={{
            fontSize: 18,
            fontWeight: isActive('/closet') ? 600 : 400,
            color: isActive('/closet') ? '#ffffff' : '#f8f2f0',
            borderBottom: isActive('/closet') ? '2px solid #d44f1f' : '2px solid transparent',
            paddingBottom: 2,
          }}
        >
          My Closet
        </button>
        <button
          onClick={() => navigate('/ootd')}
          className="cursor-pointer transition-all"
          style={{
            fontSize: 18,
            fontWeight: isActive('/ootd') ? 600 : 400,
            color: isActive('/ootd') ? '#ffffff' : '#f8f2f0',
            borderBottom: isActive('/ootd') ? '2px solid #d44f1f' : '2px solid transparent',
            paddingBottom: 2,
          }}
        >
          OOTD
        </button>

        {/* 유저 아이콘 */}
        <button
          onClick={() => navigate('/profile')}
          className="cursor-pointer"
          style={{
            width: 36, height: 36,
            borderRadius: '50%',
            backgroundColor: '#1a1a1a',
            border: '1px solid #282828',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="8" r="4" stroke="#f8f2f0" strokeWidth="1.5" />
            <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="#f8f2f0" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      </div>
    </nav>
  )
}
