import os
from dotenv import load_dotenv
from modules.subreddits import SUBREDDIT_LIST

load_dotenv()

# Reddit
REDDIT_SUBREDDITS = SUBREDDIT_LIST
REDDIT_TIMEFRAME = "day" # day, week, month, year, all

# OpenAI / DeepSeek
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Logic to switch between providers
if DEEPSEEK_API_KEY:
    OPENAI_API_KEY = DEEPSEEK_API_KEY
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "deepseek-chat")
else:
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "gpt-4o")

# Instagram (Unofficial)
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

# Video
BACKGROUND_VIDEO_PATH = "assets/backgrounds"
OUTPUT_VIDEO_PATH = "output"
FONT_PATH = "assets/fonts/KomikaAxis.ttf" # Custom user font

# TTS Voices (EdgeTTS)
TTS_VOICES = [
    "en-US-AriaNeural",       # Female (US)
    "en-US-GuyNeural",        # Male (US)
    "en-US-JennyNeural",      # Female (US)
    "en-US-ChristopherNeural",# Male (US)
    "en-GB-SoniaNeural",      # Female (UK)
    "en-GB-RyanNeural",       # Male (UK)
]


# Add FFmpeg to PATH for current session
ffmpeg_path = r"C:\Users\HP\AppData\Local\Microsoft\WinGet\Links"
os.environ["PATH"] += os.pathsep + ffmpeg_path

# --- Persistent Device Identity ---
import uuid
import json

DEVICE_CONFIG_FILE = "device_config.json"

def get_device_settings():
    """
    Returns a unified device configuration (S23 Ultra) with persistent UUIDs.
    If UUIDs don't exist in device_config.json, they are generated and saved.
    This ensures Instagram sees the 'same phone' every time.
    """
    # 1. Base S23 Ultra Template
    device_settings = {
        "app_version": "269.0.0.18.75",
        "android_version": 29,
        "android_release": "10.0",
        "dpi": "450dpi",
        "resolution": "1080x2340",
        "manufacturer": "Samsung",
        "device": "SM-S918B",
        "model": "Galaxy S23 Ultra",
        "cpu": "samsungexynos",
        "version_code": "314596395"
    }

    # 2. Check for existing UUIDs
    if os.path.exists(DEVICE_CONFIG_FILE):
        try:
            with open(DEVICE_CONFIG_FILE, 'r') as f:
                saved_uuids = json.load(f)
                device_settings.update(saved_uuids)
                return device_settings
        except Exception as e:
            print(f"Warning: Could not load device config ({e}). Generating new one.")

    # 3. Generate New UUIDs (First run only)
    new_uuids = {
        "phone_id": str(uuid.uuid4()),
        "uuid": str(uuid.uuid4()),
        "client_session_id": str(uuid.uuid4()),
        "advertising_id": str(uuid.uuid4()),
        "device_id": f"android-{uuid.uuid4().hex[:16]}"
    }

    # 4. Save for future runs
    with open(DEVICE_CONFIG_FILE, 'w') as f:
        json.dump(new_uuids, f, indent=4)
    
    device_settings.update(new_uuids)
    return device_settings
