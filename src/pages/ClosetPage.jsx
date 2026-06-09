import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import ClothingCard from '../components/ClothingCard'
import useClosetStore from '../store/useClosetStore'
import { closetAPI } from '../api'

const BG = '#ffffff'
const CARD = '#f2f2f2'
const BORDER = '#e8e8e8'
const TEXT = '#111111'
const DIM = '#999999'
const ACCENT = '#ff6b35'
const ACCENT_BTN = '#111111'
const BTN_TEXT = '#ffffff'

const CATEGORIES = ['전체', '아우터', '상의', '원피스', '하의', '신발']

export default function ClosetPage() {
  const navigate = useNavigate()
  const { clothes, setClothes, removeCloth, selectedCategory, setCategory } = useClosetStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    closetAPI.getAll()
      .then(res => setClothes(res.data))
      .catch(() => setClothes([]))
      .finally(() => setLoading(false))
  }, [])

  const filtered = selectedCategory === '전체'
    ? clothes
    : clothes.filter(c => c.category === selectedCategory)

  const handleDelete = async (id) => {
    if (!window.confirm('이 옷을 삭제할까요?')) return
    try {
      await closetAPI.delete(id)
      removeCloth(id)
    } catch {
      alert('삭제 중 오류가 발생했어요.')
    }
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: BG }}>
      <Navbar />

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 40px', minHeight: 'calc(100vh - 73px)', display: 'flex', flexDirection: 'column' }}>
        {/* 헤더 */}
        <h2 className="font-heading" style={{ color: TEXT, fontSize: 22, fontWeight: 700, marginBottom: 16 }}>내 옷장</h2>

        {/* 카테고리 탭 + 옷 추가 버튼 (같은 행) */}
        <div className="flex items-center justify-between mb-6">
          <div
            className="flex items-center gap-1"
            style={{ backgroundColor: CARD, borderRadius: 12, padding: 4 }}
          >
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className="cursor-pointer transition-all"
              style={{
                width: 72,
                padding: '10px 0',
                textAlign: 'center',
                borderRadius: 8,
                fontSize: 14,
                fontWeight: selectedCategory === cat ? 600 : 400,
                backgroundColor: selectedCategory === cat ? ACCENT_BTN : 'transparent',
                color: selectedCategory === cat ? BTN_TEXT : DIM,
                border: 'none',
              }}
            >
              {cat}
            </button>
          ))}
          </div>

          <button
            onClick={() => navigate('/closet/add')}
            className="flex items-center gap-2 cursor-pointer hover:opacity-90 transition-opacity"
            style={{
              backgroundColor: ACCENT_BTN, color: BTN_TEXT,
              fontSize: 14, fontWeight: 600,
              padding: '10px 20px', borderRadius: 10, border: 'none',
            }}
          >
            <span style={{ fontSize: 18, lineHeight: 1 }}>+</span> 옷 추가
          </button>
        </div>

        {/* 그리드 */}
        {loading ? (
          <div className="flex justify-center py-20">
            <div style={{ width: 32, height: 32, border: `2px solid ${ACCENT}`, borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center flex-1 gap-4">
            <p style={{ color: DIM, fontSize: 14 }}>아직 옷이 없어요</p>
            <button
              onClick={() => navigate('/closet/add')}
              style={{ backgroundColor: ACCENT_BTN, color: BTN_TEXT, fontSize: 14, fontWeight: 600, padding: '10px 20px', borderRadius: 10, border: 'none', cursor: 'pointer' }}
            >
              첫 번째 옷 추가하기
            </button>
          </div>
        ) : (
          <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))' }}>
            {filtered.map(item => (
              <ClothingCard key={item.id} item={item} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
