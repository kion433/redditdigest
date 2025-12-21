from instagrapi import Client
from config import *
import os

class InstagramClient:
    def __init__(self):
        self.client = Client()
        # Create a session file to store cookies (avoids re-login flags)
        self.session_file = "ig_session.json"

    def login(self):
        if not IG_USERNAME or not IG_PASSWORD:
            print("Error: IG_USERNAME or IG_PASSWORD not set in .env")
            return False

        try:
            if os.path.exists(self.session_file):
                print("Loading session from disk...")
                self.client.load_settings(self.session_file)
                # Verify session
                try:
                    self.client.get_timeline_feed()
                    print("Session valid.")
                    return True
                except Exception:
                    print("Session expired, re-logging in...")
            
            print(f"Logging in as {IG_USERNAME}...")
            self.client.login(IG_USERNAME, IG_PASSWORD)
            self.client.dump_settings(self.session_file)
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def upload_video(self, video_path, caption):
        """
        Uploads a video to Instagram Feed/Reels.
        """
        try:
            print(f"Uploading {video_path}...")
            # clip_upload uploads to Reels by default if aspect ratio is vertical
            media = self.client.clip_upload(
                path=video_path,
                caption=caption
            )
            print(f"Successfully uploaded: {media.pk}")
            return media.pk
        except Exception as e:
            print(f"Upload failed: {e}")
            return None
