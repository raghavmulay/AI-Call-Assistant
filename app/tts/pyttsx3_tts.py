import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
from elevenlabs.play import play

load_dotenv()
_client = ElevenLabs(api_key=os.getenv("API_KEY_ELEVEN_LABS"))

def speak(text: str) -> None:
    print(f"[Assistant]: {text}")
    audio = _client.text_to_speech.convert(
        text=text,
        voice_id="nPczCjzI2devNBz1zQrb",  # Brian
        model_id="eleven_flash_v2"
    )
    play(audio)
