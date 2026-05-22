import { useRef, useEffect } from "react"
import Sidebar from "./components/Sidebar"
import VoiceOrb from "./components/VoiceOrb"
import Waveform from "./components/Waveform"
import Controls from "./components/Controls"
import ChatPanel from "./components/ChatPanel"
import { useVoiceSocket } from "./hooks/useVoiceSocket"

export default function App() {
  const { connected, listening, speaking, messages, partialText, error, toggle } = useVoiceSocket()
  const chatBottomRef = useRef(null)

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, partialText])

  const statusLabel = speaking ? "Speaking" : listening ? "Listening" : connected ? "Connected" : "Ready"
  const statusColor = speaking
    ? "bg-cyan-500/15 text-cyan-400 border-cyan-500/20"
    : listening
    ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/20"
    : connected
    ? "bg-blue-500/15 text-blue-400 border-blue-500/20"
    : "bg-white/5 text-zinc-400 border-white/10"
  const dotColor = speaking ? "bg-cyan-400" : listening ? "bg-emerald-400" : connected ? "bg-blue-400" : "bg-zinc-500"

  return (
    <div
      className="h-screen bg-[#080808] text-white flex overflow-hidden"
      style={{
        backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.03) 1px, transparent 1px)",
        backgroundSize: "28px 28px",
      }}
    >
      <Sidebar onNewChat={() => {}} />

      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 flex flex-col items-center justify-center gap-8 relative px-8">
          <div className={`absolute inset-0 pointer-events-none transition-all duration-1000 ${speaking ? "opacity-100" : "opacity-0"}`}>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-125 w-125nded-full bg-cyan-500/5 blur-3xl" />
          </div>

          <VoiceOrb speaking={speaking} listening={listening} />
          <Waveform speaking={speaking} listening={listening} />

          <div className="text-center space-y-3">
            <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full border text-sm font-medium transition-all duration-300 ${statusColor}`}>
              <span className={`h-1.5 w-1.5 rounded-full ${dotColor} ${speaking || listening ? "animate-pulse" : ""}`} />
              {statusLabel}
            </div>
            <p className="text-zinc-500 text-sm">Realtime AI Voice Assistant</p>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2.5 text-red-400 text-sm max-w-sm text-center">
              {error}
            </div>
          )}

          <Controls connected={connected} listening={listening} speaking={speaking} onToggle={toggle} />
        </div>

        {/* Chat transcript */}
        <div className="h-75 border-t border-white/8 bg-black/30 backdrop-blur-xl">
          <div className="h-full overflow-y-auto px-6 py-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-zinc-500 text-xs font-medium uppercase tracking-wider">
                Transcript
                {messages.length > 0 && (
                  <span className="text-zinc-600 normal-case font-normal ml-1">
                    · {Math.ceil(messages.length / 2)} turns
                  </span>
                )}
              </p>
            </div>
            <ChatPanel messages={messages} partialText={partialText} />
            <div ref={chatBottomRef} />
          </div>
        </div>
      </div>
    </div>
  )
}
