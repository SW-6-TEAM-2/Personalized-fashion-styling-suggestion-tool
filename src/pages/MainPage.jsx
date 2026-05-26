import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import useAuthStore from '../store/useAuthStore'

const BG = '#0d0d0d'
const PANEL = '#131313'
const BORDER = '#282828'
const PANEL_BORDER = '#1a1a1a'
const TEXT = '#f0ece6'
const DIM = '#6b6b6b'
const ACCENT = '#ff6b35'
const ACCENT_BTN = '#ff6b35'
const BTN_TEXT = '#ffffff'
const TAG_BG = '#1a1a1a'

const STYLE_TAGS = ['#캐주얼', '#미니멀', '#스트릿', '#시티보이', '#오피스룩']

export default function MainPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const name = user?.name || '사용자'

  return (
    <div style={{ height: '100vh', backgroundColor: BG, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Navbar />

      <div
        className="flex items-stretch"
        style={{ flex: 1, minHeight: 0, padding: '0 0 0 140px' }}
      >
        {/* ── 왼쪽 ── */}
        <div className="flex-1 flex flex-col justify-center" style={{ padding: '54px 72px 54px 0' }}>
          <h1 style={{ color: TEXT, fontSize: 64, fontWeight: 700, lineHeight: 1.1, letterSpacing: '-0.03em', marginBottom: 16 }}>
            {name}님,<br />
            오늘은 어떤 스타일로<br />
            입고 싶으세요?
          </h1>
          <p style={{ color: DIM, fontSize: 16, lineHeight: 1.8, marginBottom: 28 }}>
            오늘의 날씨, 스타일 취향을 분석해<br />
            당신만의 OOTD를 추천해 드릴게요.
          </p>

          {/* 날씨 */}
          <div
            className="flex items-center gap-3"
            style={{ backgroundColor: '#161616', border: `1px solid ${BORDER}`, borderRadius: 12, padding: '10px 16px', marginBottom: 20, width: 'fit-content' }}
          >
            <span style={{ fontSize: 22 }}>⛅</span>
            <div>
              <p style={{ color: TEXT, fontSize: 15, fontWeight: 600 }}>--°</p>
              <p style={{ color: DIM, fontSize: 11 }}>Seoul • 날씨 불러오는 중</p>
            </div>
          </div>

          {/* 스타일 태그 */}
          <div className="flex flex-wrap gap-2">
            {STYLE_TAGS.map(tag => (
              <span
                key={tag}
                style={{
                  backgroundColor: TAG_BG,
                  color: DIM,
                  fontSize: 12,
                  padding: '5px 13px',
                  borderRadius: 20,
                  border: `1px solid ${BORDER}`,
                  cursor: 'pointer',
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* ── 오른쪽 패널 — 비주얼 전용 ── */}
        <div
          className="flex flex-col"
          style={{
            width: '45%',
            minWidth: 300,
            backgroundColor: PANEL,
            borderLeft: `1px solid ${PANEL_BORDER}`,
            padding: '40px 52px',
          }}
        >
          {/* 상단: 라벨 + stats */}
          <div className="flex items-center justify-between" style={{ marginBottom: 20, flexShrink: 0 }}>
            <p style={{ color: DIM, fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase' }}>
              Today's Look
            </p>
            <div className="flex gap-4">
              {['상의', '하의', '아우터', 'acc'].map(cat => (
                <div key={cat} className="flex flex-col items-center gap-1">
                  <span style={{ color: DIM, fontSize: 9 }}>{cat}</span>
                  <span style={{ color: TEXT, fontSize: 13, fontWeight: 700 }}>0</span>
                </div>
              ))}
            </div>
          </div>

          {/* 중앙: 일러스트 */}
          <div
            className="flex-1 flex items-center justify-center"
            style={{ minHeight: 0, overflow: 'hidden' }}
          >
            <img
              src="/trying-on-clothes.svg"
              alt="outfit illustration"
              style={{
                width: '100%',
                maxHeight: '100%',
                objectFit: 'contain',
                opacity: 0.85,
              }}
            />
          </div>

          {/* 하단: 버튼 */}
          <div style={{ paddingTop: 24, flexShrink: 0 }}>
            <button
              onClick={() => navigate('/ootd')}
              className="flex items-center justify-between cursor-pointer hover:opacity-90 transition-opacity"
              style={{
                width: '100%',
                backgroundColor: ACCENT_BTN,
                color: BTN_TEXT,
                fontSize: 14,
                fontWeight: 600,
                padding: '14px 20px',
                borderRadius: 10,
                border: 'none',
                cursor: 'pointer',
                marginBottom: 10,
              }}
            >
              OOTD 추천받기
              <span style={{ fontSize: 16 }}>→</span>
            </button>
            <button
              onClick={() => navigate('/closet')}
              style={{ color: DIM, fontSize: 12, display: 'block', textAlign: 'right', cursor: 'pointer', background: 'none', border: 'none', width: '100%' }}
            >
              내 옷장으로 가기 →
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
