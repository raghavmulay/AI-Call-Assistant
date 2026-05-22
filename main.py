import asyncio
import uuid
from backend.app.ai.stt.whisper_stt import SpeechToText
from backend.app.ai.tts.edge_tts import speak
from backend.app.ai.orchestrator.orchestrator import process_query

async def main():
    stt = SpeechToText(model_size="base")
    session_id = str(uuid.uuid4())
    
    print("\n[AI Campus Assistant] Initialized. Type 'exit' to quit.\n")
    speak("Hi! I'm your college assistant. How can I help?")

    while True:
        # 1. Listen for voice input
        user_text = stt.listen()

        if not user_text:
            continue

        print(f"[You]: {user_text}")

        if any(word in user_text.lower() for word in ("exit", "quit", "bye")):
            speak("Goodbye! Have a great day.")
            break

        # 2. Process through central orchestrator
        # CLI doesn't have DB/User context by default, passing empty
        result = await process_query(
            user_input=user_text,
            session_id=session_id
        )

        answer = result.get("response", "I'm sorry, I couldn't process that.")
        print(f"[AI]: {answer}")
        
        # 3. Speak the response
        speak(answer)

if __name__ == "__main__":
    asyncio.run(main())
