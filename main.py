"""
AI Personal Assistant — Phase 1
Pipeline: Wake Word → Whisper STT → GPT-4o → Piper TTS
Run:  python main.py          (press-Enter mode, easiest to start)
Run:  python main.py wake     (always-listening wake-word mode)
"""

import os
import json
import time
import wave
import struct
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import pyaudio
import whisper
from groq import Groq
import numpy as np

from config import (
    GROQ_API_KEY,
    PORCUPINE_ACCESS_KEY,
    PIPER_MODEL_PATH,
    PIPER_EXECUTABLE,
    MEMORY_FILE,
    ASSISTANT_NAME,
    YOUR_NAME,
)

# ── Clients & Models (loaded once at startup) ─────────────────────────────────
client = Groq(api_key=GROQ_API_KEY)

print("⏳ Loading Whisper model... (first run downloads ~150MB, be patient)")
whisper_model = whisper.load_model("base")
print("✅ Whisper ready.\n")

# ── Conversation memory ───────────────────────────────────────────────────────
def load_memory() -> list:
    if Path(MEMORY_FILE).exists():
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_memory(history: list):
    """Keep only the last 40 turns so the file never gets too big."""
    with open(MEMORY_FILE, "w") as f:
        json.dump(history[-40:], f, indent=2)

conversation_history: list = load_memory()

# ── GPT-4o system prompt ──────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""
You are {ASSISTANT_NAME}, a personal AI assistant for {YOUR_NAME}.
You live on their laptop and are always available to help.

Personality:
- Warm, direct, and concise. Never overly formal.
- You remember previous conversations — they are passed to you as history.
- You are a VOICE assistant. Keep responses short: 1-3 sentences max unless asked for detail.
- No markdown. No bullet points. No asterisks. Plain spoken English only.
- Current date and time is injected into each user message automatically.
- Always call the user {YOUR_NAME}.
"""

# ── Ask GPT-4o ────────────────────────────────────────────────────────────────
def ask_gpt(user_text: str) -> str:
    global conversation_history

    # Inject current time so the AI always knows when it is
    now = datetime.now().strftime("%A, %d %B %Y — %I:%M %p")
    timestamped = f"[{now}]\n{user_text}"

    conversation_history.append({"role": "user", "content": timestamped})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=300,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        reply = f"Sorry, I had trouble reaching the API. Error: {e}"

    conversation_history.append({"role": "assistant", "content": reply})
    save_memory(conversation_history)
    return reply

# ── Piper TTS ─────────────────────────────────────────────────────────────────
def speak(text: str):
    """Speak text aloud using Piper (offline, free, fast)."""
    print(f"\n🤖 {ASSISTANT_NAME}: {text}\n")

    try:
        result = subprocess.run(
            [PIPER_EXECUTABLE, "--model", PIPER_MODEL_PATH, "--output_raw"],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=15,
        )

        raw_audio = result.stdout

        if not raw_audio:
            print("⚠️  Piper returned no audio.")
            print(f"   stderr: {result.stderr.decode()}")
            return

        # Play the raw 16-bit PCM audio
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=22050,      # Piper's default output sample rate
            output=True,
        )
        stream.write(raw_audio)
        stream.stop_stream()
        stream.close()
        pa.terminate()

    except FileNotFoundError:
        print(f"⚠️  Piper not found at: {PIPER_EXECUTABLE}")
        print("   Run setup.sh first, or update PIPER_EXECUTABLE in config.py")
    except subprocess.TimeoutExpired:
        print("⚠️  Piper timed out.")
    except Exception as e:
        print(f"⚠️  TTS error: {e}")

# ── Whisper STT (mic → text) ──────────────────────────────────────────────────
def record_until_silence(
    silence_threshold: float = 500,   # RMS level below this = silence
    silence_duration: float = 2.0,    # stop after 2s of silence
    max_duration: float = 30.0,       # hard cap at 30s
    sample_rate: int = 16000,         # Whisper expects 16kHz
) -> str:
    """
    Records from mic until the user stops speaking,
    then transcribes with Whisper and returns the text string.
    """
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        frames_per_buffer=1024,
    )

    print("🎙️  Listening... (speak now, I'll stop when you go quiet)")
    frames = []
    silent_chunks = 0
    required_silent_chunks = int(silence_duration * sample_rate / 1024)
    max_chunks = int(max_duration * sample_rate / 1024)

    for _ in range(max_chunks):
        data = stream.read(1024, exception_on_overflow=False)
        frames.append(data)

        # Calculate RMS to detect silence
        count = len(data) // 2
        shorts = struct.unpack(f"{count}h", data)
        rms = (sum(s * s for s in shorts) / len(shorts)) ** 0.5

        if rms < silence_threshold:
            silent_chunks += 1
        else:
            silent_chunks = 0  # reset on any sound

        # Stop if silent long enough (and we have some audio)
        if silent_chunks >= required_silent_chunks and len(frames) > 20:
            break

    stream.stop_stream()
    stream.close()
    pa.terminate()

    # Save to temp WAV for Whisper
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    with wave.open(tmp_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))

    print("🧠 Transcribing with Whisper...")
    result = whisper_model.transcribe(
        tmp_path,
        language="en",
        fp16=False,
        initial_prompt="My name is Ritik. My assistant is Jessy. Friends names include Suraj, Anuj, Chaudhary, Yash, Pankaj. We speak clear Indian English.",
    )
    os.unlink(tmp_path)

    text = result["text"].strip()
    print(f"👤 You: {text}")
    return text

# ── Single conversation turn ───────────────────────────────────────────────────
def handle_one_turn():
    """Full pipeline: record → transcribe → GPT → speak."""
    user_text = record_until_silence()

    if not user_text or len(user_text) < 2:
        speak("I didn't catch that. Could you say it again?")
        return

    # Exit commands
    exit_words = ["goodbye", "bye", "shut down", "stop listening", "exit"]
    if any(word in user_text.lower() for word in exit_words):
        speak(f"Goodbye {YOUR_NAME}. Talk to you later!")
        raise SystemExit

    reply = ask_gpt(user_text)
    speak(reply)

# ── Mode 1: Press ENTER to talk (easiest, start here) ────────────────────────
def run_press_enter_mode():
    print(f"\n{'='*52}")
    print(f"  ✅ {ASSISTANT_NAME} is ONLINE  —  press-Enter mode")
    print(f"  Press ENTER to speak  |  Ctrl+C to quit")
    print(f"{'='*52}\n")

    speak(f"Hello {YOUR_NAME}! I am online and ready. Press Enter whenever you want to talk to me.")

    try:
        while True:
            input("⏎  Press ENTER to speak...")
            handle_one_turn()
    except (KeyboardInterrupt, SystemExit):
        speak("Goodbye!")
        print("\n👋 Shut down cleanly.")

# ── Mode 2: Always-on wake word (say "Hey Google" or "Porcupine") ─────────────
def run_wake_word_mode():
    from openwakeword.model import Model
    import numpy as np

    print(f"\n{'='*52}")
    print(f"  ✅ {ASSISTANT_NAME} is ONLINE  —  wake-word mode")
    print(f"  Say 'Hey Jarvis' to activate")
    print(f"  Ctrl+C to quit")
    print(f"{'='*52}\n")

    # Load the hey jarvis wake word model
    oww_model = Model(
        wakeword_models=["hey_jarvis_v0.1"],
        inference_framework="onnx"
    )

    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=16000,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=1280,
    )

    print("👂 Listening for 'Hey Jarvis'...")

    try:
        while True:
            # Read audio chunk
            raw = stream.read(1280, exception_on_overflow=False)

            # Convert to numpy array for openwakeword
            audio_data = np.frombuffer(raw, dtype=np.int16)

            # Check for wake word
            prediction = oww_model.predict(audio_data)

            # If confidence is above threshold → activate
            for model_name, score in prediction.items():
                if score > 0.3:
                    print(f"\n🔔 Wake word detected! (score: {score:.2f})")
                    # Clear the buffer
                    oww_model.reset()
                    speak("Yes?")
                    handle_one_turn()
                    print("\n👂 Listening for 'Hey Jarvis'...")

    except (KeyboardInterrupt, SystemExit):
        speak("Goodbye!")
        print("\n👋 Shut down cleanly.")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "enter"

    if mode == "wake":
        run_wake_word_mode()
    else:
        run_press_enter_mode()
