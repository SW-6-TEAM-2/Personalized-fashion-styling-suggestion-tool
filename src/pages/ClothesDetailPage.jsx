import { useEffect, useState } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar'
import useClosetStore from '../store/useClosetStore'
import { closetAPI } from '../api'

const BG = '#ffffff'
const CARD = '#f8f8f8'
const BORDER = '#e8e8e8'
const TAG_BG = '#f2f2f2'
const TEXT = '#111111'
const DIM = '#999999'
const ACCENT = '#ff6b35'

export default function ClothesDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const { clothes, removeCloth } = useClosetStore()

  const [item, setItem] = useState(() => clothes.find((c) => String(c.id) === id) || null)
  const [loading, setLoading] = useState(!item)

  const fromOOTD = location.state?.fromOOTD

  useEffect(() => {
    if (!item) {
      closetAPI.getOne(id)
        .then((res) => setItem(res.data))
        .catch(() => navigate('/closet'))
        .finally(() => setLoading(false))
    }
  }, [id])

  const handleDelete = async () => {
    if (!window.confirm('이 옷을 삭제할까요?')) return
    try {
      await closetAPI.delete(id)
      removeCloth(Number(id))
      navigate('/closet')
    } catch {
      alert('삭제 중 오류가 발생했어요.')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: BG }}>
        <div style={{ width: 32, height: 32, border: `2px solid ${ACCENT}`, borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      </div>
    )
  }

  if (!item) return null

  return (
    <div style={{ minHeight: '100vh', backgroundColor: BG }}>
      <Navbar />

      <div style={{ maxWidth: 860, margin: '0 auto', padding: '40px 40px' }}>
        {/* 뒤로가기 */}
        <button
          onClick={() => navigate(-1)}
          style={{ color: DIM, fontSize: 13, background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 32 }}
          onMouseEnter={e => e.currentTarget.style.color = TEXT}
          onMouseLeave={e => e.currentTarget.style.color = DIM}
        >
          ← 뒤로
        </button>

        <div style={{ display: 'flex', gap: 48, alignItems: 'flex-start' }}>

          {/* ── 왼쪽: 이미지 ── */}
          <div style={{ flexShrink: 0, width: 320 }}>
            <div style={{
              width: '100%', aspectRatio: '3/4', borderRadius: 20,
              backgroundColor: CARD, border: `1px solid ${BORDER}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden',
            }}>
              {item.imageUrl ? (
                <img src={item.imageUrl} alt={item.name} style={{ width: '100%', height: '100%', objectFit: 'contain', padding: 24 }} />
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 40, opacity: 0.2 }}>
                    {item.category === '상의' ? '👕' : item.category === '하의' ? '👖' : item.category === '아우터' ? '🧥' : '👟'}
                  </span>
                  <span style={{ color: DIM, fontSize: 12 }}>이미지 없음</span>
                </div>
              )}
            </div>
          </div>

          {/* ── 오른쪽: 정보 ── */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 28, paddingTop: 8 }}>

            <div>
              <span style={{ fontSize: 11, color: DIM, letterSpacing: '0.1em', textTransform: 'uppercase', display: 'block', marginBottom: 8 }}>
                {item.category}
              </span>
              <h1 style={{ fontSize: 28, fontWeight: 700, color: TEXT, letterSpacing: '-0.02em', lineHeight: 1.2 }}>
                {item.name}
              </h1>
            </div>

            <div style={{ height: 1, backgroundColor: BORDER }} />

            {item.colors?.length > 0 && (
              <div>
                <p style={{ color: DIM, fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 10 }}>색상</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {item.colors.map((tag) => (
                    <span key={tag} style={{ padding: '5px 14px', borderRadius: 20, fontSize: 12, fontWeight: 500, color: ACCENT, backgroundColor: `${ACCENT}12`, border: `1px solid ${ACCENT}35` }}>
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {item.materials?.length > 0 && (
              <div>
                <p style={{ color: DIM, fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 10 }}>소재</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {item.materials.map((tag) => (
                    <span key={tag} style={{ padding: '5px 14px', borderRadius: 20, fontSize: 12, color: TEXT, backgroundColor: TAG_BG, border: `1px solid ${BORDER}` }}>
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
              {fromOOTD && (
                <button
                  onClick={() => navigate(-1)}
                  style={{ width: '100%', padding: '13px 20px', borderRadius: 12, backgroundColor: '#111111', color: '#ffffff', fontSize: 14, fontWeight: 600, border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
                >
                  코디로 돌아가기 <span>→</span>
                </button>
              )}
              <button
                onClick={() => navigate('/closet')}
                style={{ width: '100%', padding: '13px 20px', borderRadius: 12, backgroundColor: TAG_BG, color: TEXT, fontSize: 14, fontWeight: 500, border: `1px solid ${BORDER}`, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
              >
                옷장으로 가기 <span style={{ color: DIM }}>→</span>
              </button>
              <button
                onClick={handleDelete}
                style={{ width: '100%', padding: '11px 20px', borderRadius: 12, backgroundColor: 'transparent', color: '#ef4444', fontSize: 13, fontWeight: 500, border: '1px solid #fca5a5', cursor: 'pointer' }}
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
