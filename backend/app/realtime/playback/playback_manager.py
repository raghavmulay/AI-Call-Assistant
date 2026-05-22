"""
playback_manager.py — Client-side audio playback for TTS responses.

Stage 3 Part 3 additions:
  - interrupt(): immediately stop current playback
  - clear(): flush pending queue on barge-in
  - Chunk-based sequential playback
"""
import asyncio
import io
from typing import Optional


def _play_sync(audio_bytes: bytes, encoding: str, stop_flag: list):
    """Synchronous playback with stop support via stop_flag[0]."""
    try:
        import pygame
        pygame.mixer.init()
        buf = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(buf, encoding)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if stop_flag[0]:
                pygame.mixer.music.stop()
                break
            pygame.time.wait(30)
        pygame.mixer.quit()
    except Exception:
        pass


class PlaybackManager:
    """
    Manages queued audio playback for a session.
    Supports interruption (barge-in) and chunk streaming.
    """

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None
        self._stop_flag: list = [False]   # mutable flag passed to sync thread

    def start(self):
        self._stop_flag[0] = False
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._worker())

    async def enqueue(self, audio_bytes: bytes, encoding: str = "mp3"):
        """Add audio chunk to playback queue."""
        if audio_bytes:
            await self._queue.put((audio_bytes, encoding))

    def interrupt(self):
        """Stop current playback immediately and clear queue."""
        self._stop_flag[0] = True
        self.clear()

    def clear(self):
        """Flush all pending audio from queue."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break

    def resume(self):
        """Reset stop flag after interruption."""
        self._stop_flag[0] = False

    async def _worker(self):
        while True:
            audio_bytes, encoding = await self._queue.get()
            if not self._stop_flag[0]:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None, _play_sync, audio_bytes, encoding, self._stop_flag
                )
            self._queue.task_done()

    def stop(self):
        self.interrupt()
        if self._task:
            self._task.cancel()
            self._task = None


playback_manager = PlaybackManager()
