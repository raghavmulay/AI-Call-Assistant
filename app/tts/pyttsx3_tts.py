import pyttsx3

def speak(text: str) -> None:
    """Convert text to speech and block until done."""
    print(f"[Assistant]: {text}")
    engine = pyttsx3.init()
    engine.setProperty("rate", 160)
    engine.setProperty("volume", 1.0)
    engine.say(text)
    engine.runAndWait()
    engine.stop()
