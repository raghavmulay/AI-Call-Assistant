import pyttsx3
import time

def speak(text: str) -> None:

    print(f"[Assistant]: {text}")

    start = time.time()

    engine = pyttsx3.init()

    engine.setProperty('rate', 200)
    engine.setProperty('volume', 1.0)

    voices = engine.getProperty('voices')

    if voices:
        engine.setProperty('voice', voices[1].id)

    engine.say(text)

    engine.runAndWait()

    end = time.time()

    print(f"[TTS Time]: {end - start:.2f} seconds")