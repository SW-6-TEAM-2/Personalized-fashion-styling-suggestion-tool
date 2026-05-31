import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import useAuthStore from '../store/useAuthStore'

const BG = '#ffffff'
const CARD = '#f8f8f8'
const BORDER = '#e8e8e8'
const TAG_BG = '#f2f2f2'
const TEXT = '#111111'
const DIM = '#999999'

export default function ProfilePage() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: BG }}>
      <Navbar />

      <div className="max-w-xl mx-auto px-6 py-10">
        <h2 style={{ color: TEXT, fontSize: 18, fontWeight: 700, marginBottom: 32 }}>프로필</h2>

        <div
          className="rounded-2xl p-6 mb-4"
          style={{ backgroundColor: CARD, border: `1px solid ${BORDER}` }}
        >
          {/* 아바타 */}
          <div className="flex items-center gap-4 mb-6">
            <div
              className="w-14 h-14 rounded-full flex items-center justify-center"
              style={{ backgroundColor: TAG_BG, border: `1px solid ${BORDER}` }}
            >
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="8" r="4" stroke={DIM} strokeWidth="1.5" />
                <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke={DIM} strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </div>
            <div>
              <p style={{ color: TEXT, fontWeight: 600, fontSize: 15 }}>{user?.name || '사용자'}</p>
              <p style={{ color: DIM, fontSize: 13 }}>{user?.email || ''}</p>
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
              style={{ borderBottom: `1px solid ${BORDER}` }}
            >
              <span style={{ color: DIM, fontSize: 13 }}>{label}</span>
              <span style={{ color: TEXT, fontSize: 13 }}>{value || '-'}</span>
            </div>
          ))}
        </div>

        <button
          onClick={handleLogout}
          className="w-full py-3 rounded-xl font-medium text-sm cursor-pointer hover:opacity-80 transition-opacity"
          style={{ backgroundColor: 'transparent', color: '#ef4444', border: `1px solid #fca5a5` }}
        >
          로그아웃
        </button>
      </div>
    </div>
  )
}
