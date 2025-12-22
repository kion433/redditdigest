import os
import yt_dlp
import glob

# Curated "No Copyright" Search Queries for each mood
MOOD_SEARCH_TERMS = {
    "Shock": "suspenseful thriller no copyright music horror tension",
    "Anger": "aggressive phonk no copyright music intense",
    "Fear": "creepy dark ambient no copyright music horror",
    "Sadness": "sad emotional piano no copyright music cinematic",
    "Joy": "upbeat happy vlog no copyright music pop",
    "Disgust": "unsettling weird experimental no copyright music",
    "Confused": "mystery investigation no copyright music subtle",
    "Neutral": "lofi hip hop no copyright music chill"
}

def get_music_for_mood(mood, output_dir="assets/music"):
    """
    Returns the path to a music file for the given mood.
    Downloads it if it doesn't exist.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 1. Check if file exists
    expected_filename = f"{mood}.mp3"
    expected_path = os.path.join(output_dir, expected_filename)
    
    if os.path.exists(expected_path):
        print(f"Music found for {mood}: {expected_path}")
        return expected_path
    
    # 2. Download if missing
    print(f"Music missing for {mood}. Downloading...")
    return download_music(mood, output_dir)

def download_music(mood, output_dir):
    search_query = MOOD_SEARCH_TERMS.get(mood, MOOD_SEARCH_TERMS["Neutral"])
    # Add "short" or duration filter logic in search string if possible, 
    # but yt-dlp search is just string based. We'll search for "1 minute" to avoid 10 hour loops.
    full_query = f"ytsearch1:{search_query}"
    
    # Define temp filename template
    # We want final to be {mood}.mp3
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, f"{mood}.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Searching YouTube for: {full_query}")
            ydl.download([full_query])
            
        # Verify download
        final_path = os.path.join(output_dir, f"{mood}.mp3")
        if os.path.exists(final_path):
            print(f"Downloaded: {final_path}")
            return final_path
        else:
            print("Download failed: File not found after download.")
            return None
            
    except Exception as e:
        print(f"Music download error: {e}")
        return None

if __name__ == "__main__":
    # Test
    get_music_for_mood("Sadness")
