import os
import queue
import tempfile
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
from collections import deque
from faster_whisper import WhisperModel

class SpeechToText:
    def __init__(self, model_size="base"):
        """
        Initialize the Faster-Whisper STT model.
        Optimized for CPU usage with int8 compute type.
        """
        self.sample_rate = 16000
        self.channels = 1
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self._q = queue.Queue()

    def _audio_callback(self, indata, frames, time, status):
        """Callback to handle incoming audio stream chunks."""
        if status:
            pass  # Suppress internal errors like underrun during active recording
        self._q.put(indata.copy())

    def record_audio(self) -> str:
        """
        Record audio from the microphone to a temporary WAV file.
        Uses RMS energy detection to start and stop recording automatically.
        """
        energy_threshold = 0.015  # Adjust threshold based on background noise
        silence_duration = 1.5    # Hold duration for silence (in seconds)
        chunk_duration = 0.1      # Audio chunk size (in seconds)

        chunk_samples = int(self.sample_rate * chunk_duration)
        max_silence_chunks = int(silence_duration / chunk_duration)

        audio_data = []
        pre_speech_buffer = deque(maxlen=int(0.5 / chunk_duration))  # 0.5s lookback buffer

        is_recording = False
        silence_chunks = 0

        try:
            with sd.InputStream(samplerate=self.sample_rate,
                                channels=self.channels,
                                dtype='float32',
                                blocksize=chunk_samples,
                                callback=self._audio_callback):

                print("\n[Listening for speech...]", end="", flush=True)
                
                while True:
                    chunk = self._q.get()
                    rms = np.sqrt(np.mean(chunk**2))

                    if not is_recording:
                        pre_speech_buffer.append(chunk)
                        if rms > energy_threshold:
                            is_recording = True
                            print("\r[Recording...          ]", end="", flush=True)
                            audio_data.extend(pre_speech_buffer)
                            silence_chunks = 0
                    else:
                        audio_data.append(chunk)
                        if rms <= energy_threshold:
                            silence_chunks += 1
                            if silence_chunks >= max_silence_chunks:
                                print("\r[Processing audio...   ]", flush=True)
                                break
                        else:
                            silence_chunks = 0

        except sd.PortAudioError as e:
            print(f"\nMicrophone Error: {e}")
            return None
        except Exception as e:
            print(f"\nRecording Error: {e}")
            return None

        if not audio_data:
            return None

        # Assemble chunks into a single audio array
        full_audio = np.concatenate(audio_data, axis=0)
        full_audio = np.clip(full_audio, -1.0, 1.0)
        int_audio = np.int16(full_audio * 32767)

        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        try:
            wav.write(temp_path, self.sample_rate, int_audio)
        except Exception as e:
            print(f"Error saving temporary audio: {e}")
            os.remove(temp_path)
            return None

        return temp_path

    def transcribe(self, audio_path: str) -> str:
        """
        Convert saved temporary audio file into text using Faster-Whisper.
        Automatically removes the temporary file when finished.
        """
        if not audio_path or not os.path.exists(audio_path):
            return ""

        try:
            # Beam size tuning: 5 is a good balance between speed and accuracy
            segments, info = self.model.transcribe(audio_path, beam_size=5)
            transcription = "".join([segment.text for segment in segments])
            return transcription.strip()
        except Exception as e:
            print(f"Transcription Error: {e}")
            return ""
        finally:
            try:
                os.remove(audio_path)
            except OSError:
                pass

    def listen(self) -> str:
        """
        Complete pipeline: Listens for audio, saves it, transcribes, and returns the text.
        """
        audio_path = self.record_audio()
        if audio_path:
            return self.transcribe(audio_path)
        return ""
