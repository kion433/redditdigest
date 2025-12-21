from instagrapi import Client
import json
import os

SESSION_FILE = "session.json"

def create_session_via_cookie():
    print("--- Instagram Session Setup (Cookie Method) ---")
    print("This method is safer than password login and avoids 2FA challenges.")
    print("\nStep 1: Open Instagram.com in your browser (Chrome/Edge).")
    print("Step 2: Log in to your account.")
    print("Step 3: Press F12 -> Go to 'Application' (or Storage) tab -> Cookies.")
    print("Step 4: Find the cookie named 'sessionid' and copy its Value.")
    
    session_id = input("\nPaste your 'sessionid' here: ").strip()
    
    if not session_id:
        print("Error: Empty session ID.")
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
        print("Verifying session...")
        # Login by sessionid
        cl.login_by_sessionid(session_id)
        
        # Check if it worked by getting self info
        info = cl.account_info()
        print(f"Success! Logged in as: {info.username}")
        
        # Save to disk
        cl.dump_settings(SESSION_FILE)
        print(f"Session saved to '{SESSION_FILE}'.")
        print("You can now run 'python upload_scheduler.py'")
        
    except Exception as e:
        print(f"Error: {e}")
        print("The session ID might be expired or invalid. Try logging out and back in on the browser.")

if __name__ == "__main__":
    create_session_via_cookie()
