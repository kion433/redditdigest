import os
from dotenv import load_dotenv

# Load from parent directory .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# --- API KEYS ---
# Text Generation (DeepSeek / OpenAI)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if DEEPSEEK_API_KEY:
    LLM_API_KEY = DEEPSEEK_API_KEY
    LLM_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    LLM_MODEL_NAME = os.getenv("AI_MODEL_NAME", "deepseek-chat")
else:
    LLM_API_KEY = OPENAI_API_KEY
    LLM_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL_NAME = os.getenv("AI_MODEL_NAME", "gpt-4o")

# Image Generation (Gemini)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- PATHS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.join(BASE_DIR, "youtube_longform")

ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")

# Ensure dirs exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)

# --- VIDEO SETTINGS ---
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
ZOOM_DURATION = 20 # Seconds per image
TRANSITION_DURATION = 1.0 # Seconds

# --- AUDIO SETTINGS ---
# --- AUDIO SETTINGS ---
TTS_PROVIDER = "EDGE" # "EDGE" (Free), "OPENAI" (Paid), "HF_INFERENCE" (Free/RateLimited)
TTS_VOICE = "en-US-ChristopherNeural" # Deep documentary voice (Free). 
# Alt: "en-US-EricNeural"

# --- IMAGE SETTINGS ---
IMAGE_PROVIDER = "POLLINATIONS" # "POLLINATIONS" (Free), "OPENAI" (Paid), "GEMINI" (Paid/Quota)

# ... existing config ... # Documentary style
