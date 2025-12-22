import os
import requests
import random
from duckduckgo_search import DDGS

# Curated Library of High-Quality Cinematic Search Terms
# Curated Library of Meme/Reaction Search Terms (Dopamine Focused)
EMOTION_QUERIES = {
    "Shock": [
        "shocked face meme funny",
        "surprised pikachu meme high quality",
        "jaw drop meme reaction",
        "shookt meme funny"
    ],
    "Anger": [
        "angry rage meme funny",
        "pissed off meme reaction",
        "arthur fist meme high quality",
        "angry bird meme funny"
    ],
    "Fear": [
        "scared meme funny",
        "nervous sweating meme reaction",
        "panik meme high quality",
        "fear reaction meme funny"
    ],
    "Sadness": [
        "crying cat meme funny",
        "sad pablo escobar meme high quality",
        "trying not to cry meme reaction",
        "pain meme funny"
    ],
    "Joy": [
        "celebration meme funny",
        "happiness noise meme reaction",
        "dancing cat meme gif",
        "success kid meme high quality"
    ],
    "Disgust": [
        "disgusted tanjiro meme",
        "eww meme funny reaction",
        "absolutely disgusting meme",
        "side eye meme funny"
    ],
    "Confused": [
        "confused math lady meme high quality",
        "confused nick young meme",
        "visible confusion meme reaction",
        "what meme funny"
    ],
    "Neutral": [
        "staring blankly meme",
        "awkward silence meme funny",
        "waiting meme skeleton",
        "ok meme reaction"
    ]
}

def download_image(query, output_dir, filename_prefix="img"):
    # 1. Prepare Search Strategies
    strategies = []
    
    # Strategy 1: Curated Mood Query (if applicable)
    if query in EMOTION_QUERIES:
        strategies.append(random.choice(EMOTION_QUERIES[query]))
    
    # Strategy 2: Direct query
    strategies.append(query)
    
    # Strategy 3: Modified Query (Meme-focused)
    if query not in EMOTION_QUERIES:
        strategies.append(f"{query} funny meme")
    else:
        strategies.append(f"{query} reaction meme")

    print(f"Starting persistent search for: '{query}' (Strategies: {len(strategies)})")
    
    for i, search_term in enumerate(strategies):
        print(f"  Attempt {i+1}/{len(strategies)}: Searching for '{search_term}'...")
        
        try:
            from bing_image_downloader import downloader
            import shutil
            import glob
            
            download_folder = os.path.join(output_dir, "bing_temp")
            if os.path.exists(download_folder):
                shutil.rmtree(download_folder)
            
            downloader.download(
                search_term, 
                limit=5, # Increased limit for better hit rate
                output_dir=download_folder, 
                adult_filter_off=True, 
                force_replace=False, 
                timeout=10, # Increased timeout
                verbose=False
            )
            
            # Find downloaded images
            query_folder = os.path.join(download_folder, search_term)
            if not os.path.exists(query_folder):
                subfolders = glob.glob(os.path.join(download_folder, "*"))
                if subfolders:
                    query_folder = subfolders[0]
            
            if os.path.exists(query_folder):
                extensions = ['*.jpg', '*.jpeg', '*.png']
                images = []
                for ext in extensions:
                    images.extend(glob.glob(os.path.join(query_folder, ext)))
                    
                if images:
                    chosen_image = random.choice(images)
                    final_filename = f"{filename_prefix}_{random.randint(1000,9999)}.jpg"
                    final_path = os.path.join(output_dir, final_filename)
                    shutil.move(chosen_image, final_path)
                    print(f"  Success on attempt {i+1}: {final_path}")
                    
                    # Cleanup
                    try: shutil.rmtree(download_folder)
                    except: pass
                    return final_path
            
            print(f"  Attempt {i+1} failed to yield images.")

        except Exception as e:
            print(f"  Attempt {i+1} error: {e}")
            
    # 2. Final Fallback: DuckDuckGo Search
    print("Bing failed all attempts. Trying DuckDuckGo...")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=5))
            if results:
                url = results[0]['image']
                final_filename = f"{filename_prefix}_ddg_{random.randint(1000,9999)}.jpg"
                final_path = os.path.join(output_dir, final_filename)
                
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    with open(final_path, 'wb') as f:
                        f.write(resp.content)
                    print(f"  DuckDuckGo Success: {final_path}")
                    return final_path
    except Exception as e:
        print(f"  DuckDuckGo error: {e}")

    # 3. Total Disaster Fallback
    print("All search methods failed. Using placeholder as absolute last resort.")
    return generate_placeholder(query, output_dir, filename_prefix)

def generate_placeholder(text, output_dir, prefix):
    """Generates a reliable placeholder image if search fails."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import random
        
        # Random pastel color
        color = (random.randint(100,200), random.randint(100,200), random.randint(100,200))
        img = Image.new('RGB', (1280, 720), color)
        d = ImageDraw.Draw(img)
        
        # Draw text
        try:
            # Try to load the project font, else default
            font = ImageFont.truetype("assets/fonts/KomikaAxis.ttf", 80)
        except:
            font = ImageFont.load_default()
            
        # Draw centered text (simple approx)
        d.text((640, 360), f"IMG: {text}", fill=(255,255,255), anchor="mm", font=font)
        
        filename = f"{prefix}_placeholder_{random.randint(1000,9999)}.jpg"
        path = os.path.join(output_dir, filename)
        img.save(path)
        print(f"Generated Placeholder: {path}")
        return path
    except Exception as e:
        print(f"Placeholder generation failed: {e}")
        return None

if __name__ == "__main__":
    os.makedirs("test_images", exist_ok=True)
    download_image("scary ghost", "test_images")
