export default function ChatPanel({ messages = [], partialText = "" }) {
  const isEmpty = messages.length === 0 && !partialText

  return (
    <div className="w-full max-w-3xl mx-auto space-y-5">
      {isEmpty && (
        <p className="text-zinc-600 text-sm text-center py-4">
          Press the mic button and start speaking…
        </p>
      )}

      {messages.map((msg, i) => (
        <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
          <div className={`h-8 w-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold mt-0.5 ${
            msg.role === "user"
              ? "bg-gradient-to-br from-violet-500 to-purple-700"
              : "bg-gradient-to-br from-cyan-400 to-blue-600"
          }`}>
            {msg.role === "user" ? "S" : "AI"}
          </div>

          <div className={`flex flex-col gap-1 max-w-[72%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
            <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
              msg.role === "user"
                ? "bg-white text-zinc-900 rounded-tr-sm"
                : "bg-white/6 text-white border border-white/8 rounded-tl-sm"
            } ${msg._streaming ? "opacity-80" : ""}`}>
              {msg.text}
              {msg._streaming && <span className="inline-block w-1.5 h-3.5 bg-cyan-400 ml-1 animate-pulse rounded-sm align-middle" />}
            </div>
            {msg.time && <span className="text-zinc-600 text-xs px-1">{msg.time}</span>}
          </div>
        </div>
      ))}

      {/* Live partial transcript */}
      {partialText && (
        <div className="flex gap-3 flex-row-reverse">
          <div className="h-8 w-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold mt-0.5 bg-gradient-to-br from-violet-500 to-purple-700 opacity-60">
            S
          </div>
          <div className="flex flex-col gap-1 max-w-[72%] items-end">
            <div className="px-4 py-3 rounded-2xl rounded-tr-sm text-sm leading-relaxed bg-white/10 text-zinc-300 border border-white/8 italic">
              {partialText}
              <span className="inline-block w-1 h-3 bg-zinc-400 ml-1 animate-pulse rounded-sm align-middle" />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
