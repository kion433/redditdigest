import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import VideoFileClip, AudioFileClip, vfx, CompositeVideoClip, ImageClip
import random
import os
from modules.subtitle_renderer import add_subtitles
from config import *

class VideoEngine:
    def __init__(self):
        self.background_path = BACKGROUND_VIDEO_PATH
        self.output_path = os.path.join(OUTPUT_VIDEO_PATH, "finished_videos")
        # Ensure dirs exist
        os.makedirs(self.background_path, exist_ok=True)
        os.makedirs(self.output_path, exist_ok=True)

    def get_random_background(self):
        files = [f for f in os.listdir(self.background_path) if f.endswith(('.mp4', '.mov'))]
        if not files:
            raise FileNotFoundError(f"No background videos found in {self.background_path}")
        return os.path.join(self.background_path, random.choice(files))

    def create_video(self, audio_path, script_data, sync_path=None):
        """
        Merges background video with audio AND image overlays using MoviePy 1.x syntax.
        """
        import json
        print(f"DEBUG SCRIPT DATA: {json.dumps(script_data, indent=2)}")
        try:
            # MoviePy 1.x imports
            from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
            import moviepy.video.fx.all as vfx
            
            from modules.image_downloader import download_image
            import math

            print("Initializing MoviePy editor...")
            bg_video_path = self.get_random_background()
            
            # Load Audio
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration
            
            # Load Background Video
            video_clip = VideoFileClip(bg_video_path)
            
            # Loop/Cut Logic (MoviePy 1.x)
            if video_clip.duration < audio_duration:
                # vfx.loop in 1.x
                video_clip = vfx.loop(video_clip, duration=audio_duration)
            
            if video_clip.duration > audio_duration:
                max_start = video_clip.duration - audio_duration
                start_time = random.uniform(0, max_start)
                print(f"Randomly seeking to {start_time:.2f}s")
                # .subclip in 1.x
                video_clip = video_clip.subclip(start_time, start_time + audio_duration)
            else:
                 video_clip = video_clip.set_duration(audio_duration)
            
            # --- 9:16 CROP LOGIC (vfx.crop in 1.x) ---
            w, h = video_clip.size
            target_ratio = 9/16
            current_ratio = w/h
            
            if current_ratio > target_ratio:
                new_w = int(h * target_ratio)
                if new_w % 2 != 0: new_w -= 1
                video_clip = vfx.crop(video_clip, x1=(w/2 - new_w/2), width=new_w, height=h)
            else:
                new_h = int(w / target_ratio)
                if new_h % 2 != 0: new_h -= 1
                video_clip = vfx.crop(video_clip, y1=(h/2 - new_h/2), width=w, height=new_h)
            
            final_w, final_h = video_clip.size

            # --- IMAGE OVERLAY PREPARATION ---
            # 1. Download Images
            temp_img_dir = "temp_images"
            os.makedirs(temp_img_dir, exist_ok=True)
            
            image_clips = []
            
            # Helper: styled image clip (1.x syntax)
            def create_centered_image_clip(img_path, start_t, duration_t):
                if not img_path: return None
                img = ImageClip(img_path).set_start(start_t).set_duration(duration_t)
                
                # Resize to 70% width
                target_img_w = final_w * 0.7
                img = img.resize(width=target_img_w)
                
                # Center it
                img = img.set_position(("center", "center"))
                
                # Revert to Fade In (Pop animation caused visibility issues)
                img = img.crossfadein(0.5)
                
                # Simple Fade Out at end
                img = img.crossfadeout(0.5)
                
                return img

            # A. Hook Image
            hook_mood = script_data.get('hook_mood')
            if hook_mood:
                print(f"Downloading Hook Image (Mood: {hook_mood})")
                hook_path = download_image(hook_mood, temp_img_dir, "hook")
                hook_clip = create_centered_image_clip(hook_path, 0, 3)
                if hook_clip: image_clips.append(hook_clip)

            # B. Retention Images (Memes)
            # Prioritize specific "visual_keywords" if available, else fallback to moods
            visual_queries = script_data.get('visual_keywords', script_data.get('retention_moods', []))
            
            if visual_queries:
                # We want them to stay longer (4s), so we might fit fewer images
                # Calculate how many 4s images fit in the available time
                available_time = audio_duration - 4 # buffer for hook
                
                # Limit number of images to prevent overcrowding
                # If we have 20s available, we can fit ~5 images
                max_images = int(available_time / 4.5) 
                if max_images < 1: max_images = 1
                
                # Take top N queries
                queries_to_use = visual_queries[:max_images]
                
                if available_time > 0:
                    # Space them out evenly or just back-to-back?
                    # Let's do evenly distributed centers
                    interval = available_time / (len(queries_to_use) + 1)
                    
                    for i, query in enumerate(queries_to_use):
                        print(f"Downloading Retention Image (Query: {query})")
                        # Add 'meme' to query if not present for better results
                        search_q = query if "meme" in query.lower() else f"{query} meme funny"
                        
                        path = download_image(search_q, temp_img_dir, f"retention_{i}")
                        
                        # Start time: Hook end (3s) + interval step
                        start_t = 3 + (i * interval)
                        
                        # Duration: 4 seconds (User Request)
                        clip = create_centered_image_clip(path, start_t, 4.0)
                        if clip: image_clips.append(clip)

            # --- COMPOSITING ---
            # Layer 1: Background Video
            # Layer 2: Image Overlays
            
            video_with_images = CompositeVideoClip([video_clip] + image_clips)
            video_with_images = video_with_images.set_audio(audio_clip)

            # --- SUBTITLES ---
            subtitle_file = sync_path
            if not subtitle_file or not os.path.exists(subtitle_file):
                 base_name = os.path.splitext(audio_path)[0]
                 subtitle_file = base_name + ".vtt"

            final_clip = video_with_images 
            
            if subtitle_file and os.path.exists(subtitle_file):
                print(f"Adding subtitles from {subtitle_file}...")
                final_clip = add_subtitles(video_with_images, subtitle_file, font_path=FONT_PATH)
            
            # --- 6. Audio Mixing (TTS + BGM) ---
            final_audio = audio_clip # Use the loaded audio_clip as the base for final_audio
            
            try:
                from modules.music_downloader import get_music_for_mood
                from moviepy.editor import AudioFileClip, CompositeAudioClip, afx
                
                # 1. Get Mood
                mood = script_data.get('hook_mood', 'Neutral')
                print(f"Fetching Background Music for Mood: {mood}")
                
                # 2. Get/Download Track
                bgm_path = get_music_for_mood(mood, "assets/music")
                
                if bgm_path and os.path.exists(bgm_path):
                    # 3. Load & Process BGM
                    bgm_clip = AudioFileClip(bgm_path)
                    
                    # Random Start Logic
                    # Pick a random point in the song to start
                    if bgm_clip.duration > 0:
                        bgm_start = random.uniform(0, bgm_clip.duration)
                    else:
                        bgm_start = 0
                        
                    # Calculate total duration needed to support starting late + video length
                    needed_duration = bgm_start + final_clip.duration + 1.0 # +1s buffer
                    
                    # Loop the track enough times to cover the needed duration
                    # afx.audio_loop repeats the clip content
                    bgm_looped = bgm_clip.fx(afx.audio_loop, duration=needed_duration)
                    
                    # Cut the segment from [start, start + duration]
                    # This achieves the "Random Start + Loop if hit end" behavior
                    bgm_clip = bgm_looped.subclip(bgm_start, bgm_start + final_clip.duration)
                    
                    # Set Volume (Low Ambience)
                    
                    # Set Volume (Low Ambience)
                    bgm_clip = bgm_clip.volumex(0.12) # 12% Volume
                    
                    # Trim exactly to video length
                    bgm_clip = bgm_clip.subclip(0, final_clip.duration)
                    
                    # 4. Mix
                    final_audio = CompositeAudioClip([audio_clip, bgm_clip]) # Use audio_clip here
                    print("Background Music Mixed Successfully.")
                else:
                    print("Background Music skipped (Download failed or file missing).")
                    
            except Exception as e:
                print(f"Background Music Warning: {e}")
                # non-critical, proceed with just voice
            
            final_clip = final_clip.set_audio(final_audio)

            # --- 7. Write Output ---
            final_filename = f"final_{random.randint(1000,9999)}.mp4"
            output_filepath = os.path.join(self.output_path, final_filename)
            
            print(f"Rendering Video to {output_filepath}...")
            final_clip.write_videofile(
                output_filepath, 
                codec='libx264', 
                audio_codec='aac', 
                temp_audiofile='temp-audio.m4a', 
                remove_temp=True,
                fps=30,
                preset='medium',
                ffmpeg_params=['-pix_fmt', 'yuv420p']
            )
            
            final_clip.close()
            video_clip.close() 
            audio_clip.close()
            
            return output_filepath

        except Exception as e:
            print(f"Error creating video with MoviePy: {e}")
            import traceback
            traceback.print_exc()
            return None
