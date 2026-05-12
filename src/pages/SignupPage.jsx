import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import useAuthStore from '../store/useAuthStore'
import { authAPI } from '../api'

const BG = '#181d22'
const CARD = '#22292f'
const BORDER = '#2e3a42'
const TEXT = '#f8f2f0'
const DIM = '#8a9ba8'
const ACCENT = '#93fffd'
const BTN_TEXT = '#4a4543'

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function getErrorMessage(err) {
  const status = err.response?.status
  const serverMsg = err.response?.data?.message
  if (!err.response) return '서버에 연결할 수 없어요.'
  if (status === 409) return '이미 사용 중인 이메일이에요.'
  if (status === 400) return serverMsg || '입력값을 다시 확인해주세요.'
  if (status === 500) return '서버 오류가 발생했어요. 잠시 후 다시 시도해주세요.'
  return serverMsg || '회원가입 중 오류가 발생했어요.'
}

export default function SignupPage() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)

  const validate = () => {
    const e = {}
    if (!form.name.trim()) e.name = '이름을 입력해주세요.'
    if (!form.email) e.email = '이메일을 입력해주세요.'
    else if (!emailRegex.test(form.email)) e.email = '올바른 이메일 형식이 아니에요.'
    if (!form.password) e.password = '비밀번호를 입력해주세요.'
    else if (form.password.length < 6) e.password = '비밀번호는 6자 이상이어야 해요.'
    if (!form.confirm) e.confirm = '비밀번호 확인을 입력해주세요.'
    else if (form.password !== form.confirm) e.confirm = '비밀번호가 일치하지 않아요.'
    return e
  }

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    setErrors(prev => ({ ...prev, [e.target.name]: '', global: '' }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const ve = validate()
    if (Object.keys(ve).length > 0) { setErrors(ve); return }
    setLoading(true)
    try {
      await authAPI.signup(form.name, form.email, form.password)
      navigate('/login', { state: { signupSuccess: true } })
    } catch (err) {
      if (!err.response) {
        login({ name: form.name, email: form.email }, 'mock-token')
        navigate('/')
        return
      }
      setErrors({ global: getErrorMessage(err) })
    } finally {
      setLoading(false)
    }
  }

  const fields = [
    { label: '이름', name: 'name', type: 'text', placeholder: '홍길동' },
    { label: '이메일', name: 'email', type: 'email', placeholder: 'example@email.com' },
    { label: '비밀번호', name: 'password', type: 'password', placeholder: '6자 이상 입력하세요' },
    { label: '비밀번호 확인', name: 'confirm', type: 'password', placeholder: '비밀번호를 다시 입력하세요' },
  ]

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: BG }}>
      <div className="w-full max-w-md mx-4 rounded-2xl p-8" style={{ backgroundColor: CARD, border: `1px solid ${BORDER}` }}>
        <h2 style={{ color: TEXT, fontSize: 22, fontWeight: 700, marginBottom: 4 }}>회원가입</h2>
        <p style={{ color: DIM, fontSize: 13, marginBottom: 24 }}>나만의 옷장을 만들어보세요</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {fields.map(({ label, name, type, placeholder }) => (
            <div key={name}>
              <label style={{ color: DIM, fontSize: 12, display: 'block', marginBottom: 6 }}>{label}</label>
              <input
                type={type}
                name={name}
                value={form[name]}
                onChange={handleChange}
                placeholder={placeholder}
                className="w-full outline-none"
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
            <div style={{ backgroundColor: '#ef444415', border: '1px solid #ef444440', borderRadius: 12, padding: '12px 16px', color: '#ef4444', fontSize: 13 }}>
              {errors.global}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full cursor-pointer disabled:opacity-60 hover:opacity-90 transition-opacity"
            style={{
              backgroundColor: ACCENT, color: BTN_TEXT,
              fontWeight: 600, fontSize: 15,
              padding: '13px 0', borderRadius: 12, border: 'none', marginTop: 4,
            }}
          >
            {loading ? '처리 중...' : '회원가입'}
          </button>
        </form>

        <p style={{ textAlign: 'center', color: DIM, fontSize: 12, marginTop: 20 }}>
          이미 계정이 있으신가요?{' '}
          <Link to="/login" style={{ color: ACCENT }}>로그인</Link>
        </p>
      </div>
    </div>
  )
}
