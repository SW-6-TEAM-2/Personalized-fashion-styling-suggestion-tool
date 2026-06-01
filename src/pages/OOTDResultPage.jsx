import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { closetAPI } from '../api'

const BG = '#ffffff'
const BORDER = '#e8e8e8'
const TEXT = '#111111'
const DIM = '#999999'
const ACCENT = '#ff6b35'
const ACCENT_BTN = '#111111'
const BTN_TEXT = '#ffffff'
const TAG_BG = '#f2f2f2'

const CATEGORY_ORDER = ['아우터', '상의', '원피스', '하의', '신발']

/* 개별 아이템 카드 (오른쪽 그리드용) */
function ItemCard({ item, onReplace, onInfo }) {
  const [hovered, setHovered] = useState(false)

  return (
    <div
      className="relative rounded-xl flex items-center justify-center cursor-pointer"
      style={{ border: `1px solid ${BORDER}`, width: '100%', height: '100%', overflow: 'hidden' }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {item.imageUrl ? (
        <img src={item.imageUrl} alt={item.name} style={{ width: '100%', height: '100%', objectFit: 'contain', padding: 12 }} />
      ) : (
        <div className="flex flex-col items-center gap-2">
          <span style={{ color: DIM, fontSize: 22 }}>
            {item.category === '상의' ? '👕' : item.category === '하의' ? '👖' : item.category === '아우터' ? '🧥' : item.category === '원피스' ? '👗' : '👟'}
          </span>
          <span style={{ color: DIM, fontSize: 11 }}>{item.category}</span>
        </div>
      )}

      {hovered && (
        <div className="absolute inset-0 rounded-xl flex items-center justify-center gap-3" style={{ backgroundColor: 'rgba(0,0,0,0.6)' }}>
          <button
            onClick={(e) => { e.stopPropagation(); onReplace(item) }}
            className="p-2 rounded-full cursor-pointer"
            style={{ background: 'rgba(255,255,255,0.12)' }}
            title="다른 옷으로 교체"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M1 4v6h6M23 20v-6h-6" stroke={ACCENT} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4-4.64 4.36A9 9 0 0 1 3.51 15" stroke={ACCENT} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
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

/* 교체 선택 모달 */
function ReplaceModal({ targetItem, onSelect, onClose }) {
  const [closetItems, setClosetItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    closetAPI.getAll()
      .then(res => {
        const filtered = res.data.filter(c => c.category === targetItem.category && c.id !== targetItem.id)
        setClosetItems(filtered)
      })
      .catch(() => setClosetItems([]))
      .finally(() => setLoading(false))
  }, [targetItem])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
      onClick={onClose}
    >
      <div
        style={{ backgroundColor: BG, borderRadius: 20, padding: '28px', width: 480, maxHeight: '70vh', display: 'flex', flexDirection: 'column' }}
        onClick={e => e.stopPropagation()}
      >
        {/* 헤더 */}
        <div className="flex items-center justify-between" style={{ marginBottom: 20 }}>
          <div>
            <p style={{ color: TEXT, fontSize: 16, fontWeight: 700 }}>{targetItem.category} 교체</p>
            <p style={{ color: DIM, fontSize: 12, marginTop: 2 }}>옷장에서 교체할 옷을 선택해주세요</p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: DIM, fontSize: 20 }}>✕</button>
        </div>

        {/* 옷 목록 */}
        <div style={{ overflowY: 'auto', flex: 1 }}>
          {loading ? (
            <div className="flex justify-center py-10">
              <div style={{ width: 28, height: 28, border: `2px solid ${ACCENT}`, borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
            </div>
          ) : closetItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 gap-2">
              <p style={{ color: DIM, fontSize: 14 }}>옷장에 {targetItem.category} 아이템이 없어요</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
              {closetItems.map(item => (
                <div
                  key={item.id}
                  onClick={() => onSelect(item)}
                  className="cursor-pointer"
                  style={{ border: `1px solid ${BORDER}`, borderRadius: 12, padding: 10, backgroundColor: TAG_BG, transition: 'border-color 0.15s' }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = ACCENT}
                  onMouseLeave={e => e.currentTarget.style.borderColor = BORDER}
                >
                  <div style={{ aspectRatio: '1', marginBottom: 8 }}>
                    {item.imageUrl ? (
                      <img src={item.imageUrl} alt={item.name} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                    ) : (
                      <div className="flex items-center justify-center w-full h-full">
                        <span style={{ fontSize: 32 }}>
                          {item.category === '상의' ? '👕' : item.category === '하의' ? '👖' : item.category === '아우터' ? '🧥' : item.category === '원피스' ? '👗' : '👟'}
                        </span>
                      </div>
                    )}
                  </div>
                  <p style={{ color: TEXT, fontSize: 11, fontWeight: 500, textAlign: 'center' }} className="truncate">{item.name}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function OOTDResultPage() {
  const navigate = useNavigate()
  const location = useLocation()

  const [outfit, setOutfit] = useState(location.state?.outfit || [])
  const [replacingItem, setReplacingItem] = useState(null)
  const keywords = location.state?.keywords || []

  const handleReplaceSelect = (newItem) => {
    setOutfit(prev => prev.map(o => o.id === replacingItem.id ? { ...newItem } : o))
    setReplacingItem(null)
  }

  const handleInfo = (item) => {
    navigate(`/closet/${item.id}`, { state: { fromOOTD: true } })
  }

  const sortedOutfit = [...outfit].sort(
    (a, b) => CATEGORY_ORDER.indexOf(a.category) - CATEGORY_ORDER.indexOf(b.category)
  )

  const displayOutfit = sortedOutfit.length > 0
    ? sortedOutfit
    : ['상의', '하의', '아우터', '신발'].map((cat, i) => ({ id: i, category: cat, name: cat, imageUrl: null }))

  const topItem    = displayOutfit.find(i => ['아우터', '상의', '원피스'].includes(i.category))
  const bottomItem = displayOutfit.find(i => i.category === '하의')
  const accItems   = displayOutfit.filter(i => i.category === '신발')

  return (
    <div style={{ height: '100vh', backgroundColor: BG, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Navbar />

      {/* 교체 모달 */}
      {replacingItem && (
        <ReplaceModal
          targetItem={replacingItem}
          onSelect={handleReplaceSelect}
          onClose={() => setReplacingItem(null)}
        />
      )}

      <div className="flex items-stretch" style={{ flex: 1, padding: '28px 60px', gap: 32, overflow: 'hidden', minHeight: 0 }}>

        {/* ── 왼쪽: 키워드 태그 + 합성 코디 ── */}
        <div className="flex flex-col" style={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
          <div className="flex items-center gap-2" style={{ marginBottom: 20, flexShrink: 0 }}>
            <span style={{ color: DIM, fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase' }}>Today's Look</span>
            {(keywords.length > 0 ? keywords.slice(0, 3) : ['오늘의 코디']).map((kw, i) => (
              <span key={i} style={{ color: DIM, fontSize: 11, padding: '3px 10px', borderRadius: 20, border: `1px solid ${BORDER}` }}>
                {kw}
              </span>
            ))}
          </div>

          <div className="flex-1 flex flex-col items-center justify-center" style={{ overflow: 'hidden', minHeight: 0 }}>
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

        {/* ── 오른쪽: 그리드 + 버튼 ── */}
        <div style={{ width: '44%', minWidth: 280, display: 'flex', flexDirection: 'column', border: `1px solid ${BORDER}`, borderRadius: 16, overflow: 'hidden' }}>
          <div
            style={{
              flex: 1,
              display: 'grid',
              gridTemplateColumns: displayOutfit.length === 1 ? '1fr' : '1fr 1fr',
              gap: 1,
              backgroundColor: BORDER,
              overflow: 'hidden',
              minHeight: 0,
            }}
          >
            {displayOutfit.map((item, i) => (
              <div key={item.id ?? i} style={{ backgroundColor: BG, padding: 16, display: 'flex' }}>
                <ItemCard item={item} onReplace={setReplacingItem} onInfo={handleInfo} />
              </div>
            ))}
          </div>

          <div style={{ padding: '14px 18px', flexShrink: 0 }}>
            <button
              onClick={() => navigate('/closet')}
              className="flex items-center justify-between w-full cursor-pointer hover:opacity-90 transition-opacity"
              style={{ backgroundColor: ACCENT_BTN, color: BTN_TEXT, fontWeight: 600, fontSize: 14, padding: '11px 18px', borderRadius: 10, border: 'none' }}
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
