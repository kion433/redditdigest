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
        system_prompt = """You are a viral TikTok/Reels scriptwriter. 
        Your goal is to transform a Reddit story into a highly engaging, retention-focused video script.
        
        STRUCTURE REQUIREMENTS:
        1. **HOOK (0-3s)**: Start with an outrageous, absurd, or shocking statement summarizing the conflict. Do NOT say "Here is a story about...". Jump right into the drama. (e.g., "My mother-in-law just demanded I pay her rent because she babysat once!")
        2. **THE STORY**: Tell the core event clearly. Keep the original facts but make the pacing fast. Remove fluff.
        3. **CTA (Ending)**: End abruptly with a question to drive comments. (e.g., "Am I the jerk here? Tell me in the comments!" or "What would you do?")
        
        Output format (JSON):
        {
          "script_text": "The full spoken script including Hook, Story, and CTA. Approx 150-180 words.",
          "caption": "Viral caption with hashtags.",
          "title_overlay": "Punchy 3-5 word cover title"
        }
        """
        
        user_content = f"Title: {post_data['title']}\n\nBody: {post_data['text']}"
        
        try:
            print("Generating script from LLM...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={ "type": "json_object" }
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # Ensure keys exist
            if 'title_overlay' not in data:
                data['title_overlay'] = post_data['title'][:30] # Fallback to reddit title
            if 'caption' not in data:
                 data['caption'] = f"{post_data['title']} #reddit #viral"
            
            return data
        except Exception as e:
            print(f"Error generating script: {e}")
            return None

    async def generate_audio(self, text, output_filename="speech.mp3", voice=None):
        """
        Generates TTS audio AND precise word-level JSON timestamps using Edge-TTS python library.
        Selects a random voice if none is provided.
        """
        try:
            # Randomize voice if not specified or default
            if not voice:
                voice = random.choice(TTS_VOICES)
            
            print(f"Generating audio ({len(text)} chars) using Voice: {voice}...")
            # Sanitize text to prevent WordBoundary failures (Edge-TTS bug with special chars)
            clean_text = text.replace('"', '').replace("'", "").replace("’", "").strip()
            print(f"Generating audio ({len(clean_text)} chars) + Sync Data...")
            
            output_abs = os.path.abspath(output_filename)
            base_name = os.path.splitext(output_abs)[0]
            json_filename = base_name + ".json"
            vtt_filename = base_name + ".vtt" # Keep legacy VTT for reference/fallback

            # Windows Loop Policy (Safe to set here for script execution)
            if os.name == "nt":
                try:
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                except:
                    pass # Might already be set

            communicate = edge_tts.Communicate(clean_text, voice)
            word_data = []
            
            # Simple VTT builder strings
            vtt_lines = ["WEBVTT\n\n"]
            
            with open(output_abs, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        # 10,000,000 ticks = 1 second
                        start_s = chunk["offset"] / 1e7
                        duration_s = chunk["duration"] / 1e7
                        end_s = start_s + duration_s
                        word_txt = chunk["text"]
                        
                        word_data.append({
                            "word": word_txt,
                            "start": start_s,
                            "end": end_s
                        })
                        
                        # Fallback VTT logic (approximate)
                        start_fmt = self._format_vtt_time(start_s)
                        end_fmt = self._format_vtt_time(end_s)
                        vtt_lines.append(f"{start_fmt} --> {end_fmt}\n{word_txt}\n\n")
            
            # Save JSON
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(word_data, f, indent=2)
                
            # Save VTT (Manual Build)
            with open(vtt_filename, "w", encoding="utf-8") as f:
                f.writelines(vtt_lines)
                
            print(f"Saved Metadata: {json_filename} (Items: {len(word_data)})")
            
            # Use JSON if populated, otherwise True Fallback (CLI)
            if len(word_data) > 0:
                return output_abs, json_filename
            else:
                print("Warning: No WordTimestamp events capture (Empty JSON). Engaging CLI Fallback...")
                # The manual VTT is likely empty too. We must regenerate using CLI.
                cmd = [
                    "python", "-m", "edge_tts",
                    "--text", clean_text,
                    "--voice", voice,
                    "--write-media", output_abs,
                    "--write-subtitles", vtt_filename
                ]
                
                # Synchronous subprocess to avoid SelectorLoop issues
                import subprocess
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    print("CLI Fallback Successful. VTT generated.")
                    return output_abs, vtt_filename
                except subprocess.CalledProcessError as e:
                    print(f"CLI Fallback Error: {e.stderr.decode()}")
                    return None
            
        except Exception as e:
            print(f"Error generating audio: {e}")
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
