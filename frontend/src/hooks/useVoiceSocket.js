import { useRef, useState, useCallback } from "react"

const WS_URL = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/audio`
const SAMPLE_RATE = 16000
const CHUNK_MS = 40 // send audio every 40ms

export function useVoiceSocket(sessionId = "web-session-1") {
  const [connected, setConnected] = useState(false)
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [messages, setMessages] = useState([])
  const [partialText, setPartialText] = useState("")
  const [error, setError] = useState(null)

  const wsRef = useRef(null)
  const mediaStreamRef = useRef(null)
  const processorRef = useRef(null)
  const audioCtxRef = useRef(null)
  const chunkIdRef = useRef(0)
  const pendingAudioRef = useRef([]) // queued MP3 chunks
  const expectingBytesRef = useRef(false) // next WS message is audio bytes
  const audioQueueRef = useRef([])
  const playingRef = useRef(false)

  // ── Audio playback queue ──────────────────────────────────────────────────
  async function playNextChunk() {
    if (playingRef.current || audioQueueRef.current.length === 0) return
    playingRef.current = true
    const blob = audioQueueRef.current.shift()
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    audio.onended = () => {
      URL.revokeObjectURL(url)
      playingRef.current = false
      if (audioQueueRef.current.length > 0) {
        playNextChunk()
      } else {
        setSpeaking(false)
      }
    }
    audio.onerror = () => {
      playingRef.current = false
      playNextChunk()
    }
    await audio.play().catch(() => { playingRef.current = false })
  }

  function enqueueAudio(bytes) {
    const blob = new Blob([bytes], { type: "audio/mpeg" })
    audioQueueRef.current.push(blob)
    setSpeaking(true)
    playNextChunk()
  }

  function clearAudioQueue() {
    audioQueueRef.current = []
    playingRef.current = false
    setSpeaking(false)
  }

  // ── WebSocket message handler ─────────────────────────────────────────────
  function handleMessage(event) {
    // Binary frame = TTS audio bytes
    if (event.data instanceof ArrayBuffer || event.data instanceof Blob) {
      const process = async () => {
        const buf = event.data instanceof Blob
          ? await event.data.arrayBuffer()
          : event.data
        enqueueAudio(buf)
      }
      process()
      return
    }

    let msg
    try { msg = JSON.parse(event.data) } catch { return }

    switch (msg.type) {
      case "transcript":
        setPartialText("")
        setListening(false)
        setMessages(prev => [...prev, {
          role: "user",
          text: msg.text,
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        }])
        break

      case "partial_transcript":
        setPartialText(msg.text)
        setListening(true)
        break

      case "tts_stream_start":
        clearAudioQueue()
        setSpeaking(true)
        break

      case "tts_chunk":
        // next binary frame is the audio for this chunk's text
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last?.role === "assistant" && last._streaming) {
            return [...prev.slice(0, -1), { ...last, text: last.text + " " + msg.text }]
          }
          return [...prev, {
            role: "assistant",
            text: msg.text,
            time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            _streaming: true,
          }]
        })
        break

      case "tts_stream_end":
        setSpeaking(audioQueueRef.current.length > 0 || playingRef.current)
        setMessages(prev => prev.map(m => ({ ...m, _streaming: false })))
        break

      case "tts_stream_interrupted":
        clearAudioQueue()
        setMessages(prev => prev.map(m => ({ ...m, _streaming: false })))
        break

      case "barge_in":
        clearAudioQueue()
        setListening(true)
        break

      case "ping":
        wsRef.current?.send(JSON.stringify({ type: "pong", session_id: sessionId }))
        break

      case "error":
        setError(msg.message)
        break

      default:
        break
    }
  }

  // ── Start mic + WebSocket ─────────────────────────────────────────────────
  const connect = useCallback(async () => {
    if (wsRef.current) return
    setError(null)

    // 1. Open WebSocket
    const ws = new WebSocket(`${WS_URL}/${sessionId}`)
    ws.binaryType = "arraybuffer"
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => { setConnected(false); setListening(false); setSpeaking(false) }
    ws.onerror = () => setError("WebSocket connection failed. Is the backend running?")
    ws.onmessage = handleMessage

    // 2. Get microphone
    let stream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: { sampleRate: SAMPLE_RATE, channelCount: 1 }, video: false })
    } catch {
      setError("Microphone access denied.")
      ws.close()
      wsRef.current = null
      return
    }
    mediaStreamRef.current = stream

    // 3. Set up AudioWorklet / ScriptProcessor to capture PCM16
    const audioCtx = new AudioContext({ sampleRate: SAMPLE_RATE })
    audioCtxRef.current = audioCtx
    const source = audioCtx.createMediaStreamSource(stream)

    // ScriptProcessor — widely supported, no worklet needed
    const processor = audioCtx.createScriptProcessor(SAMPLE_RATE * CHUNK_MS / 1000, 1, 1)
    processorRef.current = processor

    processor.onaudioprocess = (e) => {
      if (ws.readyState !== WebSocket.OPEN) return
      const float32 = e.inputBuffer.getChannelData(0)
      // Convert Float32 → PCM16
      const pcm16 = new Int16Array(float32.length)
      for (let i = 0; i < float32.length; i++) {
        pcm16[i] = Math.max(-32768, Math.min(32767, float32[i] * 32768))
      }
      // Prepend 4-byte little-endian chunk_id
      const id = chunkIdRef.current++
      const buf = new ArrayBuffer(4 + pcm16.byteLength)
      const view = new DataView(buf)
      view.setUint32(0, id, true) // little-endian
      new Int16Array(buf, 4).set(pcm16)
      ws.send(buf)
    }

    source.connect(processor)
    processor.connect(audioCtx.destination)
    setListening(true)
  }, [sessionId])

  // ── Stop mic + WebSocket ──────────────────────────────────────────────────
  const disconnect = useCallback(() => {
    processorRef.current?.disconnect()
    processorRef.current = null
    audioCtxRef.current?.close()
    audioCtxRef.current = null
    mediaStreamRef.current?.getTracks().forEach(t => t.stop())
    mediaStreamRef.current = null
    wsRef.current?.send(JSON.stringify({ type: "disconnect", session_id: sessionId }))
    wsRef.current?.close()
    wsRef.current = null
    clearAudioQueue()
    setConnected(false)
    setListening(false)
    setSpeaking(false)
    setPartialText("")
    chunkIdRef.current = 0
  }, [sessionId])

  const toggle = useCallback(() => {
    if (connected) disconnect()
    else connect()
  }, [connected, connect, disconnect])

  return { connected, listening, speaking, messages, partialText, error, toggle, connect, disconnect }
}
