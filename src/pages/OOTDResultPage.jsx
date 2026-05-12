import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar'
import useAuthStore from '../store/useAuthStore'
import { ootdAPI } from '../api'

const CATEGORY_POSITIONS = {
  '상의': 'col-start-2 row-start-1',
  '아우터': 'col-start-1 row-start-1',
  '원피스': 'col-start-2 row-start-1 row-span-2',
  '하의': 'col-start-2 row-start-2',
  'acc': 'col-start-3 row-start-2',
}

function OutfitItem({ item, onRefresh, onInfo }) {
  const [hovered, setHovered] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = async (e) => {
    e.stopPropagation()
    setRefreshing(true)
    try {
      await onRefresh(item)
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <div
      className="relative rounded-xl flex items-center justify-center cursor-pointer"
      style={{
        backgroundColor: '#1C1C1C',
        border: '1px solid #2A2A2A',
        minHeight: '140px',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {item.imageUrl ? (
        <img src={item.imageUrl} alt={item.name} className="w-full h-full object-contain p-4 max-h-40" />
      ) : (
        <div className="flex flex-col items-center gap-2 p-4">
          <div className="w-16 h-16 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#2A2A2A' }}>
            <span className="text-gray-500 text-xs">{item.category}</span>
          </div>
          <span className="text-gray-500 text-xs">{item.name}</span>
        </div>
      )}

      {/* 호버 오버레이 */}
      {hovered && (
        <div
          className="absolute inset-0 rounded-xl flex items-center justify-center gap-3"
          style={{ backgroundColor: 'rgba(0,0,0,0.6)' }}
        >
          {/* 새로고침 */}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2.5 rounded-full cursor-pointer transition-colors hover:bg-white/10"
            title="같은 카테고리 다른 옷으로"
          >
            {refreshing ? (
              <div className="w-5 h-5 border-2 border-[#4DFFC8] border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M1 4v6h6M23 20v-6h-6" stroke="#4DFFC8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4-4.64 4.36A9 9 0 0 1 3.51 15" stroke="#4DFFC8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </button>

          {/* 정보 */}
          <button
            onClick={(e) => { e.stopPropagation(); onInfo(item) }}
            className="p-2.5 rounded-full cursor-pointer transition-colors hover:bg-white/10"
            title="옷 정보 보기"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
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
  const { user } = useAuthStore()
  const name = user?.name || '사용자'

  const [outfit, setOutfit] = useState(location.state?.outfit || [])

  const handleRefresh = async (item) => {
    try {
      const res = await ootdAPI.refresh(item.category)
      setOutfit((prev) =>
        prev.map((o) => (o.id === item.id ? res.data : o))
      )
    } catch {
      alert('다른 옷을 불러오지 못했어요.')
    }
  }

  const handleInfo = (item) => {
    navigate(`/closet/${item.id}`, { state: { fromOOTD: true } })
  }

  const categories = ['상의', '아우터', '하의', '원피스', 'acc']
  const displayOutfit = outfit.length > 0
    ? outfit
    : categories.slice(0, 4).map((cat, i) => ({ id: i, category: cat, name: cat, imageUrl: null }))

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#111111' }}>
      <Navbar />

      <div className="max-w-4xl mx-auto px-6 py-10 flex gap-10">
        {/* 왼쪽 */}
        <div className="flex-1 flex flex-col">
          <p className="text-gray-400 text-sm mb-2">dailycloset</p>
          <h1 className="text-white text-3xl font-bold leading-tight mb-4">
            {name}님,<br />
            오늘은 어떤 스타일로<br />
            입고 싶으세요?
          </h1>
          <p className="text-gray-500 text-sm mb-8">
            마음에 드는 조합이에요!<br />
            아이콘으로 교체하거나 상세 정보를 확인해보세요.
          </p>

          <div className="flex flex-col gap-2">
            <button
              onClick={() => navigate('/ootd')}
              className="px-5 py-2.5 rounded-xl text-black font-semibold text-sm cursor-pointer hover:opacity-90 transition-opacity w-fit"
              style={{ backgroundColor: '#4DFFC8' }}
            >
              다시 추천 받기
            </button>
            <button
              onClick={() => navigate('/closet')}
              className="px-5 py-2.5 rounded-xl text-[#4DFFC8] font-medium text-sm cursor-pointer hover:opacity-80 transition-opacity w-fit"
              style={{ backgroundColor: '#4DFFC820', border: '1px solid #4DFFC840' }}
            >
              옷장으로 가기
            </button>
          </div>
        </div>

        {/* 오른쪽: 코디 배치 */}
        <div className="w-72">
          <p className="text-gray-500 text-xs mb-3 text-right">
            🔄 아이콘으로 교체 · ℹ 정보 보기
          </p>
          <div className="grid grid-cols-3 gap-3">
            {displayOutfit.map((item) => (
              <OutfitItem
                key={item.id}
                item={item}
                onRefresh={handleRefresh}
                onInfo={handleInfo}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
