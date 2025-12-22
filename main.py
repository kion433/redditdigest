import asyncio
import argparse
import random
import os
import json
from config import *
from modules.reddit_client import RedditClient
from modules.content_generator import ContentGenerator
from modules.video_engine import VideoEngine
from modules.post_history import PostHistory
# from modules.instagram_client import InstagramClient

async def run_one_cycle(reddit, content_gen, video_engine, history, index, total, mode="classic", fast_mode=False):
    print(f"\n--- [Batch {index}/{total}] Starting Cycle ---")
    
    # 2. Get Content
    # 2. Get Content (Aggressive Retry)
    max_retries = 10
    post = None
    
    for attempt in range(max_retries):
        sort_strategy = random.choice(["top", "controversial", "best"])
        print(f"Fetching Reddit posts (Attempt {attempt+1}/{max_retries} | Sort: {sort_strategy})...")
        
        # RedditClient now handles random sub selection if we don't pass one, 
        # BUT we want to force a re-roll if it failed.
        # Since main.py passed `subreddits=list` to init, `get_top_posts()` picks one internally if None passed.
        candidates = reddit.get_top_posts(time_filter=REDDIT_TIMEFRAME, limit=75, sort=sort_strategy)
        
        for candidate in candidates:
            if not history.is_seen(candidate['id']):
                post = candidate
                break
        
        if post:
            print(f"Found suitable post: {post['title']}")
            break
        else:
            print("No suitable posts in this sub/batch. Retrying...")
            
    if not post:
        print("CRITICAL: No new suitable posts found after multiple retries.")
        return False
        
    print(f"Found post: {post['title']}")
    history.add_post(post) 

    # 3. Generate Script
    print("Generating script from LLM...")
    script_data = content_gen.generate_script(post)
    if not script_data:
        print("Failed to generate script.")
        return False
        
    print(f"Script generated. Title: {script_data['title_overlay']}")
    
    # 4. Audio
    # Use a unique temp filename for audio to avoid collisions if running parallel (future proofing)
    temp_audio_name = f"temp_audio_{index}.mp3"
    audio_path = os.path.join(OUTPUT_VIDEO_PATH, temp_audio_name)
    
    # Determine Input Source (Segments > Text)
    script_segments = script_data.get('script_segments')
    if script_segments and fast_mode:
        print("[DEBUG] Fast Mode: Truncating script to 3 segments for rapid testing.")
        script_segments = script_segments[:3]
        
    script_input = script_segments if script_segments else script_data.get('script_text')
    
    input_len = len(str(script_input)) # Approx length for logging
    print(f"Generating audio (Input Len: {input_len})...")
    # Pass script_data (which includes 'used_subreddit') as context
    result = await content_gen.generate_audio(script_input, audio_path, context_data=script_data)
    
    if not result:
        print("Failed to generate audio.")
        return False
        
    # Audio + Metadata (JSON) are now returned
    audio_path, sync_path = result
    
    # 5. Create Video
    try:
        final_video_path = video_engine.create_video(audio_path, script_data, sync_path=sync_path, mode=mode)
        if final_video_path:
            # Save Metadata Sidecar for Scheduler
            base_name = os.path.splitext(final_video_path)[0]
            json_sidecar_path = f"{base_name}.json"
            
            meta_data = {
                "id": post['id'],
                "title": script_data.get('title', 'Reddit Story'),
                "caption": script_data.get('caption', f"{post['title']} #reddit"),
                "author": post['author'],
                "subreddit": post['subreddit'],
                "video_path": final_video_path
            }
            
            with open(json_sidecar_path, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, indent=2, ensure_ascii=False)
                
            print(f"\nSUCCESS! Video created at: {final_video_path}")
            print(f"Metadata saved to: {json_sidecar_path}")
            return True
    except Exception as e:
        print(f"Video generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate")
    parser.add_argument("--mode", type=str, default="classic", choices=["classic", "brainrot"], help="Video Style: 'classic' (Fullscreen Gameplay) or 'brainrot' (Split Screen)")
    parser.add_argument("--fast", action="store_true", help="Debug Mode: Generate a very short video")
    args = parser.parse_args()
    
    print(f"--- AI Instagram Bot Starting (Target: {args.count} videos | Mode: {args.mode}) ---")
    
    # 1. Initialize Modules
    reddit = RedditClient(subreddits=REDDIT_SUBREDDITS)
    content_gen = ContentGenerator()
    video_engine = VideoEngine()
    history = PostHistory()
    
    successful = 0
    for i in range(1, args.count + 1):
        if await run_one_cycle(reddit, content_gen, video_engine, history, i, args.count, mode=args.mode, fast_mode=args.fast):
            successful += 1
        
        # Small delay between batches to be nice to APIs?
        if i < args.count:
            print("Waiting 5 seconds before next batch...")
            await asyncio.sleep(5)
            
    print(f"\n--- Batch Finished. {successful}/{args.count} videos created. ---")

if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
