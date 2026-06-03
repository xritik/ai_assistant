# ─────────────────────────────────────────────
#  config.py  —  All settings in one place
#  Fill in YOUR values before running main.py
# ─────────────────────────────────────────────

# ── Your name (assistant will address you by this) ────────────────────────────
YOUR_NAME = "Ritik"               # ← change to your name

# ── Assistant name (what you want to call it) ─────────────────────────────────
ASSISTANT_NAME = "Jarvis"         # ← call it whatever you like

# ── OpenAI API key ────────────────────────────────────────────────────────────
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY = "sk-..."         # ← paste your key here

# ── Porcupine wake-word key (FREE tier is fine) ───────────────────────────────
# Get from: https://console.picovoice.ai/  → sign up → copy Access Key
# If you leave this blank, the assistant runs in press-ENTER mode (still works)
PORCUPINE_ACCESS_KEY = ""         # ← paste key, or leave "" for Enter mode

# ── Piper TTS paths ───────────────────────────────────────────────────────────
# After running setup.sh these paths will be correct automatically.
# Only change if you installed Piper somewhere else.

import platform, pathlib

if platform.system() == "Windows":
    PIPER_EXECUTABLE = r"C:\piper\piper.exe"          # ← adjust if needed
else:
    PIPER_EXECUTABLE = "/usr/local/bin/piper"          # set by setup.sh

# Voice model — download via setup.sh
# Other voices: https://huggingface.co/rhasspy/piper-voices/tree/main
PIPER_MODEL_PATH = str(
    pathlib.Path(__file__).parent / "voices" / "en_US-ryan-high.onnx"
)

# ── Memory file (stores conversation history) ─────────────────────────────────
MEMORY_FILE = str(pathlib.Path(__file__).parent / "memory.json")

# ── Whisper model size ────────────────────────────────────────────────────────
# tiny  → fastest, least accurate  (good for testing)
# base  → good balance             (recommended)
# small → more accurate, slower
# Set in main.py line:  whisper.load_model("base")
