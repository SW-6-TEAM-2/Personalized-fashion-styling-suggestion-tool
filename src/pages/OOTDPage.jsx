import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import useAuthStore from '../store/useAuthStore'
import { ootdAPI } from '../api'

const BG = '#ffffff'
const PANEL = '#f8f8f8'
const PANEL_BORDER = '#e8e8e8'
const CARD = '#f2f2f2'
const BORDER = '#e8e8e8'
const TEXT = '#111111'
const DIM = '#999999'
const ACCENT = '#ff6b35'
const ACCENT_BTN = '#111111'
const BTN_TEXT = '#ffffff'
const TAG_BG = '#f2f2f2'

const GENRES = ['#캐주얼', '#미니멀', '#클래식', '#스트릿', '#워크웨어', '#시티보이']

export default function OOTDPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const name = user?.name || '사용자'

  const [selectedGenres, setSelectedGenres] = useState([])
  const [loading, setLoading] = useState(false)

  const toggleGenre = (genre) => {
    setSelectedGenres(prev =>
      prev.includes(genre) ? prev.filter(g => g !== genre) : [...prev, genre]
    )
  }

  const handleRecommend = async () => {
    setLoading(true)
    const keywords = [...selectedGenres]
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
            스타일 키워드를 골라주시면<br />
            딱 맞는 OOTD를 추천해드려요.
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
