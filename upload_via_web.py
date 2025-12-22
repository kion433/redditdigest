import os
import time
import json
import random
from config import OUTPUT_VIDEO_PATH
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

# Persistence: Matches user's "newidea" folder structure
CHROME_PROFILE_PATH = os.path.join(os.getcwd(), "selenium_profile")

def human_delay(min_seconds=5.0, max_seconds=8.0):
    """Simulates human thinking time between actions."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def human_type_slowly(element, text):
    """Types text character by character with jitter."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2)) 

def safe_click(driver, element):
    """Hovers first (human-like), then attempts normal click, falls back to JS click."""
    try:
        # Move mouse to element first
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        human_delay(1.0, 2.0) # Brief pause after moving mouse
        element.click()
    except:
        driver.execute_script("arguments[0].click();", element)

def get_next_video():
    """Finds the first .mp4 that has a matching .json metadata file."""
    search_path = os.path.join(OUTPUT_VIDEO_PATH, "finished_videos")
    files = sorted([f for f in os.listdir(search_path) if f.endswith(".mp4")])
    
    for vid_file in files:
        base_name = os.path.splitext(vid_file)[0]
        meta_file = base_name + ".json"
        
        vid_path = os.path.join(search_path, vid_file)
        meta_path = os.path.join(search_path, meta_file)
        
        if os.path.exists(meta_path):
            return vid_path, meta_path
            
    return None, None

def init_driver():
    """Starts Chrome with a persistent user profile."""
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}")
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    # Make automation harder to detect
    options.add_argument("--disable-blink-features=AutomationControlled") 
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver
    except WebDriverException as e:
        print("\n!!! CHROME FAILED TO START !!!")
        print(f"Error: {e}")
        print("\nPOSSIBLE FIX: You probably have an old Chrome window open from the last run.")
        print("Please CLOSE all Chrome windows (especially those controlled by automation) and try again.")
        raise SystemExit

def upload_video(driver, video_path, caption):
    print("Navigating to Instagram...")
    driver.get("https://www.instagram.com/")
    human_delay(6, 10) # Initial load wait

    # Check if logged in
    try:
        create_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[text()='Create'] | //*[name()='svg' and @aria-label='New post']"))
        )
        print("Logged in. Clicking Create...")
        safe_click(driver, create_btn)
    except:
        print("\n!!! NOT LOGGED IN !!!")
        print("Please log in manually in the opened window.")
        input("Press ENTER after logging in...")
        create_btn = driver.find_element(By.XPATH, "//span[text()='Create'] | //*[name()='svg' and @aria-label='New post']")
        safe_click(driver, create_btn)
    
    human_delay()
    
    print("Selecting 'Post'...")
    try:
        post_menu_item = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Post'] | //div[text()='Post']"))
        )
        safe_click(driver, post_menu_item)
        print("Clicked 'Post' from menu.")
    except:
        pass 

    print("Uploading file...")
    file_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )
    file_input.send_keys(os.path.abspath(video_path))
    
    print("Waiting for upload preview...")
    # Wait for Crop Header or Next button
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//div[text()='Crop'] | //div[@aria-label='Crop'] | //button[text()='Next'] | //div[text()='Next']"))
    )
    human_delay() # Explicit "easy like 5 second gap"
    
    # --- HANDLING ASPECT RATIO (Fix 1:1 Crop) ---
    print("Setting Aspect Ratio to Original...")
    try:
        # 1. Click the "Expand/Ratio" icon (bottom left)
        # Strategy: Find button with 'Select crop' aria-label or child SVG
        ratio_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, 
                "//button[@aria-label='Select crop'] | " 
                "//button[descendant::*[name()='svg' and @aria-label='Select crop']] | " 
                "//div[@role='dialog']//button[.//svg] | " 
                "//button[.//svg[@aria-label='Select Crop']]"
            ))
        )
        safe_click(driver, ratio_btn)
        human_delay(2, 4)
        
        # 2. Select "Original" from the menu
        original_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, 
                "//span[text()='Original'] | "
                "//div[text()='Original'] | "
                "//button[.//span[text()='Original']]"
            ))
        )
        safe_click(driver, original_btn)
        print("Selected 'Original' aspect ratio.")
        human_delay(2, 4)
    except Exception as e:
        print(f"Warning: Could not set aspect ratio (might be already correct): {e}")

    # 1. Crop Step -> Next
    try:
        next_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[text()='Next'] | //button[text()='Next']"))
        )
        safe_click(driver, next_btn)
        print("Clicked Next (Crop).")
        human_delay()
    except:
        print("Could not find/click first Next button.")
        
    # 2. Edit Step -> Next
    try:
        next_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[text()='Next'] | //button[text()='Next']"))
        )
        safe_click(driver, next_btn)
        print("Clicked Next (Edit).")
        human_delay()
    except:
        print("Could not find/click second Next button.")
        
    print("Adding caption...")
    try:
        caption_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Write a caption...']"))
        )
        safe_click(driver, caption_area)
        human_delay(1, 2)
        human_type_slowly(caption_area, caption)
        human_delay()
    except:
        print("Could not find caption area.")
    
    print("Sharing...")
    try:
        share_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[text()='Share'] | //button[text()='Share']"))
        )
        safe_click(driver, share_btn)
    except:
        print("Could not find Share button.")
    
    print("Waiting for completion...")
    
    # CRITICAL: Strict wait for SUCCESS message first.
    try:
        # Wait up to 3 mins for "Post shared"
        WebDriverWait(driver, 180).until(
            EC.presence_of_element_located((By.XPATH, 
                "//div[text()='Post shared'] | "
                "//span[text()='Post shared'] | "
                "//img[@alt='Animated checkmark'] | "
                "//h2[text()='Post shared']"
            ))
        )
        print("Upload confirmed (Success message detected).")
        human_delay() # Wait a bit before closing
        
        # NOW looking for Close button
        try:
            close_btn = driver.find_element(By.XPATH, "//*[name()='svg' and @aria-label='Close']/parent::div | //*[name()='svg' and @aria-label='Close']/parent::button")
            safe_click(driver, close_btn)
        except:
            print("Close button not found, potentially redirected.")

    except:
        # If we timed out waiting for success, check if we failed OR if we just missed the message but are on Home
        try:
            # Check for failure
            error_msg = driver.find_element(By.XPATH, "//div[text()='Post could not be shared'] | //div[text()='Something went wrong'] | //span[text()='Post could not be shared']")
            print(f"UPLOAD FAILED: Instagram said '{error_msg.text}'")
            human_delay(2, 3)
            driver.get("https://www.instagram.com") 
            return 
        except:
            pass
            
        # Check if we are back on Home screen (Create button visible)
        try:
             WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Create'] | //*[name()='svg' and @aria-label='New post']"))
             )
             print("Upload likely successful (Returned to Home).")
        except:
             print("Timed out waiting for confirmation (Unknown status).")

    # Safety Latch (Discard Dialog) - in case we are stuck
    try:
        discard_dialog = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//div[text()='Discard post?'] | //h3[text()='Discard post?']"))
        )
        print("Detected 'Discard post?' dialog. Clicking Cancel (to stay)...")
        cancel_btn = driver.find_element(By.XPATH, "//button[text()='Cancel']")
        safe_click(driver, cancel_btn)
    except:
        pass

def main():
    driver = init_driver()
    try:
        while True:
            vid_path, meta_path = get_next_video()
            
            if not vid_path:
                print("No videos found. Waiting...")
                time.sleep(60)
                continue
            
            print(f"Processing: {vid_path}")
            with open(meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            caption = data.get("caption", "New Reel! #viral")
            
            upload_video(driver, vid_path, caption)
            
            # Post-upload cleanup
            uploaded_dir = os.path.join(OUTPUT_VIDEO_PATH, "uploaded")
            os.makedirs(uploaded_dir, exist_ok=True)
            try:
                os.rename(vid_path, os.path.join(uploaded_dir, os.path.basename(vid_path)))
                os.rename(meta_path, os.path.join(uploaded_dir, os.path.basename(meta_path)))
            except Exception as e:
                print(f"File move failed (file in use?): {e}")
            
            print("Video moved to 'uploaded'. Sleeping for 10 mins...")
            time.sleep(600) # 10 mins
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
