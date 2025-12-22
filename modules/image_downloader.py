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
    # 1. Check if query is a Mood and map to curated term
    search_term = query
    if query in EMOTION_QUERIES:
        search_term = random.choice(EMOTION_QUERIES[query])
        print(f"Mapped Mood '{query}' -> Curated Query: '{search_term}'")
    else:
        # Fallback for old keywords or unmapped moods
        print(f"Using direct query: {query}")

    print(f"Searching for image: {search_term}")
    try:
        from bing_image_downloader import downloader
        import shutil
        import glob
        
        # Bing downloader creates its own subfolder structure
        download_folder = os.path.join(output_dir, "bing_temp")
        
        downloader.download(
            search_term, 
            limit=5, 
            output_dir=download_folder, 
            adult_filter_off=True, 
            force_replace=False, 
            timeout=10, 
            verbose=False
        )
        
        # 2. Find downloaded images
        # The library creates a subfolder named after the query
        query_folder = os.path.join(download_folder, search_term)
        if not os.path.exists(query_folder):
            # Sometimes it sanitizes the folder name, try globbing
            subfolders = glob.glob(os.path.join(download_folder, "*"))
            if subfolders:
                query_folder = subfolders[0]
            else:
                 print("Bing Downloader: No folder created.")
                 return generate_placeholder(query, output_dir, filename_prefix)
        
        # Get all images
        extensions = ['*.jpg', '*.jpeg', '*.png']
        images = []
        for ext in extensions:
            images.extend(glob.glob(os.path.join(query_folder, ext)))
            
        if not images:
             print("Bing Downloader: No images found in folder.")
             return generate_placeholder(query, output_dir, filename_prefix)
             
        # 3. Pick random image
        chosen_image = random.choice(images)
        
        # 4. Move/Rename to our target output location
        final_filename = f"{filename_prefix}_{random.randint(1000,9999)}.jpg"
        final_path = os.path.join(output_dir, final_filename)
        
        shutil.move(chosen_image, final_path)
        print(f"Downloaded & Moved: {final_path}")
        
        # 5. Cleanup temp folder
        try:
            shutil.rmtree(download_folder)
        except:
            pass # Non-critical
            
        return final_path

    except Exception as e:
        print(f"Image search error: {e}")
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
