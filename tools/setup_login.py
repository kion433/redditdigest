from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired, ChallengeRequired
import os
from dotenv import load_dotenv
import json

SESSION_FILE = "session.json"

def setup_login():
    print("--- Instagram Interactive Login Setup ---")
    load_dotenv()
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    
    if not username or not password:
        print("Error: Credentials missing in .env")
        return

    cl = Client()
    
    try:
        print(f"Attempting login as {username}...")
        cl.login(username, password)
    except TwoFactorRequired:
        print("2FA Required!")
        code = input("Enter the 2FA code sent to your SMS/Email/App: ")
        cl.two_factor_login(code)
    except ChallengeRequired:
        print("Challenge Required! (Email/SMS verification needed)")
        # instagrapi often handles this flow automatically or throws specific errors
        # If it fails here, Manual intervention in App is usually required.
        print("Check your email/SMS now. If no code comes, verify your identity in the Instagram Mobile App.")
        code = input("Enter code if you received one: ")
        cl.challenge_code_handler(code)
    except Exception as e:
        print(f"Login failed: {e}")
        print("\nTROUBLESHOOTING:")
        print("1. Open Instagram App on your phone.")
        print("2. Go to Settings > Security > Login Activity.")
        print("3. If you see a login from this location, tap 'This Was Me'.")
        print("4. Wait 5 minutes and try running this script again.")
        return

    print("\nLOGIN SUCCESSFUL!")
    cl.dump_settings(SESSION_FILE)
    print(f"Session saved to {SESSION_FILE}")
    print("You can now run 'python upload_scheduler.py' without issues.")

if __name__ == "__main__":
    setup_login()
