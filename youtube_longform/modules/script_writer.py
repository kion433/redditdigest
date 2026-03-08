import json
from openai import OpenAI
from youtube_longform.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME

class ScriptWriter:
    def __init__(self):
        self.client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        self.model = LLM_MODEL_NAME

    def generate_detailed_script(self, topic_data, num_chapters=5):
        """
        Generates a full video script with `num_chapters`.
        """
        print(f"Generating script for: {topic_data['title']} ({num_chapters} chapters)...")
        
        # 1. Outline Generation
        outline = self._generate_outline(topic_data, num_chapters)
        if not outline:
            return None
            
        # Strict enforcement: Slice outline if LLM returned too many
        outline = outline[:num_chapters]
            
        # 2. Chapter Generation
        full_script = []
        previous_context = ""
        
        for i, chapter in enumerate(outline):
            print(f"  Writing Chapter {i+1}/{len(outline)}: {chapter['title']}...")
            chapter_content = self._write_chapter(topic_data, chapter, previous_context)
            if chapter_content:
                full_script.append(chapter_content)
                # Update context for next chapter continuity
                all_text = " ".join([seg['text'] for seg in chapter_content.get('segments', [])])
                previous_context = all_text[-500:] # Keep last 500 chars
                
        return {
            "title": topic_data['title'],
            "chapters": full_script
        }

    def _generate_outline(self, topic, num_chapters):
        system_prompt = f"""You are a master storyteller and documentary planner.
        Create a {num_chapters}-chapter outline for a documentary.
        
        Flow:
        1. The Hook / Mystery
        2. The Context / History
        3. The Conflict / Climax
        4. The Resolution / Aftermath
        5. The Modern Relevance / Conclusion
        
        Output JSON:
        [
            {{
                "title": "Chapter 1: The Vanishing",
                "focus": "Introduce the event..."
            }},
            ...
        ]
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Topic: {topic['title']}\nPremise: {topic['premise']}"}
                ],
                response_format={ "type": "json_object" } # Ensure model supports this or parse manually
            )
            # Handle potential non-JSON output wrappers
            content = response.choices[0].message.content
            # Quick cleanup if wrapped in markdown
            if "```json" in content:
                 content = content.split("```json")[1].split("```")[0]
                 
            data = json.loads(content)
            return data if isinstance(data, list) else data.get('chapters', [])
        except Exception as e:
            print(f"Error generating outline: {e}")
            return None

    def _write_chapter(self, topic, chapter, context):
        system_prompt = f"""You are writing the script for a high-production documentary.
        Topic: {topic['title']}
        Current Chapter: {chapter['title']}
        
        Tone: Cinematic, engaging, educational, slightly dramatic (like "Lemmino" or "Barely Sociable").
        
        Instructions:
        - Write about 300-400 words of narration.
        - Break text into chunks of 2-3 sentences.
        - For EACH chunk, suggest a "Renaissance Style Painting" prompt that visualizes the narration.
        
        Output JSON:
        {{
            "title": "{chapter['title']}",
            "segments": [
                {{
                    "text": "In the winter of 1939, the orphanage stood silent...",
                    "image_prompt": "Oil painting of a gloomy orphanage in winter, 1939, gothic style, muted colors, cinematic lighting"
                }},
                ...
            ]
        }}
        """
        
        user_msg = f"Write the script. Focus: {chapter['focus']}."
        if context:
            user_msg += f"\nPrevious context: ...{context}"
            
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                response_format={ "type": "json_object" }
            )
            content = response.choices[0].message.content
            if "```json" in content:
                 content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except Exception as e:
            print(f"Error writing chapter: {e}")
            return None
