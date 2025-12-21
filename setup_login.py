from instagrapi import Client
import os
from dotenv import load_dotenv

load_dotenv()

SESSION_FILE = "session.json"

def standard_login():
    print("--- Instagram Login (Standard) ---")
    
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    
    if not username or not password:
        print("Error: IG_USERNAME and IG_PASSWORD must be set in your .env file.")
        return

    cl = Client()

    # Emulate Samsung Galaxy S23 Ultra to match scheduler
    cl.set_device({
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
    })
    
    try:
        print(f"Attempting login for: {username}...")
        cl.login(username, password)
        
        print("Login Successful!")
        cl.dump_settings(SESSION_FILE)
        print(f"Session saved to '{SESSION_FILE}'.")
        
    except Exception as e:
        print(f"Login failed: {e}")
        print("Try using 'python setup_session_via_cookie.py' instead if you hit 2FA/Challenge loops.")

if __name__ == "__main__":
    standard_login()
