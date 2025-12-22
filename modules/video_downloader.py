import os
import random
import glob
from yt_dlp import YoutubeDL

def download_satisfying_videos(output_dir="assets/top_backgrounds", count=3):
    """
    Downloads satisfying 'Brainrot' videos for the top half of the screen.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if we already have enough videos
    existing = glob.glob(os.path.join(output_dir, "*.mp4"))
    if len(existing) >= count:
        print(f"Already have {len(existing)} satisfying videos. Skipping download.")
        return existing

    queries = [
        "satisfying slime asmr no talking vertical",
        "soap cutting asmr no talking vertical",
        "kinetic sand satisfying asmr vertical",
        "hydraulic press satisfying vertical",
        "oddly satisfying video vertical no music"
    ]
    
    # Shuffle queries to get variety
    random.shuffle(queries)
    
    ydl_opts = {
        # Force single file to avoid merging issues
        'format': 'best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, 'satisfying_%(id)s.%(ext)s'),
        'noplaylist': True,
        'quiet': False,
        'max_filesize': 50 * 1024 * 1024, # 50MB max
    }

    downloaded = []
    
    with YoutubeDL(ydl_opts) as ydl:
        for query in queries:
            if len(downloaded) + len(existing) >= count:
                break
                
            try:
                print(f"Searching for satisfying video: {query}")
                # Search for 1 result per query
                search_query = f"ytsearch1:{query}"
                info = ydl.extract_info(search_query, download=True)
                
                if 'entries' in info:
                    video_info = info['entries'][0]
                    filename = ydl.prepare_filename(video_info)
                    
                    # yt-dlp might change extension, so we find the actual file
                    base = os.path.splitext(filename)[0]
                    # Simple glob to find the produced file
                    files = glob.glob(f"{base}*")
                    if files:
                        print(f"Downloaded: {files[0]}")
                        downloaded.append(files[0])
                        
            except Exception as e:
                print(f"Error downloading {query}: {e}")
                continue

    return glob.glob(os.path.join(output_dir, "*.mp4"))

if __name__ == "__main__":
    download_satisfying_videos(count=3)
