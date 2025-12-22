import os
import requests
import random
from duckduckgo_search import DDGS

def download_image(query, output_dir, filename_prefix="img"):
    print(f"Searching for image: {query}")
    try:
        with DDGS() as ddgs:
            # Get first 3 results and pick one random for variety
            results = list(ddgs.images(query, max_results=5))
            
            if not results:
                print("No results found.")
                return None
                
            # Pick a random one from top 5 (retention variety)
            img_data = random.choice(results)
            img_url = img_data['image']
            
            print(f"Downloading: {img_url}")
            path = os.path.join(output_dir, f"{filename_prefix}_{query.replace(' ', '_')}.jpg")
            
            response = requests.get(img_url, timeout=10)
            if response.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(response.content)
                return path
            else:
                print(f"Failed to download image: status {response.status_code}")
                return None

    except Exception as e:
        print(f"Image search error: {e}")
        return None

if __name__ == "__main__":
    os.makedirs("test_images", exist_ok=True)
    download_image("scary ghost", "test_images")
