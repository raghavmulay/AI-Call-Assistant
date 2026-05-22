export default function Sidebar({ onNewChat }) {
  const sessions = [
    { title: "Fees Inquiry", preview: "What are the IT dept fees?", time: "2m ago" },
    { title: "Hostel Info", preview: "Tell me about hostel facilities", time: "1h ago" },
    { title: "Admission Dates", preview: "When does admission start?", time: "Yesterday" },
  ]

  return (
    <div className="w-75 bg-zinc-950 border-r border-white/8 h-screen flex flex-col">
      <div className="p-5 border-b border-white/8">
        <div className="flex items-center gap-3 mb-4">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-sm font-bold">
            AI
          </div>
          <div>
            <h1 className="text-white font-semibold leading-tight">Campus Assistant</h1>
            <p className="text-zinc-500 text-xs">VIT Pune</p>
          </div>
        </div>
        <button
          onClick={onNewChat}
          className="w-full bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-xl py-2.5 text-sm font-medium transition-all flex items-center justify-center gap-2"
        >
          <span className="text-lg leading-none">+</span> New Conversation
        </button>
      </div>

      <div className="px-3 pt-4 pb-1">
        <p className="text-zinc-500 text-xs font-medium uppercase tracking-wider px-2">Recent</p>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {sessions.map((s, i) => (
          <div
            key={i}
            className={`rounded-xl p-3.5 cursor-pointer transition-all ${
              i === 0 ? "bg-white/8 border border-white/10" : "hover:bg-white/5"
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <p className="text-white text-sm font-medium">{s.title}</p>
              <span className="text-zinc-600 text-xs">{s.time}</span>
            </div>
            <p className="text-zinc-500 text-xs truncate">{s.preview}</p>
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-white/8">
        <div className="flex items-center gap-3 px-1">
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-violet-500 to-purple-700 flex items-center justify-center text-xs font-bold">
            S
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white text-sm font-medium">Student</p>
            <p className="text-zinc-500 text-xs">VIT Pune</p>
          </div>
          <div className="h-2 w-2 rounded-full bg-emerald-400" />
        </div>
      </div>
    </div>
  )
}
