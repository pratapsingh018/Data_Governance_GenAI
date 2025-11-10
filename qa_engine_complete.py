import os
import sqlite3
import yaml
from dotenv import load_dotenv

try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    print("❌ google-generativeai not available. Install with: pip install google-generativeai")
    GOOGLE_AI_AVAILABLE = False

# -----------------
# Load environment
# -----------------
load_dotenv()  # loads GEMINI_API_KEY from .env

# Check if API key is available
api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "AIzaSyCuwKr7FBx9gXzchTCzCeaJp-eCkHhcE_o":
    print("❌ Please set your GEMINI_API_KEY in the .env file")
    print("   Get your API key from: https://aistudio.google.com/app/apikey")
    exit(1)

# Configure the API
if GOOGLE_AI_AVAILABLE:
    genai.configure(api_key=api_key)

# -----------------
# Load YAML metadata and policy
# -----------------
def load_yaml_texts():
    texts = []
    for f in ["metadata.yaml", "policy.yaml"]:
        if os.path.exists(f):
            with open(f, "r") as file:
                texts.append(f"# {f}\n" + file.read())
        else:
            print(f"⚠️  Warning: {f} not found")
    return "\n".join(texts)

# -----------------
# Load validation logs
# -----------------
def load_validation_texts():
    try:
        conn = sqlite3.connect("governance.db")
        rows = conn.execute("SELECT * FROM validation_logs LIMIT 200").fetchall()
        conn.close()
        if rows:
            return "\n".join([f"Column '{r[2]}' failed at row {r[3]} with value '{r[4]}' → {r[5]}" for r in rows])
        else:
            return "No validation failures found."
    except sqlite3.OperationalError:
        return "No validation logs table found. Run validation_engine.py first."
    except Exception as e:
        return f"Error loading validation logs: {e}"

# -----------------
# List available models
# -----------------
def list_available_models():
    if not GOOGLE_AI_AVAILABLE:
        return []
    
    try:
        models = genai.list_models()
        available_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                available_models.append(model.name)
        return available_models
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

# -----------------
# QA using Google Generative AI directly
# -----------------
def qa_with_google_ai(question):
    context = load_yaml_texts() + "\n\n" + load_validation_texts()
    
    if not GOOGLE_AI_AVAILABLE:
        return f"Google Generative AI not available. Here's the raw context:\n\n{context[:1000]}..."
    
    try:
        # List available models
        print("🔍 Checking available models...")
        available_models = list_available_models()
        
        if available_models:
            print("📋 Available models:")
            for model in available_models[:5]:  # Show first 5
                print(f"  - {model}")
            
            # Try to use the first available model
            model_name = available_models[0]
            print(f"🤖 Using model: {model_name}")
            
            model = genai.GenerativeModel(model_name)
            
            prompt = f"""You are a Data Governance Copilot.
Use the provided context to answer clearly and concisely.

Context:
{context}

Question:
{question}

Answer:"""
            
            print("🤖 Generating response...")
            response = model.generate_content(prompt)
            return response.text
            
        else:
            return "❌ No compatible models found."
            
    except Exception as e:
        return f"Error with Google AI: {e}\n\nFallback - Available context:\n{context[:500]}..."

# -----------------
# Run a test query
# -----------------
if __name__ == "__main__":
    print("🚀 Starting Data Governance QA Engine...")
    print("📝 Using Google Generative AI directly (bypassing LangChain)")
    
    # Test if files exist
    print("\n📋 Checking for required files:")
    for filename in ["metadata.yaml", "policy.yaml", "governance.db"]:
        if os.path.exists(filename):
            print(f"  ✅ {filename}")
        else:
            print(f"  ❌ {filename} - missing")
    
    print("\n" + "="*50)
    
    query = "Summarize all PII columns and masking policies."
    print(f"🧠 Q: {query}")
    print("💬 A:", qa_with_google_ai(query))