"""
client_streamer.py — CLI microphone streaming client for Stage 3 Part 1 testing.

Usage:
    python client_streamer.py --session my-session-1 --url ws://localhost:8000/ws/audio

Requirements:
    pip install sounddevice websockets numpy
"""
import asyncio
import argparse
import struct
import time
import json
import io
import threading
import numpy as np
import sounddevice as sd
import websockets
from websockets.exceptions import ConnectionClosed

try:
    import pygame
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    PYGAME_OK = True
except Exception:
    PYGAME_OK = False
    print("[warn] pygame not available — TTS audio will not play")

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_MS = 40
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_MS / 1000)
DTYPE = "int16"
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_BASE_DELAY = 1.0

_tts_expecting_audio = False  # True after tts_chunk JSON, next binary = audio


def _play_audio_bytes(audio_bytes: bytes):
    """Play MP3/audio bytes via pygame in a background thread."""
    if not PYGAME_OK or not audio_bytes:
        return
    def _play():
        try:
            buf = io.BytesIO(audio_bytes)
            pygame.mixer.music.load(buf)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.03)
        except Exception as e:
            print(f"\n[playback error] {e}")
    threading.Thread(target=_play, daemon=True).start()


async def _recv_loop(ws, session_id: str):
    """Consume server messages: respond to pings, play TTS audio."""
    global _tts_expecting_audio
    try:
        async for raw in ws:
            if isinstance(raw, bytes):
                # Binary frame = TTS audio bytes
                if _tts_expecting_audio:
                    _tts_expecting_audio = False
                    _play_audio_bytes(raw)
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue
            msg_type = data.get("type")
            if msg_type == "ping":
                await ws.send(json.dumps({"type": "pong", "session_id": session_id, "timestamp": time.time()}))
            elif msg_type == "tts_chunk":
                print(f"\n[tts] {data.get('text', '')}")
                _tts_expecting_audio = True
            elif msg_type == "tts_stream_start":
                print("\n[tts] Speaking...")
            elif msg_type == "tts_stream_end":
                print("\n[tts] Done.")
            elif msg_type == "transcript":
                print(f"\n[you] {data.get('text', '')}")
            elif msg_type == "error":
                print(f"\n[server error] {data.get('code')}: {data.get('message')}")
    except (ConnectionClosed, asyncio.CancelledError):
        pass


async def _stream_once(url: str, session_id: str, chunk_id_start: int) -> int:
    """
    Open one WebSocket connection and stream until disconnect.
    Returns the next chunk_id to use on reconnect.
    """
    full_url = f"{url}/{session_id}"
    chunk_id = chunk_id_start
    audio_queue: asyncio.Queue = asyncio.Queue(maxsize=500)
    loop = asyncio.get_event_loop()

    def _callback(indata, frames, time_info, status):
        if status:
            print(f"\n[sounddevice] {status}")
        if audio_queue.full():
            return  # drop frame silently — consumer is behind
        loop.call_soon_threadsafe(audio_queue.put_nowait, indata.copy())

    async with websockets.connect(full_url, ping_interval=None) as ws:
        print(f"[client] Connected → {full_url}  (chunk_id starts at {chunk_id})")
        recv_task = asyncio.create_task(_recv_loop(ws, session_id))

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=CHUNK_SAMPLES,
                callback=_callback,
            ):
                while True:
                    audio_chunk: np.ndarray = await audio_queue.get()
                    raw_bytes = audio_chunk.tobytes()
                    frame = struct.pack("<I", chunk_id) + raw_bytes
                    await ws.send(frame)
                    print(f"\r[client] chunk={chunk_id:06d}  bytes={len(raw_bytes)}", end="", flush=True)
                    chunk_id += 1
        except (ConnectionClosed, asyncio.CancelledError):
            pass
        except sd.PortAudioError as e:
            print(f"\n[microphone error] {e}")
        finally:
            recv_task.cancel()
            await asyncio.gather(recv_task, return_exceptions=True)

    return chunk_id


async def stream_microphone(url: str, session_id: str):
    chunk_id = 0
    attempt = 0

    print(f"[client] Streaming microphone at {SAMPLE_RATE}Hz / {CHUNK_MS}ms chunks. Ctrl+C to stop.")

    while attempt <= MAX_RECONNECT_ATTEMPTS:
        try:
            chunk_id = await _stream_once(url, session_id, chunk_id)
            # Clean exit (server closed or Ctrl+C propagated)
            break
        except (ConnectionClosed, OSError) as e:
            attempt += 1
            if attempt > MAX_RECONNECT_ATTEMPTS:
                print(f"\n[client] Max reconnect attempts reached. Exiting.")
                break
            delay = RECONNECT_BASE_DELAY * (2 ** (attempt - 1))
            print(f"\n[client] Disconnected ({e}). Reconnecting in {delay:.1f}s (attempt {attempt}/{MAX_RECONNECT_ATTEMPTS})...")
            await asyncio.sleep(delay)
        except KeyboardInterrupt:
            print("\n[client] Stopped by user.")
            break

    print("\n[client] Stream ended.")


def main():
    parser = argparse.ArgumentParser(description="Real-time microphone WebSocket streamer")
    parser.add_argument("--session", default="test-session-1", help="Session ID")
    parser.add_argument("--url", default="ws://localhost:8000/ws/audio", help="WebSocket base URL")
    args = parser.parse_args()
    try:
        asyncio.run(stream_microphone(args.url, args.session))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
