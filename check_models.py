import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# List available models
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    response = requests.get(url)
    if response.status_code == 200:
        models = response.json()
        print("📋 Available models:")
        for model in models.get('models', []):
            if 'generateContent' in model.get('supportedGenerationMethods', []):
                print(f"  ✅ {model['name']}")
    else:
        print(f"❌ Error listing models: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Error: {e}")