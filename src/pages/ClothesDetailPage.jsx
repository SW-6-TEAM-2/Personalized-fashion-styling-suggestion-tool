import { useEffect, useState } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar'
import useClosetStore from '../store/useClosetStore'
import { closetAPI } from '../api'

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
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#111111' }}>
        <div className="w-8 h-8 border-2 border-[#4DFFC8] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!item) return null

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#111111' }}>
      <Navbar />

      <div className="max-w-2xl mx-auto px-6 py-8">
        <button
          onClick={() => navigate(-1)}
          className="text-gray-500 text-sm hover:text-white transition-colors mb-6 flex items-center gap-1 cursor-pointer"
        >
          ← 뒤로
        </button>

        <div className="flex gap-8">
          {/* 이미지 */}
          <div
            className="w-52 h-64 rounded-2xl flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: '#1C1C1C', border: '1px solid #2A2A2A' }}
          >
            {item.imageUrl ? (
              <img src={item.imageUrl} alt={item.name} className="w-full h-full object-contain p-4" />
            ) : (
              <span className="text-gray-600 text-sm">이미지 없음</span>
            )}
          </div>

          {/* 정보 */}
          <div className="flex-1 flex flex-col gap-4">
            <div>
              <h2 className="text-white text-xl font-semibold">{item.name}</h2>
              <span
                className="inline-block text-xs px-2 py-0.5 rounded-full text-gray-400 mt-1"
                style={{ backgroundColor: '#2A2A2A' }}
              >
                {item.category}
              </span>
            </div>

            {item.colors?.length > 0 && (
              <div>
                <p className="text-gray-500 text-xs mb-1.5">색상</p>
                <div className="flex flex-wrap gap-1.5">
                  {item.colors.map((tag) => (
                    <span
                      key={tag}
                      className="px-2.5 py-1 rounded-full text-xs text-[#4DFFC8]"
                      style={{ backgroundColor: '#4DFFC820', border: '1px solid #4DFFC840' }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {item.materials?.length > 0 && (
              <div>
                <p className="text-gray-500 text-xs mb-1.5">소재</p>
                <div className="flex flex-wrap gap-1.5">
                  {item.materials.map((tag) => (
                    <span
                      key={tag}
                      className="px-2.5 py-1 rounded-full text-xs text-gray-400"
                      style={{ backgroundColor: '#1C1C1C', border: '1px solid #2A2A2A' }}
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
                  className="w-full py-2.5 rounded-xl text-black font-medium text-sm cursor-pointer hover:opacity-90"
                  style={{ backgroundColor: '#4DFFC8' }}
                >
                  코디로 돌아가기
                </button>
              )}
              <button
                onClick={() => navigate('/closet')}
                className="w-full py-2.5 rounded-xl text-[#4DFFC8] font-medium text-sm cursor-pointer hover:opacity-80 transition-opacity"
                style={{ backgroundColor: '#4DFFC820', border: '1px solid #4DFFC840' }}
              >
                옷장으로 가기
              </button>
              <button
                onClick={handleDelete}
                className="w-full py-2.5 rounded-xl text-red-400 font-medium text-sm cursor-pointer hover:opacity-80 transition-opacity"
                style={{ backgroundColor: 'transparent', border: '1px solid #2A2A2A' }}
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
