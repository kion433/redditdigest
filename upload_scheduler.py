import os
import json
import time
import random
import glob
import shutil
from pathlib import Path
from instagrapi import Client

# Configuration
INPUT_DIR = "output/finished_videos"
UPLOADED_DIR = "output/uploaded"
SESSION_FILE = "session.json"
DELAY_MINUTES = 15
JITTER_SECONDS = 300  # 0-5 minutes extra delay

def load_config():
    from dotenv import load_dotenv
    load_dotenv()
    return {
        "user": os.getenv("IG_USERNAME"),
        "pass": os.getenv("IG_PASSWORD")
    }

def get_next_video():
    # Look for pair of .mp4 and .json
    video_files = glob.glob(os.path.join(INPUT_DIR, "*.mp4"))
    for vid in video_files:
        base = os.path.splitext(vid)[0]
        meta = f"{base}.json"
        if os.path.exists(meta):
            return vid, meta
    return None, None

def login(cl, config):
    if not config["user"] or not config["pass"]:
        print("Warning: IG_USERNAME/PASSWORD not set. Running in MOCK/DRY-RUN mode.")
        return True # Mock success
        
    try:
        if os.path.exists(SESSION_FILE):
            print("Loading session...")
            cl.load_settings(SESSION_FILE)
            if cl.login(config["user"], config["pass"]):
                return True
        
        # Fresh login
        print("Logging in...")
        cl.login(config["user"], config["pass"])
        cl.dump_settings(SESSION_FILE)
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False

from instagrapi.exceptions import LoginRequired, VideoNotUpload

def upload_loop():
    print("--- Instagram Drip-Feed Scheduler ---")
    config = load_config()
    cl = Client()

    # Load persistent device identity (S23 + Fixed UUIDs)
    # This prevents the "randomly regenerating phone" issue
    from config import get_device_settings
    cl.set_device(get_device_settings())
    
    # Ensure dirs
    os.makedirs(UPLOADED_DIR, exist_ok=True)
    
    if not login(cl, config):
        return

    # WARM UP: Fetch timeline to look like a human and validate session
    try:
        print("Warming up session (fetching timeline)...")
        cl.get_timeline_feed()
        print("Session warm-up successful.")
    except Exception as e:
        print(f"Warm-up failed: {e}. Session might be restricted.")

    while True:
        vid_path, meta_path = get_next_video()
        
        if vid_path and meta_path:
            try:
                print(f"\nProcessing: {vid_path}")
                with open(meta_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                caption = data.get("caption", "New video! #viral")
                
                print("Uploading as Reel...")
                cl.clip_upload(vid_path, caption) # LIVE UPLOAD ENABLED (Reels)
                print("Upload successful!")
                
                # Move to uploaded
                shutil.move(vid_path, os.path.join(UPLOADED_DIR, os.path.basename(vid_path)))
                shutil.move(meta_path, os.path.join(UPLOADED_DIR, os.path.basename(meta_path)))
                
                print("Moved to 'uploaded/'.")
                
                # Wait
                sleep_time = (DELAY_MINUTES * 60) + random.randint(0, JITTER_SECONDS)
                print(f"Sleeping for {sleep_time/60:.1f} minutes...")
                time.sleep(sleep_time)
                
            except (LoginRequired, VideoNotUpload) as e:
                print(f"Session issue detected: {e}")
                
                # Delete bad session file to force fresh login next time
                if os.path.exists(SESSION_FILE):
                    os.remove(SESSION_FILE)
                
                print("Bad session deleted. Attempting relogin (Fresh)...")
                if login(cl, config):
                    print("Relogin successful. Retrying upload in 60s...")
                    time.sleep(60)
                    continue # Retry immediately
                else:
                    print("Relogin failed. Terminating.")
                    return

            except Exception as e:
                print(f"Upload error: {e}")
                time.sleep(60) # Wait 1 min on error
        else:
            print("Queue empty. Checking again in 1 minute...")
            time.sleep(60)

if __name__ == "__main__":
    upload_loop()
