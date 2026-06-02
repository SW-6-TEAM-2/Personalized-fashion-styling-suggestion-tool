export default function LoadingSpinner({ message = '로딩 중...' }) {
  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center z-50" style={{ backgroundColor: '#111111' }}>
      <div className="relative w-16 h-16 mb-6">
        <div
          className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#4DFFC8] animate-spin"
        />
        <div
          className="absolute inset-2 rounded-full border-2 border-transparent border-b-[#4DFFC8] animate-spin"
          style={{ animationDirection: 'reverse', animationDuration: '0.8s' }}
        />
      </div>
      <p className="text-gray-400 text-sm">{message}</p>
    </div>
  )
}
