import edge_tts
import asyncio
import json
import os
from openai import OpenAI
from youtube_longform.config import TTS_VOICE, TTS_PROVIDER, OPENAI_API_KEY
from moviepy.editor import AudioFileClip

class AudioGenerator:
    def __init__(self):
        self.provider = TTS_PROVIDER
        self.voice = TTS_VOICE
        self.openai_client = None
        if self.provider == "OPENAI":
             self.openai_client = OpenAI(api_key=OPENAI_API_KEY)

    async def generate_narration(self, text, output_file):
        """
        Generates audio via EdgeTTS, OpenAI, or HF Inference.
        Returns: (audio_path, json_path, srt_path, duration)
        """
        if self.provider == "OPENAI":
            return await self._generate_openai_narration(text, output_file)
        elif self.provider == "HF_INFERENCE":
            return await self._generate_hf_inference(text, output_file)
        else:
            return await self._generate_edge_narration(text, output_file)

    async def _generate_hf_inference(self, text, output_file):
        # Fallback/Experimental HF Inference (using generic model if not specified)
        # Better to stick to EdgeTTS for quality, but here is the logic.
        # We will use 'facebook/mms-tts-eng' or similar which is fast.
        # Or 'microsoft/speecht5_tts' (requires embeddings, complex via API).
        # Let's use a simple distinct model if possible or just log and fallback.
        print("HF Inference TTS requested. Warning: Rate limits/Quality variance.")
        # Actually, let's look for a direct robust endpoint or just perform EdgeTTS override
        # since Edge IS free and high quality. 
        # For now, let's map HF_INFERENCE to EdgeTTS with a specific 'HuggingFace-like' disclaimer
        # OR implement 'HuggingFace Spaces' via gradio_client if installed? No.
        # Let's fallback to EdgeTTS for reliability but print a message.
        print("HF Inference API for TTS is unstable/limited. Redirecting to EdgeTTS (Deep Voice).")
        return await self._generate_edge_narration(text, output_file)

    async def _generate_openai_narration(self, text, output_file):
        abs_output = os.path.abspath(output_file)
        base = os.path.splitext(abs_output)[0]
        json_output = f"{base}.json"
        
        print(f"Generating Narration (OpenAI - {self.voice})...")
        
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1-hd",
                voice=self.voice,
                input=text
            )
            response.stream_to_file(abs_output)
            
            # Estimate Duration
            duration = 0
            if os.path.exists(abs_output):
                clip = AudioFileClip(abs_output)
                duration = clip.duration
                clip.close()
            
            # ESTIMATE Timestamps (Linear)
            words = text.split()
            time_per_word = duration / max(len(words), 1)
            
            word_data = []
            current_time = 0.0
            for word in words:
                end_time = current_time + time_per_word
                word_data.append({
                    "word": word,
                    "start": current_time,
                    "end": end_time
                })
                current_time = end_time
                
            # Save Timing (JSON)
            with open(json_output, "w", encoding="utf-8") as f:
                json.dump(word_data, f, indent=2)

            # Save Timing (SRT)
            srt_output = f"{base}.srt"
            self._write_srt(word_data, srt_output)
            
            return abs_output, json_output, srt_output, duration
            
        except Exception as e:
            print(f"OpenAI TTS Failed: {e}")
            return None

    async def _generate_edge_narration(self, text, output_file):
        """
        Original EdgeTTS logic.
        """
        # File paths
        abs_output = os.path.abspath(output_file)
        base = os.path.splitext(abs_output)[0]
        json_output = f"{base}.json"
        
        # Directory check
        os.makedirs(os.path.dirname(abs_output), exist_ok=True)
        
        communicate = edge_tts.Communicate(text, self.voice)
        word_data = []
        
        print(f"Generating Narration ({len(text)} chars)...")
        
        with open(abs_output, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    word_data.append({
                        "word": chunk["text"],
                        "start": chunk["offset"] / 1e7,
                        "end": (chunk["offset"] + chunk["duration"]) / 1e7
                    })
                    
        # Save Timing (JSON)
        with open(json_output, "w", encoding="utf-8") as f:
            json.dump(word_data, f, indent=2)

        # Save Timing (SRT)
        srt_output = f"{base}.srt"
        self._write_srt(word_data, srt_output)
            
        # Get Duration
        duration = 0
        if word_data:
            duration = word_data[-1]['end']
        elif os.path.exists(abs_output) and os.path.getsize(abs_output) > 0:
            # Fallback: Estimate timings
            try:
                clip = AudioFileClip(abs_output)
                duration = clip.duration
                clip.close()
                
                words = text.split()
                if words:
                    char_dur = duration / len(text) if len(text) > 0 else 0.1
                    current_time = 0
                    for w in words:
                        # Simple estimation: each word proportional to length? 
                        # Or equal? Equal is safer for now.
                        w_dur = duration / len(words)
                        word_data.append({
                            "word": w,
                            "start": current_time,
                            "end": current_time + w_dur
                        })
                        current_time += w_dur
                            
                # Re-save JSON/SRT with estimates
                with open(json_output, "w", encoding="utf-8") as f:
                    json.dump(word_data, f, indent=2)
                self._write_srt(word_data, srt_output)
            except Exception as e:
                print(f"Estimation failed: {e}")
            
        return abs_output, json_output, srt_output, duration

    def _write_srt(self, word_data, output_file):
        def fmt(seconds):
            ms = int((seconds % 1) * 1000)
            s = int(seconds) % 60
            m = int(seconds // 60) % 60
            h = int(seconds // 3600)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        with open(output_file, "w", encoding="utf-8") as f:
            for i, w in enumerate(word_data):
                start = fmt(w['start'])
                end = fmt(w['end'])
                f.write(f"{i+1}\n{start} --> {end}\n{w['word']}\n\n")
