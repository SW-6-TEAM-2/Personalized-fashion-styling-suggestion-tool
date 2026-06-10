import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { closetAPI, ootdAPI } from '../api'

const BG = '#ffffff'
const BORDER = '#e8e8e8'
const TEXT = '#111111'
const DIM = '#999999'
const ACCENT = '#ff6b35'
const ACCENT_BTN = '#111111'
const BTN_TEXT = '#ffffff'
const TAG_BG = '#f2f2f2'

const CATEGORY_ORDER = ['아우터', '상의', '하의', '신발']
const GENRES = ['#캐주얼', '#미니멀', '#클래식', '#스트릿']

/* 개별 아이템 카드 (오른쪽 그리드용) */
function ItemCard({ item, onReplace, onInfo }) {
  const [hovered, setHovered] = useState(false)
  const imgPadding = item.category === '하의' ? 4 : 12

  return (
    <div
      className="relative rounded-xl flex items-center justify-center cursor-pointer"
      style={{ border: `1px solid ${BORDER}`, width: '100%', height: '100%', overflow: 'hidden' }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {item.imageUrl ? (
        <img src={item.imageUrl} alt={item.name} style={{ width: '100%', height: '100%', objectFit: 'contain', padding: imgPadding }} />
      ) : (
        <div className="flex flex-col items-center gap-2">
          <span style={{ color: DIM, fontSize: 22 }}>
            {item.category === '상의' ? '👕' : item.category === '하의' ? '👖' : item.category === '아우터' ? '🧥' : '👟'}
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
                          {item.category === '상의' ? '👕' : item.category === '하의' ? '👖' : item.category === '아우터' ? '🧥' : '👟'}
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

/* 3/4 비율 아이템 이미지 */
function ItemImg({ item }) {
  const emoji = item.category === '상의' ? '👕' : item.category === '하의' ? '👖' : item.category === '아우터' ? '🧥' : '👟'
  return (
    <div style={{ width: '100%', aspectRatio: '3/4' }}>
      {item.imageUrl ? (
        <img src={item.imageUrl} alt={item.name} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
      ) : (
        <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontSize: 38, opacity: 0.2 }}>{emoji}</span>
        </div>
      )}
    </div>
  )
}

/* 정사각형 아이템 이미지 (신발) */
function ItemImgSq({ item }) {
  return (
    <div style={{ width: '100%', aspectRatio: '1' }}>
      {item.imageUrl ? (
        <img src={item.imageUrl} alt={item.name} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
      ) : (
        <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontSize: 30, opacity: 0.2 }}>👟</span>
        </div>
      )}
    </div>
  )
}

export default function OOTDResultPage() {
  const navigate = useNavigate()
  const location = useLocation()

  const [outfit, setOutfit] = useState(location.state?.outfit || [])
  const [replacingItem, setReplacingItem] = useState(null)
  const [reloading, setReloading] = useState(false)
  const [activeKeyword, setActiveKeyword] = useState(
    (location.state?.keywords || [])[0] || GENRES[0]
  )
  const temperature = location.state?.temperature ?? null

  const handleReRecommend = async (keyword = activeKeyword) => {
    setReloading(true)
    setActiveKeyword(keyword)
    try {
      const res = await ootdAPI.recommend([keyword], temperature)
      setOutfit(res.data)
    } catch {
      // keep current outfit on error
    } finally {
      setReloading(false)
    }
  }

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

  const outerItem  = displayOutfit.find(i => i.category === '아우터') || null
  const topItem    = displayOutfit.find(i => i.category === '상의') || null
  const bottomItem = displayOutfit.find(i => i.category === '하의') || null
  const shoeItem   = displayOutfit.find(i => i.category === '신발') || null
  const hasOuter   = !!outerItem
  const hasShoes   = !!shoeItem

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
          <div className="flex items-center gap-2" style={{ marginBottom: 20, flexShrink: 0, flexWrap: 'wrap' }}>
            <span style={{ color: DIM, fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', marginRight: 4 }}>Today's Look</span>
            {GENRES.map(genre => {
              const active = genre === activeKeyword
              return (
                <button
                  key={genre}
                  onClick={() => !reloading && genre !== activeKeyword && handleReRecommend(genre)}
                  disabled={reloading}
                  style={{
                    fontSize: 11,
                    padding: '3px 10px',
                    borderRadius: 20,
                    border: `1px solid ${active ? TEXT : BORDER}`,
                    backgroundColor: active ? TEXT : 'transparent',
                    color: active ? '#ffffff' : DIM,
                    cursor: reloading ? 'default' : genre === activeKeyword ? 'default' : 'pointer',
                    transition: 'all 0.15s',
                    fontWeight: active ? 600 : 400,
                  }}
                >
                  {genre}
                </button>
              )
            })}
          </div>

          {/* 플랫레이 코디 레이아웃 */}
          <div style={{ flex: 1, position: 'relative', overflow: 'hidden', minHeight: 0 }}>

            {/* ── 케이스 1: 아우터 + 상의 + 하의 (신발 없음) ── */}
            {hasOuter && !hasShoes && (
              <>
                {/* 하의: 맨 뒤 (z:1) */}
                {bottomItem && (
                  <div style={{ position: 'absolute', top: '40%', left: '23%', width: '45%', zIndex: 1, transform: 'rotate(20deg)', transformOrigin: 'top center' }}>
                    <ItemImg item={bottomItem} />
                  </div>
                )}
                {/* 아우터: 하의 위 (z:2) */}
                {outerItem && (
                  <div style={{ position: 'absolute', top: '-11%', left: '11%', width: '53%', zIndex: 2, transform: 'rotate(5deg)', transformOrigin: 'center center' }}>
                    <ItemImg item={outerItem} />
                  </div>
                )}
                {/* 상의: 앞 (z:3) */}
                {topItem && (
                  <div style={{ position: 'absolute', top: '4%', left: '35%', width: '44%', zIndex: 3, transform: 'rotate(-10deg)', transformOrigin: 'center center' }}>
                    <ItemImg item={topItem} />
                  </div>
                )}
              </>
            )}

            {/* ── 케이스 2: 아우터 + 상의 + 하의 + 신발 ── */}
            {hasOuter && hasShoes && (
              <>
                {/* 하의: 맨 뒤 (z:1) */}
                {bottomItem && (
                  <div style={{ position: 'absolute', top: '34%', left: '22%', width: '43%', zIndex: 1, transform: 'rotate(20deg)', transformOrigin: 'top center' }}>
                    <ItemImg item={bottomItem} />
                  </div>
                )}
                {/* 아우터: 하의 위 (z:2) */}
                {outerItem && (
                  <div style={{ position: 'absolute', top: '-11%', left: '11%', width: '51%', zIndex: 2, transform: 'rotate(5deg)', transformOrigin: 'center center' }}>
                    <ItemImg item={outerItem} />
                  </div>
                )}
                {/* 상의: 앞 (z:3) */}
                {topItem && (
                  <div style={{ position: 'absolute', top: '3%', left: '33%', width: '43%', zIndex: 3, transform: 'rotate(-10deg)', transformOrigin: 'center center' }}>
                    <ItemImg item={topItem} />
                  </div>
                )}
                {/* 신발: 하단 (z:4) */}
                {shoeItem && (
                  <div style={{ position: 'absolute', bottom: '4%', left: '32%', width: '38%', zIndex: 4 }}>
                    <ItemImgSq item={shoeItem} />
                  </div>
                )}
              </>
            )}

            {/* ── 케이스 3: 상의 + 하의 (아우터·신발 없음) ── */}
            {!hasOuter && !hasShoes && (
              <>
                {topItem && (
                  <div style={{ position: 'absolute', top: '9%', left: '9%', width: '41%', zIndex: 1 }}>
                    <ItemImg item={topItem} />
                  </div>
                )}
                {bottomItem && (
                  <div style={{ position: 'absolute', top: '4%', left: '50%', width: '43%', zIndex: 1 }}>
                    <ItemImg item={bottomItem} />
                  </div>
                )}
              </>
            )}

            {/* ── 케이스 4: 상의 + 하의 + 신발 (아우터 없음) ── */}
            {!hasOuter && hasShoes && (
              <>
                {topItem && (
                  <div style={{ position: 'absolute', top: '6%', left: '9%', width: '37%', zIndex: 1 }}>
                    <ItemImg item={topItem} />
                  </div>
                )}
                {bottomItem && (
                  <div style={{ position: 'absolute', top: '3%', left: '50%', width: '42%', zIndex: 1 }}>
                    <ItemImg item={bottomItem} />
                  </div>
                )}
                {shoeItem && (
                  <div style={{ position: 'absolute', bottom: '4%', left: '24%', width: '42%', zIndex: 2 }}>
                    <ItemImgSq item={shoeItem} />
                  </div>
                )}
              </>
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
              gridAutoRows: '1fr',
              gap: 1,
              backgroundColor: BORDER,
              overflowY: 'auto',
              minHeight: 0,
            }}
          >
            {displayOutfit.map((item, i) => (
              <div key={item.id ?? i} style={{ backgroundColor: BG, padding: item.category === '하의' ? 6 : 16, display: 'flex' }}>
                <ItemCard item={item} onReplace={setReplacingItem} onInfo={handleInfo} />
              </div>
            ))}
          </div>

          <div style={{ padding: '12px 14px 14px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 7 }}>
            <button
              onClick={() => handleReRecommend()}
              disabled={reloading}
              className="flex items-center justify-between w-full cursor-pointer hover:opacity-90 transition-opacity disabled:opacity-50"
              style={{ backgroundColor: ACCENT_BTN, color: BTN_TEXT, fontWeight: 600, fontSize: 14, padding: '11px 18px', borderRadius: 10, border: 'none' }}
            >
              {reloading ? '추천 중...' : '다시 추천받기'}
              {!reloading && <span style={{ fontSize: 16 }}>↺</span>}
            </button>
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
