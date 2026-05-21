from app.stt.whisper_stt import SpeechToText
from app.intent.intent_handler import get_answer
from app.tts.edge_tts import speak
from app.session import session as sess

def main():
    stt = SpeechToText(model_size="base")
    speak("Hi! I'm your college assistant. How can I help?")

    while True:
        user_text = stt.listen()

        if not user_text:
            continue

        print(f"[You]: {user_text}")

        answer = get_answer(user_text)
        speak(answer)

        if any(word in user_text.lower() for word in ("exit", "quit", "bye")):
            break

if __name__ == "__main__":
    main()
