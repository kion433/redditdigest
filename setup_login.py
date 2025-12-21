from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired
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

    # Load persistent device identity (S23 + Fixed UUIDs)
    from config import get_device_settings
    cl.set_device(get_device_settings())
    
    try:
        print(f"Attempting login for: {username}...")
        cl.login(username, password)
    except TwoFactorRequired:
        print("\n!!! 2FA REQUIRED !!!")
        code = input("Enter the 2FA code sent to your SMS/App: ").strip()
        cl.two_factor_login(code)
    except Exception as e:
        print(f"Login failed: {e}")
        return

    print("Login Successful!")
    cl.dump_settings(SESSION_FILE)
    print(f"Session saved to '{SESSION_FILE}'.")

if __name__ == "__main__":
    standard_login()
