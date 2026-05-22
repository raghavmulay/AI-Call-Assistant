"""
TTS module — pyttsx3.
Engine is re-initialized on every speak() call to avoid conflicts
with sounddevice (STT) holding the Windows audio driver.
Reusing a single engine instance causes silent failures after the first call.
"""
import pyttsx3
import time


def _make_engine():
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)      # slightly slower = clearer voice
    engine.setProperty("volume", 1.0)
    voices = engine.getProperty("voices")
    if voices and len(voices) > 1:
        engine.setProperty("voice", voices[1].id)   # index 1 = female on most Windows
    return engine


def speak(text: str) -> None:
    if not text or not text.strip():
        return

    print(f"[Assistant]: {text}")
    start = time.time()

    try:
        engine = _make_engine()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        print(f"[TTS Time]: {time.time() - start:.2f} seconds")
    except RuntimeError as e:
        # runAndWait() can raise RuntimeError if called while loop is running
        print(f"[TTS Error - RuntimeError]: {e}")
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception as e2:
            print(f"[TTS Failed completely]: {e2}")
    except Exception as e:
        print(f"[TTS Error]: {e}")
