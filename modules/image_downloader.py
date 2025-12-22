import os
import requests
import random
from duckduckgo_search import DDGS

# Curated Library of High-Quality Cinematic Search Terms
EMOTION_QUERIES = {
    "Shock": [
        "cinematic close up portrait of shocked person dramatic lighting",
        "stunned face expression cinematic photography",
        "person gasping in surprise dramatic 4k",
        "shocked human eyes close up cinematic"
    ],
    "Anger": [
        "angry person shouting cinematic portrait",
        "furious face expression dramatic lighting dark",
        "rage emotion human face cinematic",
        "intense angry eyes close up photography"
    ],
    "Fear": [
        "scared person hiding dark cinematic",
        "terrified face expression horror lighting",
        "fearful human eyes close up dramatic",
        "person screaming in fear cinematic shot"
    ],
    "Sadness": [
        "sad person crying cinematic portrait",
        "depressed human sitting alone dark room",
        "tearful eyes close up emotional photography",
        "heartbroken person dramatic lighting"
    ],
    "Joy": [
        "person laughing uncontrollably cinematic",
        "tears of joy face expression dramatic",
        "ecstatic human emotion cinematic portrait",
        "happy person celebrating dramatic lighting"
    ],
    "Disgust": [
        "disgusted face expression cinematic",
        "person reacting with disgust dramatic lighting",
        "repulsed human emotion portrait"
    ],
    "Confused": [
        "confused person thinking cinematic",
        "puzzled face expression dramatic lighting",
        "disoriented human portrait cinematic"
    ],
    "Neutral": [
        "serious person portrait cinematic lighting",
        "neutral face expression dramatic photography",
        "calm human face close up cinematic"
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
