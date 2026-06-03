# 🤖 AI Personal Assistant — Phase 1

> Always-on voice assistant: Wake Word → Whisper STT → GPT-4o → Piper TTS

---

## What This Does

You speak → Whisper converts your voice to text → GPT-4o thinks → Piper speaks the reply.
It remembers your last 40 conversation turns across restarts (saved in `memory.json`).

---

## File Structure

```
ai_assistant/
├── main.py              ← Main program (run this)
├── config.py            ← YOUR settings go here (API keys, name, etc.)
├── requirements.txt     ← Python packages
├── setup.sh             ← One-time setup (Linux/Mac)
├── setup_windows.bat    ← One-time setup (Windows)
├── memory.json          ← Auto-created, stores conversation history
└── voices/
    ├── en_US-ryan-high.onnx       ← Downloaded by setup script
    └── en_US-ryan-high.onnx.json  ← Downloaded by setup script
```

---

## Quick Start

### Step 1 — Run Setup (once)

**Linux / Mac:**
```bash
bash setup.sh
```

**Windows (run as Administrator):**
```
setup_windows.bat
```

### Step 2 — Fill in config.py

Open `config.py` and set these three things:

```python
YOUR_NAME      = "Aryan"       # your name
ASSISTANT_NAME = "Jarvis"      # what to call the AI
OPENAI_API_KEY = "sk-..."      # your OpenAI key
```

### Step 3 — Run

```bash
# Easiest: press Enter to talk
python main.py

# Always-listening wake word mode (say "Hey Google" or "Porcupine")
python main.py wake
```

---

## The Two Modes Explained

### Press-Enter Mode (default)
- You press Enter, then speak, then it replies.
- **Start with this.** No extra setup needed.
- Good for: testing, getting used to it.

### Wake Word Mode
- The assistant listens 24/7 in the background.
- When it hears "Hey Google" or "Porcupine", it activates.
- Requires a free Porcupine key from https://console.picovoice.ai/
- Good for: actual daily use once everything works.

---

## How Each Part Works

### Whisper (Speech → Text)
- Runs 100% on your laptop. No internet needed.
- Model `base` downloads ~150MB on first run (cached after that).
- Records until you go silent for 2 seconds, then transcribes.

### GPT-4o (The Brain)
- Your OpenAI API key is used here.
- Gets your full conversation history + the current time.
- Responds in plain English (no markdown so it sounds natural when spoken).
- Uses `gpt-4o-mini` tip: swap model to `"gpt-4o-mini"` in main.py to cut costs by ~15x for simple tasks.

### Piper (Text → Voice)
- Runs 100% on your laptop. Free forever.
- Voice model: `en_US-ryan-high` (clear male voice, good quality).
- Other voices: https://huggingface.co/rhasspy/piper-voices/tree/main

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `PyAudio install fails` | Linux: `sudo apt install portaudio19-dev` then retry |
| `Piper not found` | Check `PIPER_EXECUTABLE` in config.py matches where piper is |
| `No audio from Piper` | Make sure the `.onnx` and `.onnx.json` files are both in `voices/` |
| `Whisper first run slow` | Normal — it downloads the model. Second run is fast. |
| `pvporcupine error` | Leave `PORCUPINE_ACCESS_KEY = ""` in config.py to use Enter mode instead |
| `OpenAI auth error` | Double-check your API key in config.py |

---

## Adjusting Sensitivity

In `main.py`, inside `record_until_silence()`:

```python
silence_threshold = 500   # increase if it cuts you off mid-sentence
                          # decrease if it waits too long after you stop
silence_duration  = 2.0   # seconds of quiet before it stops recording
```

---

## Memory

Conversation history is saved in `memory.json` automatically.
The last 40 turns are kept. Delete this file to reset the assistant's memory.

---

## What's Coming in Later Phases

- Phase 2: Camera + emotion detection (OpenCV + DeepFace)
- Phase 3: Task alarms + morning briefings
- Phase 4: Gmail read + reply
- Phase 5: WhatsApp integration
- Phase 6: React dashboard UI
