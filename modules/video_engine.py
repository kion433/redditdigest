import random
import os
from moviepy import VideoFileClip, AudioFileClip, vfx
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
        Merges background video with audio using MoviePy 2.x.
        """
        try:
            print("Initializing MoviePy editor...")
            bg_video_path = self.get_random_background()
            
            # Load Audio (Rest of code identical...)
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration
            
            # Load Video
            video_clip = VideoFileClip(bg_video_path)
            
            # Loop video if shorter
            if video_clip.duration < audio_duration:
                video_clip = vfx.Loop(duration=audio_duration).apply(video_clip)
            
            # Cut video
            if video_clip.duration > audio_duration:
                max_start = video_clip.duration - audio_duration
                start_time = random.uniform(0, max_start)
                print(f"Randomly seeking to {start_time:.2f}s (Total duration: {video_clip.duration:.2f}s)")
                video_clip = video_clip.subclipped(start_time, start_time + audio_duration)
            else:
                 video_clip = video_clip.with_duration(audio_duration)
            
            # --- 9:16 CROP LOGIC ---
            w, h = video_clip.size
            target_ratio = 9/16
            current_ratio = w/h
            
            if current_ratio > target_ratio:
                new_w = int(h * target_ratio)
                if new_w % 2 != 0: new_w -= 1
                video_clip = video_clip.cropped(x1=(w/2 - new_w/2), width=new_w, height=h)
            else:
                new_h = int(w / target_ratio)
                if new_h % 2 != 0: new_h -= 1
                video_clip = video_clip.cropped(y1=(h/2 - new_h/2), width=w, height=new_h)

            # Set Audio
            video_clip = video_clip.with_audio(audio_clip)

            # Add Subtitles
            # Prefer passed sync_path (JSON), fallback to checking file
            subtitle_file = sync_path
            
            if not subtitle_file or not os.path.exists(subtitle_file):
                 # Fallback to legacy VTT
                 base_name = os.path.splitext(audio_path)[0]
                 subtitle_file = base_name + ".vtt"

            if subtitle_file and os.path.exists(subtitle_file):
                print(f"Adding subtitles from {subtitle_file}...")
                video_clip = add_subtitles(video_clip, subtitle_file, font_path=FONT_PATH)
            
            # Output
            final_filename = f"final_{random.randint(1000,9999)}.mp4"
            output_filepath = os.path.join(self.output_path, final_filename)
            
            print(f"Rendering Video to {output_filepath}...")
            video_clip.write_videofile(
                output_filepath, 
                codec='libx264', 
                audio_codec='aac', 
                temp_audiofile='temp-audio.m4a', 
                remove_temp=True,
                fps=30,
                preset='medium',
                ffmpeg_params=['-pix_fmt', 'yuv420p']
            )
            
            video_clip.close()
            audio_clip.close()
            
            return output_filepath

        except Exception as e:
            print(f"Error creating video with MoviePy: {e}")
            import traceback
            traceback.print_exc()
            return None
