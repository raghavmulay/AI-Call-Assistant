import os
import queue
import tempfile
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
from collections import deque
from faster_whisper import WhisperModel
import time

# ── Tunable constants ──────────────────────────────────────────────
SAMPLE_RATE       = 16000
CHANNELS          = 1
ENERGY_THRESHOLD  = 0.02     # RMS threshold to detect speech start
                              # raise if mic picks up too much background noise
                              # lower if your voice is soft
SILENCE_DURATION  = 1.2      # seconds of silence before stopping recording
                              # was 0.5 — too short, was cutting off sentences
CHUNK_DURATION    = 0.1      # audio chunk size in seconds
PRE_SPEECH_BUFFER = 0.4      # seconds of audio kept before speech starts
                              # prevents clipping the first word
MAX_RECORD_SEC    = 15       # hard cap — stops runaway recording
# ──────────────────────────────────────────────────────────────────

# Whisper sometimes hallucinates these strings on silence/noise
_JUNK_TRANSCRIPTIONS = {
    "", "you", "the", ".", " ", "thank you.", "thanks.",
    "bye.", "okay.", "hmm.", "um.", "uh.", "...",
}

# Common mishearings specific to Indian English + college domain
# Format: "what whisper hears" -> "what it should be"
_CORRECTIONS = {
    "mht set":      "MHT-CET",
    "mht cet":      "MHT-CET",
    "mhtcet":       "MHT-CET",
    "jee mains":    "JEE Main",
    "entc":         "ENTC",
    "lpa":          "LPA",
    "cgpa":         "CGPA",
    "mahadbt":      "MahaDBT",
    "maha dbt":     "MahaDBT",
    "aadhar":       "Aadhar",
    "adhar":        "Aadhar",
    "aadhaar":      "Aadhar",
    "ebc":          "EBC",
    "obc":          "OBC",
    "sc st":        "SC/ST",
    "fees structure": "fee structure",
    "what is fees":   "what is the fee",
}


def _correct(text: str) -> str:
    """Apply known mishearing corrections."""
    t = text.lower()
    for wrong, right in _CORRECTIONS.items():
        t = t.replace(wrong, right.lower())
    # Restore original casing for first letter
    return t.strip().capitalize()


class SpeechToText:
    def __init__(self, model_size: str = "base"):
        """
        model_size options (tradeoff speed vs accuracy):
          tiny   — fastest, least accurate (~1s)
          base   — good balance (~1.5s)           ← recommended
          small  — better accuracy (~3s)
          medium — best accuracy, slow (~8s)
        """
        print(f"[STT] Loading Whisper model: {model_size} ...")
        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",   # quantized for CPU speed
        )
        self._q = queue.Queue()
        print(f"[STT] Model ready.")

    def _audio_callback(self, indata, frames, time_info, status):
        self._q.put(indata.copy())

    def record_audio(self) -> str | None:
        chunk_samples      = int(SAMPLE_RATE * CHUNK_DURATION)
        max_silence_chunks = int(SILENCE_DURATION / CHUNK_DURATION)
        max_chunks         = int(MAX_RECORD_SEC / CHUNK_DURATION)
        pre_buffer         = deque(maxlen=int(PRE_SPEECH_BUFFER / CHUNK_DURATION))

        audio_data    = []
        is_recording  = False
        silence_count = 0
        total_chunks  = 0

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                blocksize=chunk_samples,
                callback=self._audio_callback,
            ):
                print("\n[Listening...          ]", end="", flush=True)

                while True:
                    chunk = self._q.get()
                    rms   = float(np.sqrt(np.mean(chunk ** 2)))
                    total_chunks += 1

                    if not is_recording:
                        pre_buffer.append(chunk)
                        if rms > ENERGY_THRESHOLD:
                            is_recording = True
                            silence_count = 0
                            print("\r[Recording...          ]", end="", flush=True)
                            audio_data.extend(pre_buffer)
                    else:
                        audio_data.append(chunk)
                        if rms <= ENERGY_THRESHOLD:
                            silence_count += 1
                            if silence_count >= max_silence_chunks:
                                print("\r[Processing audio...   ]", flush=True)
                                break
                        else:
                            silence_count = 0

                        # Hard cap — prevent infinite recording
                        if total_chunks >= max_chunks:
                            print("\r[Max duration reached...]\n", flush=True)
                            break

        except sd.PortAudioError as e:
            print(f"\n[STT] Microphone error: {e}")
            return None
        except Exception as e:
            print(f"\n[STT] Recording error: {e}")
            return None

        if not audio_data:
            return None

        full_audio = np.concatenate(audio_data, axis=0)
        full_audio = np.clip(full_audio, -1.0, 1.0)
        int_audio  = np.int16(full_audio * 32767)

        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            wav.write(temp_path, SAMPLE_RATE, int_audio)
        except Exception as e:
            print(f"[STT] Error saving audio: {e}")
            os.remove(temp_path)
            return None

        return temp_path

    def transcribe(self, audio_path: str) -> str:
        if not audio_path or not os.path.exists(audio_path):
            return ""

        try:
            start = time.time()
            segments, info = self.model.transcribe(
                audio_path,
                language="en",
                beam_size=5,
                best_of=5,
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": 500,
                    "speech_pad_ms": 200,
                },
                condition_on_previous_text=False,
                temperature=0.0,
                # Domain-specific prompt — massively improves recognition of
                # college/admission terms, Indian names, and abbreviations.
                # Whisper uses this as context to bias its predictions.
                initial_prompt=(
                    "College admission assistant. "
                    "Topics: fees, documents, eligibility, cutoff, MHT-CET, JEE, "
                    "branches, Computer Engineering, Information Technology, ENTC, "
                    "Mechanical, Civil, Electrical, hostel, scholarship, placement, "
                    "LPA, marksheet, Aadhar, TC, OBC, SC, ST, EBC, MahaDBT, "
                    "syllabus, subjects, units, modules, CGPA, semester."
                ),
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            elapsed = time.time() - start
            print(f"[STT Time]: {elapsed:.2f} seconds")

            # Filter out junk transcriptions from silence/noise
            if text.lower().rstrip(".!?, ") in _JUNK_TRANSCRIPTIONS:
                return ""

            return _correct(text)

        except Exception as e:
            print(f"[STT] Transcription error: {e}")
            return ""
        finally:
            try:
                os.remove(audio_path)
            except OSError:
                pass

    def listen(self) -> str:
        audio_path = self.record_audio()
        if audio_path:
            return self.transcribe(audio_path)
        return ""
