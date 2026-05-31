import { useNavigate } from 'react-router-dom'

const CARD = '#f8f8f8'
const BORDER = '#e8e8e8'
const TEXT = '#111111'
const DIM = '#999999'

export default function ClothingCard({ item, onDelete }) {
  const navigate = useNavigate()

  return (
    <div
      className="relative group rounded-xl overflow-hidden cursor-pointer"
      style={{ backgroundColor: CARD, border: `1px solid ${BORDER}` }}
      onClick={() => navigate(`/closet/${item.id}`)}
    >
      <div className="aspect-square flex items-center justify-center p-4" style={{ backgroundColor: '#f2f2f2' }}>
        {item.imageUrl ? (
          <img src={item.imageUrl} alt={item.name} className="w-full h-full object-contain" />
        ) : (
          <div style={{ color: DIM, fontSize: 12 }}>{item.category}</div>
        )}
      </div>

      {/* 호버 오버레이 */}
      {onDelete && (
        <div
          className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
          style={{ backgroundColor: 'rgba(0,0,0,0.45)' }}
        >
          <button
            onClick={e => { e.stopPropagation(); onDelete(item.id) }}
            className="p-2 rounded-full"
            style={{ backgroundColor: 'rgba(239,68,68,0.2)' }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      )}

      <div style={{ padding: '10px 12px 12px' }}>
        <p style={{ color: TEXT, fontSize: 13, fontWeight: 500 }} className="truncate">{item.name}</p>
        <p style={{ color: DIM, fontSize: 11, marginTop: 2 }}>{item.category}</p>
      </div>
    </div>
  )
}
