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

# Add FFmpeg to PATH for current session
ffmpeg_path = r"C:\Users\HP\AppData\Local\Microsoft\WinGet\Links"
os.environ["PATH"] += os.pathsep + ffmpeg_path
