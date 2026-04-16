from app.stt.whisper_stt import SpeechToText
from app.intent.intent_handler import get_answer
from app.tts.pyttsx3_tts import speak

def main():
    stt = SpeechToText(model_size="base")
    speak("Hello! I am your college assistant. How can I help you?")

    while True:
        user_text = stt.listen()

        if not user_text:
            continue

        print(f"[You]: {user_text}")

        if any(word in user_text.lower() for word in ("exit", "quit", "bye")):
            speak("Goodbye!")
            break

        answer = get_answer(user_text)
        speak(answer)

if __name__ == "__main__":
    main()
