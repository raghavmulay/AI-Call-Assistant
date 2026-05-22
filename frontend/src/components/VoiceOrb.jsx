export default function VoiceOrb({ speaking, listening }) {
  const state = speaking ? "speaking" : listening ? "listening" : "idle"

  const glowColor = {
    speaking: "bg-cyan-500",
    listening: "bg-emerald-500",
    idle: "bg-indigo-600",
  }[state]

  const ringColor = {
    speaking: "border-cyan-400/40",
    listening: "border-emerald-400/40",
    idle: "border-white/8",
  }[state]

  const coreGradient = {
    speaking: "from-cyan-400 via-blue-500 to-indigo-600",
    listening: "from-emerald-400 via-teal-500 to-cyan-600",
    idle: "from-zinc-600 via-zinc-700 to-zinc-900",
  }[state]

  return (
    <div className="relative flex items-center justify-center w-64 h-64">
      {/* Outer glow */}
      <div className={`absolute h-64 w-64 rounded-full blur-3xl opacity-25 transition-all duration-700 ${glowColor} ${speaking ? "animate-pulse" : ""}`} />

      {/* Outer ring — slow ping when active */}
      <div className={`absolute h-56 w-56 rounded-full border transition-all duration-500 ${ringColor} ${speaking || listening ? "animate-ping opacity-20" : "opacity-30"}`} />

      {/* Mid ring */}
      <div className={`absolute h-48 w-48 rounded-full border transition-all duration-500 ${ringColor} opacity-40`} />

      {/* Core orb */}
      <div
        className={`relative h-36 w-36 rounded-full bg-gradient-to-br ${coreGradient} flex items-center justify-center transition-all duration-500 ${
          speaking ? "scale-110 shadow-[0_0_60px_rgba(34,211,238,0.4)]" :
          listening ? "scale-105 shadow-[0_0_40px_rgba(52,211,153,0.35)]" :
          "scale-100"
        }`}
      >
        <div className="h-20 w-20 rounded-full bg-black/30 backdrop-blur-sm flex items-center justify-center">
          {speaking ? (
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
            </svg>
          ) : listening ? (
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
            </svg>
          ) : (
            <svg className="w-8 h-8 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
            </svg>
          )}
        </div>
      </div>
    </div>
  )
}
