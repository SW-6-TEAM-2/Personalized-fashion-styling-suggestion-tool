import { useState } from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import useAuthStore from '../store/useAuthStore'
import { authAPI } from '../api'

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const BG = '#181d22'
const CARD = '#22292f'
const BORDER = '#2e3a42'
const TEXT = '#f8f2f0'
const DIM = '#8a9ba8'
const ACCENT = '#93fffd'
const BTN_TEXT = '#4a4543'

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
    <div className="min-h-screen flex" style={{ backgroundColor: BG }}>
      {/* 왼쪽 */}
      <div className="flex-1 flex flex-col justify-center px-20 py-12">
        <p style={{ color: DIM, fontSize: 14, marginBottom: 16 }}>dailycloset</p>
        <h1 style={{ color: TEXT, fontSize: 48, fontWeight: 700, lineHeight: 1.2, marginBottom: 20 }}>
          사용자님,<br />
          오늘은 어떤 스타일로<br />
          입고 싶으세요?
        </h1>
        <p style={{ color: DIM, fontSize: 14, lineHeight: 1.8 }}>
          오늘의 날씨, 스타일 취향을 분석해<br />
          당신만의 OOTD를 추천해 드릴게요.
        </p>

        {/* 스타일 태그 */}
        <div className="flex flex-wrap gap-2 mt-10">
          {['#캐주얼', '#미니멀', '#스트릿', '#시티보이', '#오피스룩'].map(tag => (
            <span
              key={tag}
              style={{
                backgroundColor: '#526767',
                color: '#ffffff',
                fontSize: 13,
                padding: '6px 14px',
                borderRadius: 20,
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* 오른쪽 - 로그인 폼 */}
      <div className="flex items-center justify-center w-full max-w-md px-8 py-12">
        <div
          className="w-full rounded-2xl p-8"
          style={{ backgroundColor: CARD, border: `1px solid ${BORDER}` }}
        >
          <h2 style={{ color: TEXT, fontSize: 22, fontWeight: 700, marginBottom: 4 }}>로그인</h2>
          <p style={{ color: DIM, fontSize: 13, marginBottom: 28 }}>dailycloset에 오신걸 환영해요</p>

          {signupSuccess && (
            <div
              className="px-4 py-3 rounded-xl text-sm mb-5"
              style={{ backgroundColor: '#93fffd18', border: `1px solid #93fffd40`, color: ACCENT }}
            >
              회원가입이 완료됐어요! 로그인해주세요.
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {[
              { label: '이메일', name: 'email', type: 'email', placeholder: 'example@email.com' },
              { label: '비밀번호', name: 'password', type: 'password', placeholder: '비밀번호를 입력하세요' },
            ].map(({ label, name, type, placeholder }) => (
              <div key={name}>
                <label style={{ color: DIM, fontSize: 12, display: 'block', marginBottom: 6 }}>{label}</label>
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
                    padding: '12px 16px',
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
              className="w-full rounded-xl font-semibold cursor-pointer disabled:opacity-60 transition-opacity hover:opacity-90 flex items-center justify-center gap-2"
              style={{
                backgroundColor: ACCENT,
                color: BTN_TEXT,
                fontSize: 15,
                padding: '13px 0',
                marginTop: 8,
                border: 'none',
              }}
            >
              {loading ? '로그인 중...' : (
                <>오늘의 OOTD 추천받기 <span style={{ fontSize: 18 }}>→</span></>
              )}
            </button>
          </form>

          <p style={{ textAlign: 'center', color: DIM, fontSize: 12, marginTop: 20 }}>
            아직 계정이 없으신가요?{' '}
            <Link to="/signup" style={{ color: ACCENT }}>회원가입</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
