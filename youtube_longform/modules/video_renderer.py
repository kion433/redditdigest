import os
from moviepy.editor import *
from moviepy.video.tools.subtitles import SubtitlesClip
import json
import numpy as np
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

class VideoRenderer:
    def __init__(self):
        self.resolution = (1920, 1080)
        self.fps = 30
    
    def render_segment(self, image_path, audio_path, duration, srt_path, output_path=None):
        """
        Creates a single video segment: Image + Zoom + Audio + Subtitles.
        """
        try:
            # 1. Load Audio
            audio = AudioFileClip(audio_path)
            # Ensure duration matches audio exactly
            final_duration = audio.duration
            
            # 2. Load Image & Apply Ken Burns
            # We create a clip that is slightly larger and crops/zooms over time
            # Smooth Ken Burns Effect
            pil_img = PIL.Image.open(image_path).convert('RGB')
            
            # 1. Calc Geometry
            w, h = pil_img.size
            target_w, target_h = self.resolution
            target_ratio = target_w / target_h
            # Strategy: Resize Image ONCE to valid coverage + 10%, then crop moving window.
            
            # 3. Create Moving Crop
            # We want to show a 1920x1080 window.
            # Start: Window is centered? No, typically Ken Burns zooms IN.
            # Start: Viewport size = (new_w, new_h) / zoom_factor = (target_w, target_h)? No.
            # Let's simplify:
            # We want to display 1920x1080.
            # Frame 0: Crop the center 1920x1080 (which is effectively zoomed in compared to a fit, but consistent).
            # Wait, if we crop 1920x1080 from a 2200x1200 image, it looks "zoomed in" compared to the full image.
            # To simulate "Zoom In", we should start with a larger crop and shrink it, resizing result to 1920x1080?
            # Yes. that is "Source Side Scaling".
            
            # Let's do:
            # Frame 0: Crop = Full "Cover" size (approx 1920x1080) -> Resize to 1920x1080 (Scale ~1.0)
            # Frame End: Crop = Smaller region (1920x1080 / 1.15) -> Resize to 1920x1080 (Scale ~1.15)
            
            # Actually, standard MoviePy 'scroll' is smoother.
            # Let's just take the `img_resized` (which is large)
            # And pan it? NO, we want zoom.
            
            # Correct Smooth Zoom Implementation:
            # 1. Start with high-res image `img`.
            # 2. Define Crop Box at t=0: Center, size = (w, h) (or whatever covers aspect)
            # 3. Define Crop Box at t=end: Center, size = (w/1.15, h/1.15)
            # 4. At time t, interpolate Crop Box.
            # 5. Crop and Resize to 1920x1080.
            
            # We need a custom MakeFrame.
            
            # Base Image (highest available res)
            base_img = pil_img 
            base_w, base_h = base_img.size
            
            # Calculate cover dimensions for 1920x1080
            if base_w / base_h > target_ratio:
                # Wide
                cover_h = base_h
                cover_w = int(base_h * target_ratio)
            else:
                # Tall
                cover_w = base_w
                cover_h = int(base_w / target_ratio)
                
            # Center offsets for cover crop
            off_x = (base_w - cover_w) // 2
            off_y = (base_h - cover_h) // 2
            
            def make_frame(t):
                # Progress 0.0 -> 1.0
                prog = t / final_duration
                current_zoom = 1.0 + (0.15 * prog) # 1.0 -> 1.15
                
                # Calculate Crop Window Size (shrinks as we zoom in)
                # At zoom 1.0, crop is (cover_w, cover_h)
                # At zoom 1.15, crop is (cover_w/1.15, cover_h/1.15)
                
                cw = cover_w / current_zoom
                ch = cover_h / current_zoom
                
                # Center Crop
                cx = off_x + (cover_w - cw) / 2
                cy = off_y + (cover_h - ch) / 2
                
                # Crop and Resize
                # PIL crop: (left, top, right, bottom)
                cropped = base_img.crop((int(cx), int(cy), int(cx+cw), int(cy+ch)))
                resized = cropped.resize(self.resolution, PIL.Image.LANCZOS)
                return np.array(resized)

            final_clip = VideoClip(make_frame, duration=final_duration)
            
            # 3. Add Subtitles
            if srt_path and os.path.exists(srt_path) and os.path.getsize(srt_path) > 10:
                # Custom PIL generator to avoid ImageMagick dependency
                def generator(txt):
                    return self._create_text_clip_pil(txt)
                
                subs = SubtitlesClip(srt_path, generator)
                subs = SubtitlesClip(srt_path, generator)
                # Position subs much higher (0.65) to match "perfect" reel alignment (approx)
                # Original was 0.6, but that's very high. 0.65 is a good balance.
                subs = subs.set_position(('center', 0.65), relative=True)
                
                final_clip = CompositeVideoClip([final_clip, subs], size=self.resolution).set_duration(final_duration)

            final_clip = final_clip.set_audio(audio)
            
            return final_clip
            
        except Exception as e:
            print(f"Error rendering segment: {e}")
            return None

    def _create_text_clip_pil(self, text, fontsize=70, color='white', stroke_width=4, stroke_color='black'):
        """
        Creates a MoviePy ImageClip for text using PIL.
        """
        # 1. Create PIL Image
        # Try custom font first
        font_path = r"youtube_longform/assets/fonts/CrimsonText-Bold.ttf"
        try:
            if os.path.exists(font_path):
                 font = PIL.ImageFont.truetype(font_path, fontsize)
            else:
                 # Fallback to standard serif
                 font = PIL.ImageFont.truetype("times.ttf", fontsize)
        except:
             # Ultimate fallback
             font = PIL.ImageFont.load_default()
            
        # Measure text
        dummy_draw = PIL.ImageDraw.Draw(PIL.Image.new("RGBA", (1,1)))
        left, top, right, bottom = dummy_draw.textbbox((0,0), text, font=font)
        w, h = right - left, bottom - top
        
        # Add generous padding (Fix for cutoff)
        padding = 60
        w += padding * 2
        h += padding * 2
        
        img = PIL.Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0))
        draw = PIL.ImageDraw.Draw(img)
        
        # Calculate centered position
        x = padding
        y = padding
        
        # Draw Stroke (Draw text in stroke color at offsets)
        if stroke_width > 0:
            for off_x in range(-stroke_width, stroke_width+1):
                for off_y in range(-stroke_width, stroke_width+1):
                    draw.text((x+off_x, y+off_y), text, font=font, fill=stroke_color)

        # Draw Text
        draw.text((x, y), text, font=font, fill=color)
        
        # Convert to numpy for MoviePy
        return ImageClip(np.array(img))
            


    def render_chapter(self, segments, output_filename):
        """
        Combines multiple segment clips into one chapter video.
        segments: list of computed clips (VideoFileClips or Composites)
        """
        print(f"Rendering Chapter to {output_filename}...")
        try:
            final_chapter = concatenate_videoclips(segments, method="compose")
            # Specify temp audio file to prevent leakage in root
            temp_audio = output_filename.replace(".mp4", "_temp_audio.m4a")
            final_chapter.write_videofile(output_filename, fps=self.fps, codec="libx264", audio_codec="aac", temp_audiofile=temp_audio, remove_temp=True)
            return output_filename
        except Exception as e:
            print(f"Chapter Render Error: {e}")
            return None
