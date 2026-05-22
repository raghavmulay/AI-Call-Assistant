"""
TTS module — edge-tts (Microsoft Edge neural voices).
Much faster and more natural than pyttsx3.
"""
import asyncio
import tempfile
import os
import edge_tts
import pygame

VOICE = "en-IN-NeerjaNeural"   # Indian English female; change to en-US-JennyNeural if preferred


async def _synthesize(text: str, path: str) -> None:
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(path)


def speak(text: str) -> None:
    if not text or not text.strip():
        return

    print(f"[Assistant]: {text}")

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()

    try:
        asyncio.run(_synthesize(text, tmp.name))

        pygame.mixer.init()
        pygame.mixer.music.load(tmp.name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        pygame.mixer.quit()
    except Exception as e:
        print(f"[TTS Error]: {e}")
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
