import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { ootdAPI } from '../api'

const BG = '#0d0d0d'
const BORDER = '#282828'
const TEXT = '#f0ece6'
const DIM = '#6b6b6b'
const ACCENT = '#ff6b35'
const ACCENT_BTN = '#ff6b35'

const BTN_TEXT = '#ffffff'

const CATEGORY_ORDER = ['아우터', '상의', '원피스', '하의', 'acc']

/* 개별 아이템 카드 (오른쪽 그리드용) */
function ItemCard({ item, onRefresh, onInfo }) {
  const [hovered, setHovered] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = async (e) => {
    e.stopPropagation()
    setRefreshing(true)
    try { await onRefresh(item) } finally { setRefreshing(false) }
  }

  return (
    <div
      className="relative rounded-xl flex items-center justify-center cursor-pointer"
      style={{
        border: `1px solid ${BORDER}`,
        width: '100%',
        height: '100%',
        overflow: 'hidden',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {item.imageUrl ? (
        <img
          src={item.imageUrl}
          alt={item.name}
          style={{ width: '100%', height: '100%', objectFit: 'contain', padding: 12 }}
        />
      ) : (
        <div className="flex flex-col items-center gap-2">
          <span style={{ color: DIM, fontSize: 22 }}>
            {item.category === '상의' ? '👕' : item.category === '하의' ? '👖' : item.category === '아우터' ? '🧥' : item.category === '원피스' ? '👗' : '👟'}
          </span>
          <span style={{ color: DIM, fontSize: 11 }}>{item.category}</span>
        </div>
      )}

      {hovered && (
        <div
          className="absolute inset-0 rounded-xl flex items-center justify-center gap-3"
          style={{ backgroundColor: 'rgba(0,0,0,0.6)' }}
        >
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2 rounded-full cursor-pointer"
            style={{ background: 'rgba(255,255,255,0.12)' }}
            title="다른 옷으로 교체"
          >
            {refreshing ? (
              <div style={{ width: 18, height: 18, border: `2px solid ${ACCENT}`, borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M1 4v6h6M23 20v-6h-6" stroke={ACCENT} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4-4.64 4.36A9 9 0 0 1 3.51 15" stroke={ACCENT} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onInfo(item) }}
            className="p-2 rounded-full cursor-pointer"
            style={{ background: 'rgba(255,255,255,0.12)' }}
            title="옷 정보 보기"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="white" strokeWidth="1.5" />
              <path d="M12 16v-4M12 8h.01" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      )}
    </div>
  )
}

export default function OOTDResultPage() {
  const navigate = useNavigate()
  const location = useLocation()

  const [outfit, setOutfit] = useState(location.state?.outfit || [])
  const keywords = location.state?.keywords || []

  const handleRefresh = async (item) => {
    try {
      const res = await ootdAPI.refresh(item.category)
      setOutfit((prev) => prev.map((o) => (o.id === item.id ? res.data : o)))
    } catch {
      alert('다른 옷을 불러오지 못했어요.')
    }
  }

  const handleInfo = (item) => {
    navigate(`/closet/${item.id}`, { state: { fromOOTD: true } })
  }

  const sortedOutfit = [...outfit].sort(
    (a, b) => CATEGORY_ORDER.indexOf(a.category) - CATEGORY_ORDER.indexOf(b.category)
  )

  const displayOutfit = sortedOutfit.length > 0
    ? sortedOutfit
    : ['상의', '하의', 'acc', 'acc'].map((cat, i) => ({ id: i, category: cat, name: cat, imageUrl: null }))

  /* 왼쪽 합성 뷰용 분류 */
  const topItem    = displayOutfit.find(i => ['아우터', '상의', '원피스'].includes(i.category))
  const bottomItem = displayOutfit.find(i => i.category === '하의')
  const accItems   = displayOutfit.filter(i => i.category === 'acc')

  return (
    <div style={{ height: '100vh', backgroundColor: BG, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Navbar />

      <div
        className="flex items-stretch"
        style={{
          flex: 1,
          padding: '28px 60px',
          gap: 32,
          overflow: 'hidden',
          minHeight: 0,
        }}
      >
        {/* ── 왼쪽: 키워드 태그 + 합성 코디 ── */}
        <div className="flex flex-col" style={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
          {/* 키워드 태그 */}
          <div className="flex items-center gap-2" style={{ marginBottom: 20, flexShrink: 0 }}>
            <span style={{ color: DIM, fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase' }}>Today's Look</span>
            {(keywords.length > 0 ? keywords.slice(0, 3) : ['오늘의 코디']).map((kw, i) => (
              <span
                key={i}
                style={{
                  color: DIM,
                  fontSize: 11,
                  padding: '3px 10px',
                  borderRadius: 20,
                  border: `1px solid ${BORDER}`,
                }}
              >
                {kw}
              </span>
            ))}
          </div>

          {/* 합성 코디 — 실루엣처럼 붙여서 */}
          <div
            className="flex-1 flex flex-col items-center justify-center"
            style={{ overflow: 'hidden', minHeight: 0 }}
          >
            {/* 상의/아우터/원피스 */}
            {topItem && (
              <div style={{ width: '52%', aspectRatio: '1', flexShrink: 0 }}>
                {topItem.imageUrl ? (
                  <img src={topItem.imageUrl} alt={topItem.name} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                ) : (
                  <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontSize: 72, opacity: 0.25 }}>
                      {topItem.category === '아우터' ? '🧥' : topItem.category === '원피스' ? '👗' : '👕'}
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* 하의 */}
            {bottomItem && (
              <div style={{ width: '44%', aspectRatio: '0.85', flexShrink: 0, marginTop: -16 }}>
                {bottomItem.imageUrl ? (
                  <img src={bottomItem.imageUrl} alt={bottomItem.name} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                ) : (
                  <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontSize: 64, opacity: 0.25 }}>👖</span>
                  </div>
                )}
              </div>
            )}

            {/* acc */}
            {accItems.length > 0 && (
              <div style={{ display: 'flex', gap: 16, marginTop: 12, flexShrink: 0 }}>
                {accItems.slice(0, 2).map((acc, i) => (
                  <div key={i} style={{ width: 60, height: 60 }}>
                    {acc.imageUrl ? (
                      <img src={acc.imageUrl} alt={acc.name} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                    ) : (
                      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <span style={{ fontSize: 32, opacity: 0.25 }}>👟</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── 오른쪽: 테두리 카드 — 2×2 그리드 + 하단 버튼 ── */}
        <div
          style={{
            width: '44%',
            minWidth: 280,
            display: 'flex',
            flexDirection: 'column',
            border: `1px solid ${BORDER}`,
            borderRadius: 16,
            overflow: 'hidden',
          }}
        >
          {/* 2×2 아이템 그리드 */}
          <div
            style={{
              flex: 1,
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 1,
              backgroundColor: BORDER,
              overflow: 'hidden',
              minHeight: 0,
            }}
          >
            {displayOutfit.slice(0, 4).map((item, i) => (
              <div key={item.id ?? i} style={{ backgroundColor: BG, padding: 16, display: 'flex' }}>
                <ItemCard item={item} onRefresh={handleRefresh} onInfo={handleInfo} />
              </div>
            ))}
          </div>

          {/* 하단 버튼 */}
          <div style={{ padding: '14px 18px', flexShrink: 0 }}>
            <button
              onClick={() => navigate('/closet')}
              className="flex items-center justify-between w-full cursor-pointer hover:opacity-90 transition-opacity"
              style={{
                backgroundColor: ACCENT_BTN,
                color: BTN_TEXT,
                fontWeight: 600,
                fontSize: 14,
                padding: '11px 18px',
                borderRadius: 10,
                border: 'none',
              }}
            >
              옷장으로 가기
              <span style={{ fontSize: 16 }}>→</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
