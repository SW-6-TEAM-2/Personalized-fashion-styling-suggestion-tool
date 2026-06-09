import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import useAuthStore from '../store/useAuthStore'
import { ootdAPI } from '../api'

const BG = '#ffffff'
const PANEL = '#f8f8f8'
const PANEL_BORDER = '#e8e8e8'
const CARD = '#f2f2f2'
const BORDER = '#e8e8e8'
const TEXT = '#111111'
const DIM = '#999999'
const ACCENT = '#ff6b35'
const ACCENT_BTN = '#111111'
const BTN_TEXT = '#ffffff'
const TAG_BG = '#f2f2f2'

const GENRES = ['#캐주얼', '#미니멀', '#클래식', '#스트릿']

function getWeatherEmoji(code) {
  if (code === 0) return '☀️'
  if (code <= 2) return '🌤️'
  if (code === 3) return '☁️'
  if (code <= 48) return '🌫️'
  if (code <= 55) return '🌦️'
  if (code <= 65) return '🌧️'
  if (code <= 77) return '🌨️'
  if (code <= 82) return '🌦️'
  if (code <= 99) return '⛈️'
  return '⛅'
}

function getTempGuide(temp) {
  if (temp === null) return null
  if (temp >= 28) return '☀️ 반팔·반바지 위주로 추천할게요'
  if (temp >= 23) return '🌤 반팔에 가벼운 옷 위주로 추천할게요'
  if (temp >= 20) return '🌤 반바지도 가능한 날씨예요'
  if (temp >= 17) return '🌥 긴팔 위주로 추천할게요'
  if (temp >= 12) return '🧥 긴팔 + 아우터를 포함해 추천할게요'
  return '❄️ 두꺼운 아우터 필수예요'
}

export default function OOTDPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const name = user?.name || '사용자'

  const [selectedGenre, setSelectedGenre] = useState(null)
  const [loading, setLoading] = useState(false)
  const [weather, setWeather] = useState(null)
  const [city, setCity] = useState('')

  // 위치 기반 날씨 자동 조회 (MainPage와 동일한 API)
  useEffect(() => {
    const fetchWeather = (lat, lon, cityName) => {
      fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&timezone=Asia%2FSeoul`)
        .then(res => res.json())
        .then(data => {
          setWeather(data.current_weather)
          setCity(cityName)
        })
        .catch(() => {})
    }

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => fetchWeather(pos.coords.latitude, pos.coords.longitude, '현재 위치'),
        ()  => fetchWeather(37.5665, 126.9780, 'Seoul')
      )
    } else {
      fetchWeather(37.5665, 126.9780, 'Seoul')
    }
  }, [])

  const temperature = weather ? Math.round(weather.temperature) : null

  const toggleGenre = (genre) => {
    setSelectedGenre(prev => (prev === genre ? null : genre))
  }

  const handleRecommend = async () => {
    if (!selectedGenre) return
    setLoading(true)
    const keywords = [selectedGenre]
    try {
      const res = await ootdAPI.recommend(keywords, temperature)
      navigate('/ootd/result', { state: { outfit: res.data, keywords, temperature } })
    } catch {
      navigate('/ootd/result', { state: { outfit: [], keywords, temperature } })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ height: '100vh', backgroundColor: BG, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Navbar />

      <div
        className="flex items-stretch"
        style={{ flex: 1, minHeight: 0, padding: '0 0 0 140px' }}
      >
        <div className="flex-1 flex flex-col justify-center" style={{ padding: '54px 140px 54px 0', maxWidth: 860 }}>
          <h1 style={{ color: TEXT, fontSize: 72, fontWeight: 700, lineHeight: 1.1, letterSpacing: '-0.03em', marginBottom: 20 }}>
            오늘은 어떤<br />
            무드예요?
          </h1>

          {/* 현재 기온 표시 (자동, 수정 불가) */}
          {weather && (
            <div
              className="flex items-center gap-3"
              style={{ backgroundColor: TAG_BG, border: `1px solid ${BORDER}`, borderRadius: 12, padding: '10px 16px', marginBottom: 20, width: 'fit-content' }}
            >
              <span style={{ fontSize: 20 }}>{getWeatherEmoji(weather.weathercode)}</span>
              <div>
                <p style={{ color: TEXT, fontSize: 15, fontWeight: 600 }}>
                  {temperature}° · {city}
                </p>
                <p style={{ color: DIM, fontSize: 11 }}>{getTempGuide(temperature)}</p>
              </div>
            </div>
          )}

          <p style={{ color: DIM, fontSize: 18, lineHeight: 1.8, marginBottom: 28 }}>
            스타일 키워드를 골라주시면<br />
            딱 맞는 OOTD를 추천해드려요.
          </p>

          {/* 스타일 태그 */}
          <div className="flex flex-wrap gap-3" style={{ marginBottom: 32 }}>
            {GENRES.map(genre => {
              const active = selectedGenre === genre
              return (
                <button
                  key={genre}
                  onClick={() => toggleGenre(genre)}
                  className="cursor-pointer transition-all"
                  style={{
                    padding: '10px 22px',
                    borderRadius: 20,
                    fontSize: 15,
                    fontWeight: active ? 600 : 400,
                    backgroundColor: active ? ACCENT : TAG_BG,
                    color: active ? BTN_TEXT : DIM,
                    border: `1px solid ${active ? ACCENT : BORDER}`,
                  }}
                >
                  {genre}
                </button>
              )
            })}
          </div>

          {/* CTA 버튼 */}
          <button
            onClick={handleRecommend}
            disabled={loading || !selectedGenre}
            className="flex items-center justify-between cursor-pointer hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
            style={{
              width: '100%',
              backgroundColor: ACCENT_BTN,
              color: BTN_TEXT,
              fontWeight: 600,
              fontSize: 16,
              padding: '16px 24px',
              borderRadius: 12,
              border: 'none',
            }}
          >
            {loading ? '추천 중...' : '오늘의 OOTD 추천받기'}
            {!loading && <span style={{ fontSize: 20 }}>→</span>}
          </button>
        </div>

        {/* ── 오른쪽 패널 — 플랫레이 이미지 ── */}
        <div
          className="flex items-center justify-center"
          style={{
            width: '45%',
            minWidth: 300,
            backgroundColor: PANEL,
            borderLeft: `1px solid ${PANEL_BORDER}`,
            overflow: 'hidden',
          }}
        >
          <img
            src="/remove_background (6).png"
            alt="outfit flatlay"
            style={{
              width: '85%',
              height: '85%',
              objectFit: 'contain',
              padding: '24px',
            }}
          />
        </div>
      </div>
    </div>
  )
}
