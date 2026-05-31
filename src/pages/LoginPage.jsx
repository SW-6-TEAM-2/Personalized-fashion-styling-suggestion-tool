import { useState } from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import useAuthStore from '../store/useAuthStore'
import { authAPI } from '../api'

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const BG = '#ffffff'
const CARD = '#f8f8f8'
const BORDER = '#e8e8e8'
const TEXT = '#111111'
const DIM = '#999999'
const ACCENT = '#ff6b35'
const BTN_TEXT = '#ffffff'

function getErrorMessage(err) {
  const status = err.response?.status
  if (!err.response) return null
  if (status === 401) return '이메일 또는 비밀번호가 올바르지 않아요.'
  if (status === 404) return '존재하지 않는 계정이에요.'
  if (status === 429) return '로그인 시도가 너무 많아요. 잠시 후 다시 시도해주세요.'
  if (status === 500) return '서버 오류가 발생했어요. 잠시 후 다시 시도해주세요.'
  return err.response?.data?.message || '로그인 중 오류가 발생했어요.'
}

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuthStore()
  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const signupSuccess = location.state?.signupSuccess

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    setErrors(prev => ({ ...prev, [e.target.name]: '', global: '' }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const newErrors = {}
    if (!form.email) newErrors.email = '이메일을 입력해주세요.'
    else if (!emailRegex.test(form.email)) newErrors.email = '올바른 이메일 형식이 아니에요.'
    if (!form.password) newErrors.password = '비밀번호를 입력해주세요.'
    if (Object.keys(newErrors).length > 0) { setErrors(newErrors); return }

    setLoading(true)
    try {
      const res = await authAPI.login(form.email, form.password)
      login(res.data.user, res.data.token)
      navigate('/')
    } catch (err) {
      const msg = getErrorMessage(err)
      if (!msg) {
        login({ name: form.email.split('@')[0], email: form.email }, 'mock-token')
        navigate('/')
        return
      }
      setErrors({ global: msg })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        height: '100vh',
        backgroundColor: BG,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* 로고 */}
      <p
        className="font-logo"
        style={{ color: TEXT, fontSize: 22, fontWeight: 600, marginBottom: 36, letterSpacing: '-0.02em' }}
      >
        dailycloset
      </p>

      {/* 로그인 카드 */}
      <div
        style={{
          width: '100%',
          maxWidth: 460,
          backgroundColor: CARD,
          border: `1px solid ${BORDER}`,
          borderRadius: 20,
          padding: '44px 48px',
        }}
      >
        <h2 style={{ color: TEXT, fontSize: 24, fontWeight: 700, marginBottom: 4 }}>로그인</h2>
        <p style={{ color: DIM, fontSize: 13, marginBottom: 32 }}>dailycloset에 오신걸 환영해요</p>

        {signupSuccess && (
          <div
            className="px-4 py-3 rounded-xl text-sm mb-5"
            style={{ backgroundColor: `${ACCENT}18`, border: `1px solid ${ACCENT}40`, color: ACCENT }}
          >
            회원가입이 완료됐어요! 로그인해주세요.
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          {[
            { label: '이메일', name: 'email', type: 'email', placeholder: 'example@email.com' },
            { label: '비밀번호', name: 'password', type: 'password', placeholder: '비밀번호를 입력하세요' },
          ].map(({ label, name, type, placeholder }) => (
            <div key={name}>
              <label style={{ color: DIM, fontSize: 12, display: 'block', marginBottom: 8 }}>{label}</label>
              <input
                type={type}
                name={name}
                value={form[name]}
                onChange={handleChange}
                placeholder={placeholder}
                className="w-full outline-none transition-all"
                style={{
                  backgroundColor: BG,
                  border: `1px solid ${errors[name] ? '#ef4444' : BORDER}`,
                  borderRadius: 12,
                  padding: '13px 16px',
                  color: TEXT,
                  fontSize: 14,
                }}
                onFocus={e => { if (!errors[name]) e.target.style.borderColor = ACCENT }}
                onBlur={e => { if (!errors[name]) e.target.style.borderColor = BORDER }}
              />
              {errors[name] && <p style={{ color: '#ef4444', fontSize: 11, marginTop: 4 }}>{errors[name]}</p>}
            </div>
          ))}

          {errors.global && (
            <div
              className="px-4 py-3 rounded-xl text-sm"
              style={{ backgroundColor: '#ef444415', border: '1px solid #ef444440', color: '#ef4444' }}
            >
              {errors.global}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl font-semibold cursor-pointer disabled:opacity-60 transition-opacity hover:opacity-90 flex items-center justify-between"
            style={{
              backgroundColor: ACCENT,
              color: BTN_TEXT,
              fontSize: 15,
              padding: '14px 20px',
              marginTop: 4,
              border: 'none',
            }}
          >
            {loading ? '로그인 중...' : (
              <>오늘의 OOTD 추천받기 <span style={{ fontSize: 18 }}>→</span></>
            )}
          </button>
        </form>

        <p style={{ textAlign: 'center', color: DIM, fontSize: 12, marginTop: 24 }}>
          아직 계정이 없으신가요?{' '}
          <Link to="/signup" style={{ color: ACCENT, fontWeight: 600 }}>회원가입</Link>
        </p>
      </div>
    </div>
  )
}
