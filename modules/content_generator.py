import asyncio
from openai import OpenAI
import edge_tts
import random
import os
import json
from config import *

class ContentGenerator:
    def __init__(self):
        self.client = OpenAI(
            api_key=OPENAI_API_KEY, 
            base_url=OPENAI_BASE_URL
        )
        self.model = AI_MODEL_NAME

    def generate_script(self, post_data):
        """
        Uses LLM to clean up Reddit post and create a caption.
        """
        # --- PERSONA LOGIC ---
        subreddit = post_data.get('subreddit', '').lower()
        
        # Default Persona
        persona_role = "HECKLER: Interrupts every 2-3 sentences to roast the OP, scream 'WHAT?!', or hype up the drama."
        
        # Subreddit-Specific Personas
        if 'amitheasshole' in subreddit:
            persona_role = "THE JUDGE: Deep, authoritative voice. Interrupts to pass judgment (e.g., 'GUILTY!', 'Objection!', 'You are the problem')."
        elif 'tifu' in subreddit:
             persona_role = "THE ROASTER: Laughs at the OP's pain. Mocking tone. (e.g., 'You idiot!', 'Look at this guy!', 'Embarrassing!')."
        elif 'creepy' in subreddit or 'nosleep' in subreddit:
             persona_role = "THE COWARD: Nervous, whispering voice. Warns the OP to run. (e.g., 'Don't look back!', 'Run bro!', 'I hear something...')."
             
        system_prompt = f"""You are a viral TikTok/Reels scriptwriter. 
        Your goal is to transform a Reddit story into a highly engaging, "Heckler-Style" video script.
        
        STRUCTURE:
        The video features TWO voices:
        1. **NARRATOR**: Tells the story seriously.
        2. **{persona_role}**
        
        REQUIREMENTS:
        - **HOOK (0-3s)**: Narrator starts with a shocker.
        - **INTERRUPTIONS**: The Heckler/Persona should interrupt 2-3 times total. Keep them short.
        - **CTA**: Narrator asks the question, Heckler demands the comment.
        
        Output format (JSON):
        {{
          "script_segments": [
            {{"role": "narrator", "text": "My best friend tried to turn my empty apartment..."}},
            {{"role": "heckler", "text": "Bro, lock the doors!"}},
            {{"role": "narrator", "text": "...into her personal storage unit."}}
          ],
          "caption": "Viral caption with hashtags.",
          "title_overlay": "Punchy 3-5 word cover title",
          "hook_mood": "One strict emotion from: 'Shock', 'Anger', 'Fear', 'Sadness', 'Joy', 'Disgust', 'Confused', 'Neutral'. Focus on initial feeling.",
          "retention_moods": ["List", "of", "3-5", "strict", "emotions", "that", "match", "the", "story", "progression"],
          "visual_keywords": ["List", "of", "3-5", "specific", "search", "terms", "for", "memes", "related", "to", "the", "story", "e.g.", "cheating boyfriend meme", "angry karen meme", "spiderman pointing meme"]
        }}
        """
        
        user_content = f"Title: {post_data['title']}\n\nBody: {post_data['text']}"
        
        try:
            print(f"Generating script from LLM (Persona: {persona_role[:30]}...)...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={ "type": "json_object" }
            )
            content = response.choices[0].message.content
            print(f"DEBUG LLM CONTENT: {content}")
            data = json.loads(content)
            
            # Helper to pass subreddit down for voice selection later
            data['used_subreddit'] = subreddit 
            
            # Ensure keys exist
            if 'title_overlay' not in data:
                data['title_overlay'] = post_data['title'][:30] 
            if 'caption' not in data:
                 data['caption'] = f"{post_data['title']} #reddit #viral"
            
            # Backwards compatibility
            if 'script_segments' not in data and 'script_text' in data:
                 data['script_segments'] = [{'role': 'narrator', 'text': data['script_text']}]
            
            return data
        except Exception as e:
            print(f"Error generating script: {e}")
            return None

    async def generate_audio(self, script_input, output_filename="speech.mp3", voice=None, context_data=None):
        """
        Generates TTS audio AND precise word-level JSON timestamps.
        Supports 'script_input' as either a string (single voice) or list of dicts (multi-voice).
        """
        try:
            # 1. Handle Multi-Voice "Heckler" Mode
            if isinstance(script_input, list):
                print(f"Generating Multi-Voice Audio ({len(script_input)} segments)...")
                return await self._generate_multi_voice_audio(script_input, output_filename, context_data)
                
            # 2. Handle Single Voice Mode (Legacy/Fallback)
            text = script_input
            if not voice:
                voice = random.choice(TTS_VOICES)
            
            return await self._generate_single_segment(text, voice, output_filename)

        except Exception as e:
            print(f"Error generating audio: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _generate_single_segment(self, text, voice, output_filename, offset_s=0):
        """Helper to generate audio for one segment."""
        # Sanitize
        clean_text = text.replace('"', '').replace("'", "").replace("’", "").strip()
        if not clean_text: return None

        print(f"  Generating segment ({len(clean_text)} chars) with {voice}...")
        
        output_abs = os.path.abspath(output_filename)
        base_name = os.path.splitext(output_abs)[0]
        json_filename = base_name + ".json"
        
        # Windows Loop Fix
        if os.name == "nt":
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            except: pass

        communicate = edge_tts.Communicate(clean_text, voice)
        word_data = []
        
        with open(output_abs, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    # Calculate timing with global offset
                    start_s = (chunk["offset"] / 1e7) + offset_s
                    duration_s = chunk["duration"] / 1e7
                    end_s = start_s + duration_s
                    word_txt = chunk["text"]
                    
                    word_data.append({
                        "word": word_txt,
                        "start": start_s,
                        "end": end_s
                    })
        
        # Save Metadata
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(word_data, f, indent=2)
            
        return output_abs, json_filename, word_data

    async def _generate_multi_voice_audio(self, segments, final_output_filename, context_data=None):
        """Stitches multiple TTS segments into one file and merges timestamps."""
        from moviepy.editor import concatenate_audioclips, AudioFileClip
        
        # Voice Mapping
        NARRATOR_VOICE = "en-US-GuyNeural"
        
        # Determine Heckler Voice based on Context (Subreddit)
        subreddit = ""
        if context_data and 'used_subreddit' in context_data:
            subreddit = context_data['used_subreddit']
            
        # Default Random Pool
        heckler_voice = random.choice(["en-US-ChristopherNeural", "en-US-EricNeural", "en-US-RogerNeural"])
        
        if 'amitheasshole' in subreddit:
             heckler_voice = "en-US-RogerNeural" # Deep/Authoritative
             print("  Persona: Judge (en-US-RogerNeural)")
        elif 'creepy' in subreddit or 'nosleep' in subreddit:
             heckler_voice = "en-US-SteffanNeural" # Softer/Anxious
             print("  Persona: Coward (en-US-SteffanNeural)")
        elif 'tifu' in subreddit:
             heckler_voice = "en-US-ChristopherNeural" # Aggressive
             print("  Persona: Roaster (en-US-ChristopherNeural)")
        else:
            print(f"  Persona: Random Heckler ({heckler_voice})")
        
        temp_files = []
        master_word_data = []
        current_offset = 0.0
        
        final_output_abs = os.path.abspath(final_output_filename)
        master_json_abs = os.path.splitext(final_output_abs)[0] + ".json"
        master_vtt_abs = os.path.splitext(final_output_abs)[0] + ".vtt"

        try:
            clips = []
            
            for i, seg in enumerate(segments):
                role = seg.get('role', 'narrator')
                text = seg.get('text', '')
                
                # Select Voice
                voice = heckler_voice if role == 'heckler' else NARRATOR_VOICE
                
                # Generate Temp Segment
                seg_filename = f"temp_seg_{i}_{random.randint(100,999)}.mp3"
                result = await self._generate_single_segment(text, voice, seg_filename, offset_s=current_offset)
                
                if result:
                    audio_path, json_path, data = result
                    temp_files.append(audio_path)
                    temp_files.append(json_path)
                    
                    # Add to clips for merging
                    clip = AudioFileClip(audio_path)
                    clips.append(clip)
                    
                    # Update Offset
                    duration = clip.duration
                    current_offset += duration
                    
                    # Append Data
                    if not data:
                        print(f"  Warning: No timing data for segment {i}. Estimating...")
                        words = text.split()
                        if words:
                            total_chars = sum(len(w) for w in words)
                            if total_chars == 0: total_chars = 1
                            char_duration = duration / total_chars
                            est_data = []
                            est_offset = current_offset - duration # current_offset was already incremented
                            temp_time = est_offset
                            for w in words:
                                w_dur = len(w) * char_duration
                                est_data.append({
                                    "word": w,
                                    "start": temp_time,
                                    "end": temp_time + w_dur
                                })
                                temp_time += w_dur
                            master_word_data.extend(est_data)
                    else:
                        master_word_data.extend(data)
            
            # Stitch Audio
            print("  Stitching dialogue segments...")
            final_audio = concatenate_audioclips(clips)
            final_audio.write_audiofile(final_output_abs, logger=None)
            
            # Close clips to release files
            for clip in clips: clip.close()
            final_audio.close()
            
            # Save Master JSON
            with open(master_json_abs, "w", encoding="utf-8") as f:
                json.dump(master_word_data, f, indent=2)
                
            # Create Master VTT (Simple Rebuild)
            with open(master_vtt_abs, "w", encoding="utf-8") as f:
                f.write("WEBVTT\n\n")
                for w in master_word_data:
                    start = self._format_vtt_time(w['start'])
                    end = self._format_vtt_time(w['end'])
                    f.write(f"{start} --> {end}\n{w['word']}\n\n")

            # Cleanup Temp Files
            for f in temp_files:
                if os.path.exists(f): os.remove(f)

            return final_output_abs, master_json_abs

        except Exception as e:
            print(f"Stitching Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _format_vtt_time(self, seconds):
        # Format: 00:00:00.000
        ms = int((seconds % 1) * 1000)
        s = int(seconds) % 60
        m = int(seconds // 60) % 60
        h = int(seconds // 3600)
        return f"{h:02}:{m:02}:{s:02}.{ms:03}"
