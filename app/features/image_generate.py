import requests
from g4f.client import Client

def generate_image(prompt: str) -> str:
    try:
        client = Client()
        response = client.images.generate(
            model="flux",
            prompt=prompt,
            response_format="url"
        )

        image_url = response.data[0].url
        print(f"[SUCCESS] Generated image URL: {image_url}")
        return image_url

    except Exception as e:
        print(f"[ERROR] Could not generate image: {e}")
        return None


