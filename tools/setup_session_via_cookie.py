from instagrapi import Client
import json

SESSION_FILE = "session.json"

def setup_via_cookies():
    print("--- Instagram Cookie Login Setup ---")
    print("This method bypasses the password screen by cloning your browser session.")
    print("\nINSTRUCTIONS:")
    print("1. Open Instagram.com in your browser and Log In.")
    print("2. Open Developer Tools (F12) -> Application Tab -> Cookies.")
    print("3. Find the cookie named 'sessionid'.")
    print("4. Copy its Value.")
    
    sessionid = input("\nPaste your 'sessionid' here: ").strip()
    
    if not sessionid:
        print("Error: No sessionid entered.")
        return

    cl = Client()
    
    try:
        print("Validating session...")
        # Login using the sessionid cookie
        cl.login_by_sessionid(sessionid)
        
        # Verify it works by getting self info
        info = cl.account_info()
        print(f"\nSUCCESS! Logged in as: {info.username}")
        
        # Dump to session.json (this saves the full session for the scheduler)
        cl.dump_settings(SESSION_FILE)
        print(f"Session saved to {SESSION_FILE}")
        print("You can now run 'python upload_scheduler.py'!")
        
    except Exception as e:
        print(f"\nLogin Failed: {e}")
        print("Make sure you copied the full value and your browser session is still active.")

if __name__ == "__main__":
    setup_via_cookies()
