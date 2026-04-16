import sys
from app.stt.whisper_stt import SpeechToText

def main():
    print("Initializing Speech-to-Text module...")
    try:
        stt = SpeechToText(model_size="base")
    except Exception as e:
        print(f"Failed to initialize STT module: {e}")
        sys.exit(1)

    print("\nSTT is ready. Starting continuous listening mode.")
    print("Speak into your microphone. (Press Ctrl+C to exit)\n")

    try:
        while True:
            text = stt.listen()
            if text:
                print(f"You said: {text}")
            else:
                print("No speech detected or empty transcription.")
    except KeyboardInterrupt:
        print("\nStopping continuous listening. Goodbye!")
    except Exception as e:
        print(f"\nAn unexpected runtime error occurred: {e}")

if __name__ == "__main__":
    main()
