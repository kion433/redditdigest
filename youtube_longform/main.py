import asyncio
import argparse
import os
import random
import re
from youtube_longform.config import OUTPUT_DIR, BASE_DIR
from youtube_longform.modules.topic_generator import TopicGenerator
from youtube_longform.modules.script_writer import ScriptWriter
from youtube_longform.modules.image_generator import ImageGenerator
from youtube_longform.modules.audio_generator import AudioGenerator
from youtube_longform.modules.video_renderer import VideoRenderer
import time

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str, default="Human Psychology", help="Topic domain")
    parser.add_argument("--test", action="store_true", help="Run a short test (Dummy Data, Placeholders)")
    parser.add_argument("--prototype", action="store_true", help="Run a 1-chapter REAL AI generation (Short Video)")
    args = parser.parse_args()
    
    print(f"--- Starting Long Form Generator (Domain: {args.domain}) ---")
    
    # Init Modules
    topic_gen = TopicGenerator()
    script_writer = ScriptWriter()
    image_gen = ImageGenerator()
    audio_gen = AudioGenerator()
    video_renderer = VideoRenderer()
    
    # 1. Topic Selection
    if args.test:
        topic = {"title": "Test Topic", "premise": "Testing the pipeline."}
    else:
        topics = topic_gen.generate_topics(args.domain)
        if not topics:
            print("Failed to generate topics.")
            return
            
        # For automation, pick random. For real use, could ask user.
        topic = random.choice(topics)
        print(f"Selected Topic: {topic['title']}")
        print(f"Premise: {topic['premise']}")
        
    # 2. Script Generation
    if args.test:
        # Dummy script
        script_data = {
            "title": "Test Video",
            "chapters": [
                {
                    "title": "Chapter 1: The Test",
                    "segments": [
                        {
                            "text": "This is a test of the emergency broadcast system. It uses Ken Burns effects.",
                            "image_prompt": "A retro television set displaying static noise, 1980s style, oil painting"
                        }
                    ]
                }
            ]
        }
    else:
        # Real AI Script
        num_chapters = 1 if args.prototype else 5
        script_data = script_writer.generate_detailed_script(topic, num_chapters=num_chapters)
        if not script_data:
            print("Failed to generate script.")
            return

    # 3. Production Loop
    chapter_files = []
    
    # Sanitize title for folder name (Windows compatibility)
    safe_title = re.sub(r'[<>:"/\\|?*]', '', topic['title'])
    safe_title = safe_title.replace(" ", "_").strip()
    
    video_folder = os.path.join(OUTPUT_DIR, safe_title)
    os.makedirs(video_folder, exist_ok=True)
    
    for i, chapter in enumerate(script_data['chapters']):
        print(f"\nProcessing {chapter['title']}...")
        chapter_segments = []
        
        for j, seg in enumerate(chapter['segments']):
            print(f"  Segment {j+1}/{len(chapter['segments'])}...")
            
            # Paths
            base_name = f"ch{i}_seg{j}"
            audio_path = os.path.join(video_folder, f"{base_name}.mp3")
            image_path = os.path.join(video_folder, f"{base_name}.png")
            
            # A. Audio
            res = await audio_gen.generate_narration(seg['text'], audio_path)
            if not res: continue
            _, _, srt_path, duration = res
            
             # B. Image
            if not os.path.exists(image_path): # Cache check
                if args.test:
                    # Save tokens during testing
                    print("Test Mode: Generating placeholder image...")
                    image_gen._create_placeholder(image_path, seg['image_prompt'])
                else:
                    success = image_gen.generate_image(seg['image_prompt'], image_path)
                    if not success:
                        print("    Image failed. Using fallback?")
                        # Continue anyway? Render will fail if no image.
                        continue
            
            # C. Render Segment (In Memory)
            clip = video_renderer.render_segment(image_path, audio_path, duration, srt_path)
            if clip:
                chapter_segments.append(clip)
            
            if args.test: break # Only 1 segment for test
            
        # Render Chapter
        if chapter_segments:
            chapter_out = os.path.join(video_folder, f"chapter_{i}.mp4")
            out_file = video_renderer.render_chapter(chapter_segments, chapter_out)
            if out_file:
                chapter_files.append(out_file)
            
            # Close clips to free memory
            for c in chapter_segments: c.close()
            
        if args.test: break # Only 1 chapter for test

    print("\n--- All Chapters Rendered ---")
    print(f"Files: {chapter_files}")
    
    # 4. Final Concatenation (Optional, or just leave chapters)
    # We could use ffmpeg list concatenation here to be fast.
    
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
