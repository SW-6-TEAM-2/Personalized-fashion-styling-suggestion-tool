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
    <div className="min-h-screen" style={{ backgroundColor: BG }}>
      <Navbar />

      <div className="max-w-2xl mx-auto px-6 py-8">
        <button
          onClick={() => navigate(-1)}
          style={{ color: DIM, fontSize: 13, background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, marginBottom: 24 }}
          onMouseEnter={e => e.currentTarget.style.color = TEXT}
          onMouseLeave={e => e.currentTarget.style.color = DIM}
        >
          ← 뒤로
        </button>

        <div className="flex gap-8">
          {/* 이미지 */}
          <div
            className="w-52 h-64 rounded-2xl flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: CARD, border: `1px solid ${BORDER}` }}
          >
            {item.imageUrl ? (
              <img src={item.imageUrl} alt={item.name} className="w-full h-full object-contain p-4" />
            ) : (
              <span style={{ color: DIM, fontSize: 13 }}>이미지 없음</span>
            )}
          </div>

          {/* 정보 */}
          <div className="flex-1 flex flex-col gap-4">
            <div>
              <h2 style={{ color: TEXT, fontSize: 20, fontWeight: 600 }}>{item.name}</h2>
              <span
                style={{ display: 'inline-block', fontSize: 11, padding: '2px 10px', borderRadius: 20, backgroundColor: TAG_BG, color: DIM, border: `1px solid ${BORDER}`, marginTop: 4 }}
              >
                {item.category}
              </span>
            </div>

            {item.colors?.length > 0 && (
              <div>
                <p style={{ color: DIM, fontSize: 11, marginBottom: 6 }}>색상</p>
                <div className="flex flex-wrap gap-1.5">
                  {item.colors.map((tag) => (
                    <span
                      key={tag}
                      style={{ padding: '3px 10px', borderRadius: 20, fontSize: 12, color: ACCENT, backgroundColor: `${ACCENT}15`, border: `1px solid ${ACCENT}40` }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {item.materials?.length > 0 && (
              <div>
                <p style={{ color: DIM, fontSize: 11, marginBottom: 6 }}>소재</p>
                <div className="flex flex-wrap gap-1.5">
                  {item.materials.map((tag) => (
                    <span
                      key={tag}
                      style={{ padding: '3px 10px', borderRadius: 20, fontSize: 12, color: DIM, backgroundColor: TAG_BG, border: `1px solid ${BORDER}` }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="flex flex-col gap-2 mt-auto">
              {fromOOTD && (
                <button
                  onClick={() => navigate(-1)}
                  className="w-full py-2.5 rounded-xl font-medium text-sm cursor-pointer hover:opacity-90 transition-opacity"
                  style={{ backgroundColor: '#111111', color: '#ffffff', border: 'none' }}
                >
                  코디로 돌아가기
                </button>
              )}
              <button
                onClick={() => navigate('/closet')}
                className="w-full py-2.5 rounded-xl font-medium text-sm cursor-pointer hover:opacity-80 transition-opacity"
                style={{ backgroundColor: TAG_BG, color: TEXT, border: `1px solid ${BORDER}` }}
              >
                옷장으로 가기
              </button>
              <button
                onClick={handleDelete}
                className="w-full py-2.5 rounded-xl font-medium text-sm cursor-pointer hover:opacity-80 transition-opacity"
                style={{ backgroundColor: 'transparent', color: '#ef4444', border: '1px solid #fca5a5' }}
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
