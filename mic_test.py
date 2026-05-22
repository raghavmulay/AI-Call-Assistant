"""
mic_test.py — Test which microphone device captures audio correctly.
"""
import sounddevice as sd
import numpy as np
import time

print("Testing microphone devices...\n")
print("Available input devices:")
devices = sd.query_devices()
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        print(f"  [{i}] {d['name']} (channels: {d['max_input_channels']})")

print("\nTesting default device for 3 seconds — SPEAK NOW...")
print("(watching for audio level above 0.01)\n")

detected = []

def callback(indata, frames, time_info, status):
    level = np.abs(indata).mean()
    bar = "#" * int(level * 500)
    print(f"\r  Level: {level:.4f}  {bar:<40}", end="", flush=True)
    if level > 0.01:
        detected.append(level)

with sd.InputStream(samplerate=16000, channels=1, dtype='int16', callback=callback):
    time.sleep(5)

print(f"\n\nDetected {len(detected)} frames with audio above threshold.")
if detected:
    print(f"Max level: {max(detected):.4f}")
    print("\n✅ Default microphone is working!")
else:
    print("\n❌ No audio detected on default device.")
    print("Try running: python mic_test.py --device N")
    print("where N is the device number from the list above.")
