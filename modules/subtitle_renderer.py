from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, CompositeVideoClip
import numpy as np
import re
import os

def parse_vtt(vtt_path):
    """
    Parses a simple VTT file from edge-tts.
    Returns list of (start_seconds, end_seconds, text).
    """
    subs = []
    time_pattern = re.compile(r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3}) --> (\d{2}):(\d{2}):(\d{2})[.,](\d{3})")
    
    with open(vtt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    current_start = None
    current_end = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        match = time_pattern.match(line)
        if match:
            # Parse start
            h, m, s, ms = map(int, match.groups()[0:4])
            current_start = h*3600 + m*60 + s + ms/1000
            
            # Parse end
            h, m, s, ms = map(int, match.groups()[4:8])
            current_end = h*3600 + m*60 + s + ms/1000
            
            # Text is usually on the next line
            if i + 1 < len(lines):
                text = lines[i+1].strip()
                if text:
                    subs.append((current_start, current_end, text))
    return subs

def create_caption_clip(text, duration, video_w, video_h, font_path=None):
    """
    Creates a transparent ImageClip with popped text using PIL.
    """
    # Settings
    fontsize = 70 # Reduced to 70 as requested
    stroke_width = 6 # Slightly thinner stroke for smaller font
    text_color = "yellow"
    stroke_color = "black"
    
    if not font_path or not os.path.exists(font_path):
        # Fallback to absolute path just in case
        font_path = os.path.abspath("assets/fonts/KomikaAxis.ttf")
    
    font = ImageFont.truetype(font_path, fontsize)
    
    # Measure text size
    dummy_img = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    
    try:
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
        text_w = right - left
        text_h = bottom - top
    except AttributeError:
        # Compatibility for older Pillow versions
        text_w, text_h = draw.textsize(text, font=font, stroke_width=stroke_width)
    
    # Add GENEROUS padding to prevent cutoff
    w, h = text_w + 100, text_h + 100
    
    img = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw text centered in the image
    draw.text((50, 50), text, font=font, fill=text_color, stroke_fill=stroke_color, stroke_width=stroke_width)
    
    # Create ImageClip
    img_array = np.array(img)
    txt_clip = ImageClip(img_array).set_duration(duration)
    
    # Center perfectly on screen
    txt_clip = txt_clip.set_position(('center', 'center'))
    
    # "Pop" Effect (Resize from 0.5 to 1.2 then 1.0)
    # Using MoviePy 1.x logic (resize accepts function)
    def resize_func(t):
        if t < 0.1:
            return 0.5 + (0.7 * (t / 0.1)) # 0.5 -> 1.2
        elif t < 0.2:
            return 1.2 - (0.2 * ((t - 0.1) / 0.1)) # 1.2 -> 1.0
        else:
            return 1.0
            
    # Apply resize effect
    txt_clip = txt_clip.resize(resize_func) 
    
    return txt_clip

def add_subtitles(video_clip, data_path, font_path="arial.ttf"):
    """
    Overlays subtitles onto the video_clip.
    data_path: Path to either .vtt or .json (word timestamps).
    """
    subtitle_clips = []
    w, h = video_clip.size
    
    # Check if JSON (Perfect Sync)
    if data_path.endswith(".json"):
        import json
        with open(data_path, "r", encoding="utf-8") as f:
            words = json.load(f)
            
        print(f"Applying Perfect Sync for {len(words)} words...")
        
        for item in words:
            word = item['word']
            start = item['start']
            end = item['end']
            duration = end - start
            
            # Min duration for visibility
            if duration < 0.15: duration = 0.15
            
            txt_clip = create_caption_clip(word, duration, w, h, font_path)
            txt_clip = txt_clip.set_start(start)
            subtitle_clips.append(txt_clip)
            
    else:
        # Fallback to VTT (Approximate)
        subs = parse_vtt(data_path)
        for start, end, text in subs:
            full_duration = end - start
            if full_duration <= 0: continue
            
            words = text.split()
            if not words: continue
            
            # Character-based sync (Legacy/Fallback)
            total_chars = sum(len(w) for w in words)
            if total_chars == 0: total_chars = 1
            
            duration_per_char = full_duration / total_chars
            
            current_time = start
            for word in words:
                word_len = len(word)
                word_duration = word_len * duration_per_char
                if word_duration < 0.1: pass

                txt_clip = create_caption_clip(word, word_duration, w, h, font_path)
                txt_clip = txt_clip.set_start(current_time)
                subtitle_clips.append(txt_clip)
                current_time += word_duration
        
    return CompositeVideoClip([video_clip] + subtitle_clips)
