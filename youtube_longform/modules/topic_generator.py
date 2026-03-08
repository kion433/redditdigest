import json
from openai import OpenAI
from youtube_longform.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME

class TopicGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        self.model = LLM_MODEL_NAME

    def generate_topics(self, domain, count=5):
        """
        Generates a list of intriguing, unknown, or deep-dive topics within a domain.
        """
        system_prompt = f"""You are a documentary researcher for a high-end YouTube channel.
        The channel focuses on "The Unknown", "Deep Dives", and "Hidden History".
        
        Your goal is to suggest {count} unique, specific, and fascinating topics within the domain of '{domain}'.
        Avoid generic topics (e.g., "History of Psychology"). Go for specific, story-driven angles.
        
        Output JSON format:
        {{
            "topics": [
                {{
                    "title": "The Monster Study: When Science Went Too Far",
                    "premise": "A deep dive into the 1939 stuttering experiment on orphans...",
                    "visual_style": "Noir, gritty, archival footage style"
                }},
                ...
            ]
        }}
        """

        try:
            print(f"Brainstorming topics for domain: {domain}...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Give me {count} masterpiece ideas for '{domain}'."}
                ],
                response_format={ "type": "json_object" }
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            data = json.loads(content)
            return data.get("topics", [])
        except Exception as e:
            print(f"Error generating topics: {e}")
            return []
