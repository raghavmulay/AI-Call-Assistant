import { useEffect, useState } from "react"

export default function Waveform({ speaking, listening }) {
  const BAR_COUNT = 28
  const [bars, setBars] = useState(Array(BAR_COUNT).fill(4))

  useEffect(() => {
    if (!speaking && !listening) {
      setBars(Array(BAR_COUNT).fill(4))
      return
    }

    const interval = setInterval(() => {
      setBars(
        Array.from({ length: BAR_COUNT }, (_, i) => {
          const center = BAR_COUNT / 2
          const distFromCenter = Math.abs(i - center) / center
          const maxH = speaking ? 80 : 40
          const base = (1 - distFromCenter) * maxH
          return Math.max(4, base * (0.4 + Math.random() * 0.8))
        })
      )
    }, speaking ? 80 : 140)

    return () => clearInterval(interval)
  }, [speaking, listening])

  const barColor = speaking
    ? "bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.7)]"
    : listening
    ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]"
    : "bg-white/15"

  return (
    <div className="flex items-center gap-[3px] h-24">
      {bars.map((height, i) => (
        <div
          key={i}
          className={`w-[3px] rounded-full transition-all duration-75 ${barColor}`}
          style={{ height: `${height}px` }}
        />
      ))}
    </div>
  )
}
