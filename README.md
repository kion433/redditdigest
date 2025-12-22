# 🤖 Reddit Video Bot (AI Automation)

> **Automated short-form video generator that turns Reddit stories into viral TikTok/Reels/Shorts.**
> *Powered by DeepSeek V3, EdgeTTS, and MoviePy.*

## 🚀 Features

### 1. 🎭 "The Heckler" (Two-Voice Mode)
- **Concept**: A serious narrator (`en-US-GuyNeural`) tells the story, while a rude/hype-man "Heckler" (`en-US-ChristopherNeural` or random male voice) interrupts every 15s.
- **Implementation**:
    - **LLM Prompting**: Generates a JSON list of dialogue segments: `[{"role": "narrator", "text": "..."}, {"role": "heckler", "text": "NO WAY!"}]`.
    - **Audio Stitching**: `content_generator.py` generates individual audio clips for each segment and seamlessly stitches them into a single track with unified timestamps.

### 2. 🐸 Contextual Meme Engine
- **Concept**: Instead of generic stock photos, the bot searches for **Dank Memes** related to the specific story context.
- **Workflow**:
    - **Visual Keyword Extraction**: LLM analyzes the story and suggests 3-5 specific terms (e.g., "Cheating boyfriend meme", "Spiderman pointing meme").
    - **Smart Search**: Uses these keywords to fetch relevant memes via `bing-image-downloader`.
    - **Timing**: Memes hold for **4.0 seconds** to allow viewers to read/register the joke.

### 3. 🎵 Smart Background Music
- **Mood Detection**: Analyzes the story sentiment (e.g., "Sadness", "Joy").
- **Dynamic Selection**: Fetches royalty-free music matching that mood.
- **Random Start & Loop**: Starts the track at a random point and loops it, ensuring every video sounds different.

### 4. 🤖 Autonomous "Forever" Mode
- **Aggressive Scraping**: Retries Reddit fetching with different sort strategies (Top/Hot/Contro) until content is found.
- **Robustness**: Handles 403 Forbidden errors, missing images, and TTS failures gracefully with fallbacks.
- **Metadata**: Saves a `.json` sidecar for every video for future scheduling integration.

### 6. 🌗 Two Video Modes
- **Classic Mode**: Standard full-screen gameplay background.
- **Brainrot Mode**: Split-screen layout.
    - **Top**: Satisfying videos (Slime, Sand, Soap Cutting).
    - **Bottom**: Gameplay footage.
    - **Why**: Maximizes visual retention.

---

## 🛠️ Installation

### 1. Prerequisites
*   Python 3.9+
*   [FFmpeg](https://ffmpeg.org/download.html) (Ensure it's in your system PATH).
*   [ImageMagick](https://imagemagick.org/) (Required for MoviePy TextClips, legacy versions may be needed on Windows).

### 2. Setup
```bash
# Clone repository
git clone https://github.com/your-repo/reddit-video-bot.git
cd reddit-video-bot

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
1.  Create a `.env` file in the root directory:
    ```env
    DEEPSEEK_API_KEY=your_key_here
    # or OPENAI_API_KEY=your_key_here
    
    # Optional: Instagram Credentials (if enabling auto-upload)
    # IG_USERNAME=...
    # IG_PASSWORD=...
    ```
2.  Review `config.py` to adjust settings (Fonts, paths, subreddit limits).
3.  Place background video files (mp4/mov) in `assets/backgrounds/`.

---

## 🎬 Usage

### Run Batch Generation
Generate 100 videos automatically (Autopilot):
```bash
# Default (Classic Mode - Full gameplay)
python main.py --count 100

# Brainrot Mode (Split Screen)
python main.py --count 100 --mode brainrot
```

### Start Scheduler (Drip-Feed Upload)
Open a new terminal and run:
```bash
python upload_scheduler.py
```
*   **What it does**: Watches `output/finished_videos`.
*   **Rate**: Uploads 1 video every 15 minutes (randomized).
*   **Safety**: Uses session caching and human-like delays.
*   **Done**: Moves uploaded videos to `output/uploaded/`.

### How It Works
1.  **Fetcher**: Aggressively retries subreddits until "Juicy" content is found.
2.  **Writer**: LLM rewrites it into a 30-60s script.
3.  **Speak**: EdgeTTS generates audio + JSON timing metadata.
4.  **Edit**: MoviePy merges audio with random background footage.
5.  **Render**: Subtitles are burned in with "Perfect Sync".
6.  **Metadata**: Saves a `.json` sidecar with Caption & Tags.
7.  **Upload**: Scheduler picks up the pair and posts it.

---

### ⚠️ First Run: Authentication
Since this is a bot, you need to generate a saved session first.

**Option A: Standard Login (Try this first)**
```bash
python setup_login.py
```
Follow the prompts. If it fails with "Suspicious Login", try Option B.

**Option B: Browser Cookie Clone (Bypass)**
1.  Log in to Instagram on your PC Browser (Chrome/Edge).
2.  Run the cookie setup script:
    ```bash
    python setup_session_via_cookie.py
    ```
3.  Paste your `sessionid` cookie when asked (F12 > Application > Cookies).
4.  Once verified, run the scheduler:
    ```bash
    python upload_scheduler.py
    ```

## 📂 Project Structure
```
├── main.py                 # Entry point (Orchestrator)
├── config.py               # Global settings & API keys
├── assets/
│   ├── backgrounds/        # Place gameplay footage here
│   └── fonts/              # Custom fonts (Komika Axis)
├── modules/
│   ├── content_generator.py # LLM & TTS logic (Hybrid Sync)
│   ├── reddit_client.py     # Scraper
│   ├── subtitle_renderer.py # "Poppy" animation engine
│   ├── video_engine.py      # MoviePy editing logic
│   └── subreddits.py        # Database of 100+ subreddits
└── output/
    └── finished_videos/    # Final MP4s appear here
```

---

## 🛡️ Troubleshooting

## Missing Subtitles?
- This project now includes a self-healing fallback. If `edge-tts` fails to return `WordBoundary` events (a common API glitch), the code automatically switches to character-based estimation.
- Check `output/temp_audio_1.json` - if it has data, the system is working.

## "Download Error" for Images?
- The new `image_downloader.py` is much more aggressive. It will try:
  1. High-quality curated terms.
  2. Your exact keyword.
  3. A "meme" version of your keyword.
  4. DuckDuckGo Search.
- Only if ALL of these fail will you see a placeholder.

## "FFMPEG Handle Invalid" Error?
- This is a known Windows-specific warning from `moviepy`. It is harmless logic during cleanup. If you see "Moviepy - Done", your video is fine.
s might be skipping posts. Just run the batch again; it will pick a different subreddit.

---

# redditdigest