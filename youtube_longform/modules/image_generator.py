from google import genai
from google.genai import types
from openai import OpenAI
from youtube_longform.config import GEMINI_API_KEY, OPENAI_API_KEY
from PIL import Image
from io import BytesIO
import requests

class ImageGenerator:
    def __init__(self):
        self.gemini_client = None
        self.client = None
        if GEMINI_API_KEY:
             self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
             self.client = self.gemini_client
        
        self.openai_client = None
        if OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)

    def generate_image(self, prompt, output_filename):
        """
        Generates image using Configured Provider (Default: Pollinations - Free).
        """
        from youtube_longform.config import IMAGE_PROVIDER
        
        print(f"Generating Image ({IMAGE_PROVIDER}): {prompt[:50]}...")
        
        if IMAGE_PROVIDER == "POLLINATIONS":
            return self._generate_pollinations(prompt, output_filename)
        elif IMAGE_PROVIDER == "OPENAI":
             return self._generate_dalle(prompt, output_filename)
        elif IMAGE_PROVIDER == "GEMINI":
             return self._generate_gemini(prompt, output_filename)
        
        # Fallback
        self._create_placeholder(output_filename, prompt)
        return True

    def _generate_pollinations(self, prompt, output_path):
        """
        Uses Pollinations.ai (Free, No Key).
        URL: https://image.pollinations.ai/prompt/{prompt}?width=1920&height=1080&nologo=true
        """
        try:
            # URL Encode prompt
            import urllib.parse
            encoded_prompt = urllib.parse.quote(prompt[:200]) # Keep it reasonably short
            
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&model=flux"
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                print(f"Pollinations Error: {response.status_code}")
                return False
        except Exception as e:
            print(f"Pollinations Failed: {e}")
            return False

    def _generate_gemini(self, prompt, output_path):
        try:
            print(f"Generating Image (Gemini - Nano Banana / 2.5 Flash)...")
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image", 
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["Image"],
                    image_config=types.ImageConfig(
                         aspect_ratio="16:9"
                    )
                )
            )
            
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image = Image.open(BytesIO(part.inline_data.data))
                    image.save(output_path)
                    return True
            return False
        except Exception as e:
            print(f"Gemini Gen Failed: {e}")
            return False

        # 2. Try OpenAI DALL-E 3
        if self.openai_client:
            print("Falling back to DALL-E 3...")
            try:
                response = self.openai_client.images.generate(
                    model="dall-e-3",
                    prompt=full_prompt,
                    size="1024x1024", # DALL-E 3 landscape not always supported in standard tier? 
                    # standard is 1024x1024. 'dall-e-3' supports '1024x1792' (portrait) or '1792x1024' (landscape)?
                    # Let's try standard 1024x1024 and crop, or assume HD.
                    quality="standard",
                    n=1,
                )
                
                image_url = response.data[0].url
                import requests
                img_data = requests.get(image_url).content
                with open(output_filename, 'wb') as handler:
                    handler.write(img_data)
                return True
                
            except Exception as e:
                print(f"DALL-E 3 Gen Failed: {e}")

        # 3. Fallback
        print("Using fallback placeholder...")
        self._create_placeholder(output_filename, prompt)
        return True

    def _create_placeholder(self, filename, prompt):
        """Creates a blue placeholder image with text"""
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (1920, 1080), color = (73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((50,50), f"Placeholder: {prompt[:100]}", fill=(255,255,0))
        img.save(filename)
