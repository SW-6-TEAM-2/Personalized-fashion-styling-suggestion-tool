import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import LoadingSpinner from '../components/LoadingSpinner'
import useClosetStore from '../store/useClosetStore'
import { closetAPI } from '../api'

const BG = '#ffffff'
const CARD = '#f8f8f8'
const CARD2 = '#f2f2f2'
const BORDER = '#e8e8e8'
const TEXT = '#111111'
const DIM = '#999999'
const ACCENT = '#ff6b35'
const BTN_TEXT = '#ffffff'

const CATEGORIES = ['아우터', '상의', '원피스', '하의', 'acc']
const COLOR_TAGS = ['블랙', '화이트', '그레이', '네이비', '베이지', '브라운', '블루', '레드', '그린', '핑크']
const MATERIAL_TAGS = ['면', '폴리', '니트', '데님', '울', '린넨', '가죽']

export default function AddClothesPage() {
  const navigate = useNavigate()
  const { addCloth } = useClosetStore()
  const fileInputRef = useRef(null)

  const [step, setStep] = useState('upload') // upload | preview | saving
  const [originalFile, setOriginalFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [removedBgUrl, setRemovedBgUrl] = useState(null)
  const [form, setForm] = useState({
    name: '',
    category: '상의',
    colors: [],
    materials: [],
  })

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setOriginalFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setStep('removing')

    try {
      const formData = new FormData()
      formData.append('image', file)
      const res = await closetAPI.removeBackground(formData)
      setRemovedBgUrl(res.data.imageUrl)
      setStep('preview')
    } catch {
      // 백엔드 연동 전: 원본 이미지 그대로 사용
      setRemovedBgUrl(URL.createObjectURL(file))
      setStep('preview')
    }
  }

  const toggleTag = (type, tag) => {
    setForm((prev) => {
      const arr = prev[type]
      return {
        ...prev,
        [type]: arr.includes(tag) ? arr.filter((t) => t !== tag) : [...arr, tag],
      }
    })
  }

  const handleSave = async () => {
    if (!form.name.trim()) {
      alert('옷 이름을 입력해주세요.')
      return
    }
    setStep('saving')
    try {
      const formData = new FormData()
      formData.append('image', originalFile)
      formData.append('name', form.name)
      formData.append('category', form.category)
      formData.append('colors', JSON.stringify(form.colors))
      formData.append('materials', JSON.stringify(form.materials))
      const res = await closetAPI.add(formData)
      addCloth(res.data)
      navigate('/closet')
    } catch {
      alert('저장 중 오류가 발생했어요.')
      setStep('preview')
    }
  }

  if (step === 'removing') {
    return <LoadingSpinner message="누끼 따는 중..." />
  }
  if (step === 'saving') {
    return <LoadingSpinner message="옷장에 저장하는 중..." />
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: BG, display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      {/* 뒤로가기 버튼 */}
      <div style={{ padding: '16px 40px' }}>
        <button
          onClick={() => navigate('/closet')}
          style={{ color: DIM, fontSize: 13, background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
          onMouseEnter={e => e.currentTarget.style.color = TEXT}
          onMouseLeave={e => e.currentTarget.style.color = DIM}
        >
          ← 옷장으로
        </button>
      </div>

      {step === 'upload' ? (
        /* 업로드 영역 — 화면 꽉 채우기 */
        <div
          style={{
            flex: 1,
            margin: '0 40px 40px',
            border: `2px dashed ${BORDER}`,
            borderRadius: 20,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
            cursor: 'pointer',
            transition: 'border-color 0.2s',
          }}
          onClick={() => fileInputRef.current?.click()}
          onMouseEnter={e => e.currentTarget.style.borderColor = ACCENT}
          onMouseLeave={e => e.currentTarget.style.borderColor = BORDER}
        >
          <svg width="52" height="52" viewBox="0 0 24 24" fill="none">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke={ACCENT} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            <polyline points="17 8 12 3 7 8" stroke={ACCENT} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            <line x1="12" y1="3" x2="12" y2="15" stroke={ACCENT} strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <p style={{ color: TEXT, fontSize: 16, fontWeight: 600 }}>옷 사진 업로드</p>
          <p style={{ color: DIM, fontSize: 13 }}>클릭하거나 사진을 드래그하세요</p>
          <p style={{ color: DIM, fontSize: 11 }}>JPG, PNG, WEBP 지원</p>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
          />
        </div>
      ) : (
        /* 누끼 결과 + 정보 입력 */
        <div style={{ maxWidth: 760, margin: '0 auto', padding: '0 40px 40px', width: '100%' }}>
          <div className="flex gap-8">
            {/* 이미지 미리보기 */}
            <div className="flex-shrink-0">
              <div
                className="w-52 h-64 rounded-2xl flex items-center justify-center relative overflow-hidden"
                style={{ backgroundColor: CARD2, border: `1px solid ${BORDER}` }}
              >
                <img
                  src={removedBgUrl || previewUrl}
                  alt="미리보기"
                  className="w-full h-full object-contain p-4"
                />
                <button
                  onClick={() => {
                    setStep('upload')
                    setPreviewUrl(null)
                    setRemovedBgUrl(null)
                  }}
                  className="absolute bottom-3 right-3 p-2 rounded-full cursor-pointer transition-colors"
                  style={{ background: 'rgba(239,68,68,0.1)' }}
                  title="삭제"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              </div>
            </div>

            {/* 정보 입력 */}
            <div className="flex-1 flex flex-col gap-5">
              <div>
                <h2 style={{ color: TEXT, fontSize: 18, fontWeight: 600, marginBottom: 4 }}>{form.name || '옷 이름'}</h2>
                <span style={{ fontSize: 12, padding: '2px 10px', borderRadius: 20, backgroundColor: CARD, color: DIM }}>{form.category}</span>
              </div>

              {/* 이름 */}
              <div>
                <label style={{ color: DIM, fontSize: 12, display: 'block', marginBottom: 6 }}>옷 이름</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="예: 기본 흰 셔츠"
                  className="w-full outline-none"
                  style={{ backgroundColor: CARD, border: `1px solid ${BORDER}`, borderRadius: 12, padding: '10px 16px', color: TEXT, fontSize: 14 }}
                  onFocus={(e) => e.target.style.borderColor = ACCENT}
                  onBlur={(e) => e.target.style.borderColor = BORDER}
                />
              </div>

              {/* 카테고리 */}
              <div>
                <label style={{ color: DIM, fontSize: 12, display: 'block', marginBottom: 6 }}>카테고리</label>
                <div className="flex flex-wrap gap-2">
                  {CATEGORIES.map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setForm({ ...form, category: cat })}
                      className="cursor-pointer transition-colors"
                      style={{
                        padding: '6px 14px', borderRadius: 8, fontSize: 13, fontWeight: 500,
                        backgroundColor: form.category === cat ? ACCENT : CARD,
                        color: form.category === cat ? BTN_TEXT : DIM,
                        border: `1px solid ${form.category === cat ? ACCENT : BORDER}`,
                      }}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>

              {/* 색상 태그 */}
              <div>
                <label style={{ color: DIM, fontSize: 12, display: 'block', marginBottom: 6 }}>색상</label>
                <div className="flex flex-wrap gap-2">
                  {COLOR_TAGS.map((tag) => (
                    <button
                      key={tag}
                      onClick={() => toggleTag('colors', tag)}
                      className="cursor-pointer transition-colors"
                      style={{
                        padding: '5px 12px', borderRadius: 20, fontSize: 12,
                        backgroundColor: form.colors.includes(tag) ? `${ACCENT}20` : CARD,
                        color: form.colors.includes(tag) ? ACCENT : DIM,
                        border: `1px solid ${form.colors.includes(tag) ? ACCENT : BORDER}`,
                      }}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>

              {/* 소재 태그 */}
              <div>
                <label style={{ color: DIM, fontSize: 12, display: 'block', marginBottom: 6 }}>소재</label>
                <div className="flex flex-wrap gap-2">
                  {MATERIAL_TAGS.map((tag) => (
                    <button
                      key={tag}
                      onClick={() => toggleTag('materials', tag)}
                      className="cursor-pointer transition-colors"
                      style={{
                        padding: '5px 12px', borderRadius: 20, fontSize: 12,
                        backgroundColor: form.materials.includes(tag) ? `${ACCENT}20` : CARD,
                        color: form.materials.includes(tag) ? ACCENT : DIM,
                        border: `1px solid ${form.materials.includes(tag) ? ACCENT : BORDER}`,
                      }}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={handleSave}
                className="w-full cursor-pointer hover:opacity-90 transition-opacity mt-auto"
                style={{ backgroundColor: ACCENT, color: BTN_TEXT, fontWeight: 700, fontSize: 15, padding: '12px 0', borderRadius: 12, border: 'none' }}
              >
                옷장에 저장
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
