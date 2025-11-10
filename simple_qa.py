import os
import sqlite3
import yaml
import json
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def load_data():
    context = ""
    for f in ["metadata.yaml", "policy.yaml"]:
        if os.path.exists(f):
            with open(f, "r") as file:
                context += f"\n# {f}\n{file.read()}\n"
    
    try:
        conn = sqlite3.connect("governance.db")
        rows = conn.execute("SELECT * FROM validation_logs LIMIT 50").fetchall()
        conn.close()
        if rows:
            context += "\nValidation Issues:\n"
            for r in rows:
                context += f"- Column '{r[2]}' had issue: {r[5]}\n"
    except:
        context += "\nNo validation logs found.\n"
    
    return context

def ask_gemini(question):
    context = load_data()
    
    # Use one of the working models from your list
    model = "models/gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": f"You are a Data Governance Copilot. Use the provided context to answer clearly and concisely.\n\nContext: {context}\n\nQuestion: {question}"}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048
        }
    }
    
    try:
        print(f"🤖 Using {model}...")
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"❌ API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"❌ Error: {e}"

if __name__ == "__main__":
    print("🚀 Data Governance QA - Working Version!")
    answer = ask_gemini("Summarize all PII columns and masking policies from the provided data.")
    print(f"\n💬 Answer:\n{answer}")