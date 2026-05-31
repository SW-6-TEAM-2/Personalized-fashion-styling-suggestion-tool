import { useNavigate, useLocation } from 'react-router-dom'
import useAuthStore from '../store/useAuthStore'

// ── C안: White + Dark Charcoal + Orange ──
const BG     = '#ffffff'
const PANEL  = '#f8f8f8'
const PANEL_BORDER = '#e8e8e8'
const BORDER = '#e8e8e8'
const NAV_BG = '#ffffff'
const TEXT   = '#111111'
const DIM    = '#999999'
const ACCENT     = '#ff6b35'
const ACCENT_BTN = '#111111'
const BTN_TEXT   = '#ffffff'
const TAG_BG = '#f2f2f2'

const STYLE_TAGS = ['#캐주얼', '#미니멀', '#스트릿', '#시티보이', '#오피스룩']

export default function MainPageLight() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuthStore()
  const name = user?.name || '사용자'

  const isActive = (path) => location.pathname.startsWith(path)

  return (
    <div style={{ height: '100vh', backgroundColor: BG, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

      {/* ── 네비바 ── */}
      <nav
        className="flex items-center justify-between sticky top-0 z-50"
        style={{ backgroundColor: NAV_BG, borderBottom: `1px solid ${BORDER}`, padding: '14px 40px' }}
      >
        <span
          className="font-logo cursor-pointer"
          style={{ fontSize: 26, fontWeight: 600, color: TEXT }}
          onClick={() => navigate('/')}
        >
          dailycloset
        </span>
        <div className="flex items-center gap-8">
          {[{ label: 'My Closet', path: '/closet' }, { label: 'OOTD', path: '/ootd' }].map(({ label, path }) => (
            <button
              key={path}
              onClick={() => navigate(path)}
              className="cursor-pointer transition-all"
              style={{
                fontSize: 18,
                fontWeight: isActive(path) ? 600 : 400,
                color: TEXT,
                background: 'none',
                border: 'none',
                borderBottom: isActive(path) ? `2px solid ${ACCENT}` : '2px solid transparent',
                paddingBottom: 2,
              }}
            >
              {label}
            </button>
          ))}
          <button
            onClick={() => navigate('/profile')}
            className="cursor-pointer"
            style={{
              width: 36, height: 36,
              borderRadius: '50%',
              backgroundColor: TAG_BG,
              border: `1px solid ${BORDER}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="8" r="4" stroke={TEXT} strokeWidth="1.5" />
              <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke={TEXT} strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      </nav>

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
            style={{ backgroundColor: TAG_BG, border: `1px solid ${BORDER}`, borderRadius: 12, padding: '10px 16px', marginBottom: 20, width: 'fit-content' }}
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

        {/* ── 오른쪽 패널 ── */}
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
