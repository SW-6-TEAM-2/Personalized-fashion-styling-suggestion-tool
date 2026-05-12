import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import useAuthStore from '../store/useAuthStore'
import useClosetStore from '../store/useClosetStore'
import { ootdAPI, closetAPI } from '../api'

const BG = '#181d22'
const CARD = '#22292f'
const BORDER = '#2e3a42'
const TEXT = '#f8f2f0'
const DIM = '#8a9ba8'
const ACCENT = '#93fffd'
const BTN_TEXT = '#4a4543'
const TAG_BG = '#2e3a42'
const TAG_ACTIVE = '#93fffd'

const GENRES = ['#캐주얼', '#미니멀', '#스트릿', '#시티보이', '#오피스룩']

export default function OOTDPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const { clothes } = useClosetStore()
  const name = user?.name || '사용자'

  const [selectedGenres, setSelectedGenres] = useState([])
  const [inputKeyword, setInputKeyword] = useState('')
  const [loading, setLoading] = useState(false)
  const [previewItems, setPreviewItems] = useState([])

  useEffect(() => {
    // 옷장에서 랜덤으로 최대 4개 미리보기
    if (clothes.length > 0) {
      const shuffled = [...clothes].sort(() => Math.random() - 0.5)
      setPreviewItems(shuffled.slice(0, 4))
    } else {
      closetAPI.getAll()
        .then(res => {
          const shuffled = [...res.data].sort(() => Math.random() - 0.5)
          setPreviewItems(shuffled.slice(0, 4))
        })
        .catch(() => setPreviewItems([]))
    }
  }, [])

  const toggleGenre = (genre) => {
    setSelectedGenres(prev =>
      prev.includes(genre) ? prev.filter(g => g !== genre) : [...prev, genre]
    )
  }

  const handleRecommend = async () => {
    setLoading(true)
    const keywords = [
      ...selectedGenres,
      ...inputKeyword.split(/[\s,]+/).filter(Boolean),
    ]
    try {
      const res = await ootdAPI.recommend({ keywords })
      navigate('/ootd/result', { state: { outfit: res.data } })
    } catch {
      navigate('/ootd/result', { state: { outfit: [] } })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: BG }}>
      <Navbar />

      <div
        className="flex items-center"
        style={{ minHeight: 'calc(100vh - 73px)', padding: '40px 80px', gap: 60 }}
      >
        {/* 왼쪽 */}
        <div className="flex-1 flex flex-col justify-center">
          <p style={{ color: DIM, fontSize: 14, marginBottom: 12 }}>dailycloset</p>

          <h1 style={{ color: TEXT, fontSize: 48, fontWeight: 700, lineHeight: 1.2, marginBottom: 16 }}>
            {name}님,<br />
            오늘은 어떤 스타일로<br />
            입고 싶으세요?
          </h1>

          <p style={{ color: DIM, fontSize: 14, lineHeight: 1.8, marginBottom: 40 }}>
            원하는 스타일 키워드를 선택하거나<br />
            직접 입력하면 OOTD를 추천해드려요.
          </p>

          {/* 장르 태그 */}
          <div style={{ marginBottom: 28 }}>
            <p style={{ color: DIM, fontSize: 12, marginBottom: 12 }}>스타일 장르</p>
            <div className="flex flex-wrap gap-2">
              {GENRES.map(genre => {
                const active = selectedGenres.includes(genre)
                return (
                  <button
                    key={genre}
                    onClick={() => toggleGenre(genre)}
                    className="cursor-pointer transition-all"
                    style={{
                      padding: '8px 18px',
                      borderRadius: 20,
                      fontSize: 13,
                      fontWeight: active ? 600 : 400,
                      backgroundColor: active ? ACCENT : TAG_BG,
                      color: active ? BTN_TEXT : DIM,
                      border: `1px solid ${active ? ACCENT : BORDER}`,
                    }}
                  >
                    {genre}
                  </button>
                )
              })}
            </div>
          </div>

          {/* 키워드 직접 입력 */}
          <div style={{ marginBottom: 36 }}>
            <p style={{ color: DIM, fontSize: 12, marginBottom: 12 }}>원하는 스타일이 있으신가요?</p>
            <div
              className="flex items-center gap-3"
              style={{
                backgroundColor: CARD,
                border: `1px solid ${BORDER}`,
                borderRadius: 14,
                padding: '14px 18px',
              }}
              onFocus={e => e.currentTarget.style.borderColor = ACCENT}
              onBlur={e => e.currentTarget.style.borderColor = BORDER}
            >
              <input
                type="text"
                value={inputKeyword}
                onChange={e => setInputKeyword(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleRecommend()}
                placeholder="예) 데이트룩, 출근룩, 편한 스타일..."
                className="flex-1 outline-none"
                style={{
                  backgroundColor: 'transparent',
                  color: TEXT,
                  fontSize: 14,
                  border: 'none',
                }}
              />
              <button
                onClick={handleRecommend}
                disabled={loading}
                className="flex items-center justify-center cursor-pointer disabled:opacity-60 transition-opacity hover:opacity-80"
                style={{
                  backgroundColor: ACCENT,
                  color: BTN_TEXT,
                  border: 'none',
                  borderRadius: 10,
                  width: 36,
                  height: 36,
                  flexShrink: 0,
                }}
              >
                {loading ? (
                  <div style={{ width: 16, height: 16, border: `2px solid ${BTN_TEXT}`, borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M5 12h14M13 6l6 6-6 6" stroke={BTN_TEXT} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* 추천받기 버튼 */}
          <button
            onClick={handleRecommend}
            disabled={loading}
            className="flex items-center gap-2 cursor-pointer hover:opacity-90 transition-opacity disabled:opacity-60 w-fit"
            style={{
              backgroundColor: ACCENT,
              color: BTN_TEXT,
              fontWeight: 600,
              fontSize: 15,
              padding: '13px 28px',
              borderRadius: 12,
              border: 'none',
            }}
          >
            {loading ? '추천 중...' : <>오늘의 OOTD 추천받기 <span style={{ fontSize: 18 }}>→</span></>}
          </button>
        </div>

        {/* 오른쪽 - 옷장 이미지 랜덤 미리보기 */}
        <div style={{ width: '42%', minWidth: 340 }}>
          <div
            className="rounded-2xl overflow-hidden"
            style={{
              backgroundColor: CARD,
              border: `1px solid ${BORDER}`,
              padding: 24,
              minHeight: 480,
            }}
          >
            <p style={{ color: DIM, fontSize: 12, marginBottom: 16 }}>내 옷장에서 랜덤 추천</p>

            {previewItems.length > 0 ? (
              <div className="grid grid-cols-2 gap-3" style={{ height: 400 }}>
                {previewItems.map((item, i) => (
                  <div
                    key={item.id || i}
                    className="rounded-xl overflow-hidden flex items-center justify-center"
                    style={{ backgroundColor: '#2a3138', border: `1px solid ${BORDER}` }}
                  >
                    {item.imageUrl ? (
                      <img
                        src={item.imageUrl}
                        alt={item.name}
                        className="w-full h-full object-contain"
                        style={{ maxHeight: 180 }}
                      />
                    ) : (
                      <div className="flex flex-col items-center gap-2">
                        <span style={{ fontSize: 32 }}>👕</span>
                        <span style={{ color: DIM, fontSize: 11 }}>{item.name}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div
                className="flex flex-col items-center justify-center gap-4 rounded-xl"
                style={{ height: 400, backgroundColor: '#2a3138', border: `1px solid ${BORDER}` }}
              >
                <span style={{ fontSize: 48 }}>👗</span>
                <p style={{ color: DIM, fontSize: 13, textAlign: 'center', lineHeight: 1.6 }}>
                  옷장에 옷을 추가하면<br />
                  여기서 랜덤으로 보여드려요
                </p>
                <button
                  onClick={() => navigate('/closet/add')}
                  style={{
                    backgroundColor: ACCENT,
                    color: BTN_TEXT,
                    fontSize: 13,
                    fontWeight: 600,
                    padding: '8px 18px',
                    borderRadius: 8,
                    border: 'none',
                    cursor: 'pointer',
                  }}
                >
                  옷 추가하기
                </button>
              </div>
            )}
          </div>

          <button
            onClick={() => navigate('/closet')}
            style={{ color: DIM, fontSize: 12, marginTop: 10, display: 'block', textAlign: 'right', cursor: 'pointer', background: 'none', border: 'none', width: '100%' }}
          >
            내 옷장으로 가기 →
          </button>
        </div>
      </div>
    </div>
  )
}
