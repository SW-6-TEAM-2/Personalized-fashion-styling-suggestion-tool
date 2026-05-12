import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import useAuthStore from '../store/useAuthStore'

const BG = '#181d22'
const CARD = '#22292f'
const BORDER = '#2e3a42'
const TEXT = '#f8f2f0'
const DIM = '#8a9ba8'
const ACCENT = '#93fffd'
const BTN_TEXT = '#4a4543'
const TAG_BG = '#526767'

const STYLE_TAGS = ['#캐주얼', '#미니멀', '#스트릿', '#시티보이', '#오피스룩']

export default function MainPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const name = user?.name || '사용자'

  return (
    <div className="min-h-screen" style={{ backgroundColor: BG }}>
      <Navbar />

      <div className="flex items-stretch" style={{ minHeight: 'calc(100vh - 73px)', padding: '40px 80px', gap: 60 }}>
        {/* 왼쪽 */}
        <div className="flex-1 flex flex-col justify-center">
          <p style={{ color: DIM, fontSize: 14, marginBottom: 12 }}>dailycloset</p>

          <h1 style={{ color: TEXT, fontSize: 52, fontWeight: 700, lineHeight: 1.2, marginBottom: 20 }}>
            {name}님,<br />
            오늘은 어떤 스타일로<br />
            입고 싶으세요?
          </h1>

          <p style={{ color: DIM, fontSize: 14, lineHeight: 1.9, marginBottom: 40 }}>
            오늘의 날씨, 스타일 취향을 분석해<br />
            당신만의 OOTD를 추천해 드릴게요.
          </p>

          {/* 날씨 */}
          <div
            className="flex items-center gap-3 w-fit"
            style={{ backgroundColor: '#34363a', borderRadius: 12, padding: '10px 16px', marginBottom: 32 }}
          >
            <span style={{ fontSize: 28 }}>⛅</span>
            <div>
              <p style={{ color: TEXT, fontSize: 18, fontWeight: 600 }}>--°</p>
              <p style={{ color: DIM, fontSize: 11 }}>Seoul • 날씨 불러오는 중</p>
            </div>
          </div>

          {/* OOTD 버튼 */}
          <button
            onClick={() => navigate('/ootd')}
            className="flex items-center gap-2 cursor-pointer hover:opacity-90 transition-opacity w-fit"
            style={{
              backgroundColor: ACCENT,
              color: BTN_TEXT,
              fontWeight: 600,
              fontSize: 15,
              padding: '13px 24px',
              borderRadius: 12,
              border: 'none',
              marginBottom: 36,
            }}
          >
            오늘의 OOTD 추천받기
            <span style={{ fontSize: 18 }}>→</span>
          </button>

          {/* 스타일 태그 */}
          <div className="flex flex-wrap gap-2">
            {STYLE_TAGS.map(tag => (
              <span
                key={tag}
                style={{
                  backgroundColor: TAG_BG,
                  color: '#fff',
                  fontSize: 13,
                  padding: '6px 14px',
                  borderRadius: 20,
                  cursor: 'pointer',
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* 오른쪽 - 옷장 미리보기 카드 */}
        <div className="flex flex-col" style={{ width: '45%', minWidth: 360 }}>
          <div
            className="rounded-2xl flex flex-col flex-1"
            style={{ backgroundColor: CARD, border: `1px solid ${BORDER}`, padding: '28px 28px 24px', overflow: 'hidden' }}
          >
            {/* 카테고리 통계 */}
            <div style={{ marginBottom: 24 }}>
              <p style={{ color: DIM, fontSize: 12, marginBottom: 16 }}>카테고리별 옷 개수</p>
              <div className="flex gap-6 flex-wrap">
                {['상의', '하의', '아우터', '원피스', 'acc'].map(cat => (
                  <div key={cat} className="flex flex-col items-center gap-2">
                    <span style={{ color: DIM, fontSize: 12 }}>{cat}</span>
                    <span style={{ color: '#93fffd', fontSize: 26, fontWeight: 700 }}>0</span>
                  </div>
                ))}
                <div className="flex flex-col items-center gap-2 ml-auto">
                  <span style={{ color: DIM, fontSize: 12 }}>총 아이템</span>
                  <span style={{ color: TEXT, fontSize: 26, fontWeight: 700 }}>0</span>
                </div>
              </div>
            </div>

            {/* 구분선 */}
            <div style={{ borderTop: `1px solid ${BORDER}`, marginBottom: 24 }} />

            {/* 오늘의 코디 영역 */}
            <div className="flex flex-col flex-1 items-center justify-center gap-4">
              <p style={{ color: DIM, fontSize: 13 }}>오늘의 추천 코디</p>
              <div style={{ color: DIM, fontSize: 48 }}>👗</div>
              <p style={{ color: DIM, fontSize: 12, textAlign: 'center', lineHeight: 1.6 }}>
                아직 추천된 코디가 없어요<br />
                OOTD 추천을 받아보세요!
              </p>
              <button
                onClick={() => navigate('/ootd')}
                style={{
                  backgroundColor: ACCENT,
                  color: BTN_TEXT,
                  fontSize: 14,
                  fontWeight: 600,
                  padding: '10px 24px',
                  borderRadius: 10,
                  border: 'none',
                  cursor: 'pointer',
                  marginTop: 8,
                }}
              >
                추천 받기 →
              </button>
            </div>
          </div>

          <button
            onClick={() => navigate('/closet')}
            style={{ color: DIM, fontSize: 12, marginTop: 12, display: 'block', textAlign: 'right', cursor: 'pointer', background: 'none', border: 'none', width: '100%' }}
          >
            내 옷장으로 가기 →
          </button>
        </div>
      </div>
    </div>
  )
}
