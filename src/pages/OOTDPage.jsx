import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import useAuthStore from '../store/useAuthStore'
import { ootdAPI } from '../api'

const BG = '#0d0d0d'
const PANEL = '#131313'
const PANEL_BORDER = '#1a1a1a'
const CARD = '#161616'
const BORDER = '#282828'
const TEXT = '#f0ece6'
const DIM = '#6b6b6b'
const ACCENT = '#ff6b35'
const ACCENT_BTN = '#ff6b35'
const BTN_TEXT = '#ffffff'
const TAG_BG = '#1a1a1a'

const GENRES = ['#캐주얼', '#미니멀', '#스트릿', '#시티보이', '#오피스룩']

export default function OOTDPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const name = user?.name || '사용자'

  const [selectedGenres, setSelectedGenres] = useState([])
  const [inputKeyword, setInputKeyword] = useState('')
  const [loading, setLoading] = useState(false)

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
      navigate('/ootd/result', { state: { outfit: res.data, keywords } })
    } catch {
      navigate('/ootd/result', { state: { outfit: [], keywords } })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ height: '100vh', backgroundColor: BG, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Navbar />

      <div
        className="flex items-stretch"
        style={{ flex: 1, minHeight: 0, padding: '0 0 0 140px' }}
      >
        <div className="flex-1 flex flex-col justify-center" style={{ padding: '54px 140px 54px 0', maxWidth: 860 }}>
          <h1 style={{ color: TEXT, fontSize: 72, fontWeight: 700, lineHeight: 1.1, letterSpacing: '-0.03em', marginBottom: 20 }}>
            오늘은 어떤<br />
            무드예요?
          </h1>
          <p style={{ color: DIM, fontSize: 18, lineHeight: 1.8, marginBottom: 40 }}>
            스타일 키워드를 고르거나<br />
            직접 입력하면 OOTD를 추천해드려요.
          </p>

          {/* 스타일 태그 */}
          <div className="flex flex-wrap gap-3" style={{ marginBottom: 32 }}>
            {GENRES.map(genre => {
              const active = selectedGenres.includes(genre)
              return (
                <button
                  key={genre}
                  onClick={() => toggleGenre(genre)}
                  className="cursor-pointer transition-all"
                  style={{
                    padding: '10px 22px',
                    borderRadius: 20,
                    fontSize: 15,
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

          {/* 키워드 직접 입력 */}
          <div
            className="flex items-center gap-3"
            style={{
              backgroundColor: CARD,
              border: `1px solid ${BORDER}`,
              borderRadius: 16,
              padding: '16px 20px',
              marginBottom: 20,
            }}
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
                fontSize: 16,
                border: 'none',
              }}
            />
            <button
              onClick={handleRecommend}
              disabled={loading}
              className="flex items-center justify-center cursor-pointer disabled:opacity-60 hover:opacity-80 transition-opacity"
              style={{
                backgroundColor: ACCENT_BTN,
                color: BTN_TEXT,
                border: 'none',
                borderRadius: 10,
                width: 40,
                height: 40,
                flexShrink: 0,
              }}
            >
              {loading ? (
                <div style={{ width: 16, height: 16, border: `2px solid ${BTN_TEXT}`, borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M5 12h14M13 6l6 6-6 6" stroke={BTN_TEXT} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </button>
          </div>

          {/* CTA 버튼 */}
          <button
            onClick={handleRecommend}
            disabled={loading}
            className="flex items-center justify-between cursor-pointer hover:opacity-90 transition-opacity disabled:opacity-60"
            style={{
              width: '100%',
              backgroundColor: ACCENT_BTN,
              color: BTN_TEXT,
              fontWeight: 600,
              fontSize: 16,
              padding: '16px 24px',
              borderRadius: 12,
              border: 'none',
            }}
          >
            {loading ? '추천 중...' : '오늘의 OOTD 추천받기'}
            {!loading && <span style={{ fontSize: 20 }}>→</span>}
          </button>
        </div>

        {/* ── 오른쪽 패널 — 플랫레이 이미지 ── */}
        <div
          className="flex items-center justify-center"
          style={{
            width: '45%',
            minWidth: 300,
            backgroundColor: PANEL,
            borderLeft: `1px solid ${PANEL_BORDER}`,
            overflow: 'hidden',
          }}
        >
          <img
            src="/remove_background (6).png"
            alt="outfit flatlay"
            style={{
              width: '85%',
              height: '85%',
              objectFit: 'contain',
              padding: '24px',
            }}
          />
        </div>
      </div>
    </div>
  )
}
