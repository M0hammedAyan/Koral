"""
Quick test for the OpenRouter / OpenAI API key.
Run: python test_api_key.py
"""
import httpx
import os

# Read key from .env.example directly for testing
KEY = ""
try:
    with open(".env.example") as f:
        for line in f:
            if line.startswith("OPENAI_API_KEY="):
                KEY = line.split("=", 1)[1].strip()
                break
except FileNotFoundError:
    pass

if not KEY:
    KEY = os.getenv("OPENAI_API_KEY", "")

if not KEY:
    print("ERROR: No API key found in .env.example or environment")
    exit(1)

print(f"Key found: {KEY[:12]}...{KEY[-6:]}")

# Detect endpoint based on key prefix
if KEY.startswith("sk-or-"):
    BASE_URL = "https://openrouter.ai/api/v1"
    MODEL    = "openai/gpt-4o"
    print("Key type  : OpenRouter")
    print(f"Endpoint  : {BASE_URL}")
else:
    BASE_URL = "https://api.openai.com/v1"
    MODEL    = "gpt-4o"
    print("Key type  : OpenAI Direct")
    print(f"Endpoint  : {BASE_URL}")

print(f"Model     : {MODEL}")
print("\nSending test message...\n")

try:
    r = httpx.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://koral.ai",
            "X-Title": "KORAL",
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are KORAL AI, a Kubernetes assistant."},
                {"role": "user",   "content": "Say hello and confirm you are working. One sentence only."},
            ],
            "max_tokens": 60,
        },
        timeout=20,
    )

    if r.status_code == 200:
        data = r.json()
        reply = data["choices"][0]["message"]["content"].strip()
        print("[OK] API KEY WORKS")
        print(f"Response : {reply}")
        print(f"Model    : {data.get('model', MODEL)}")
    else:
        print(f"[FAIL] HTTP {r.status_code}")
        print(r.text)

except Exception as e:
    print(f"[FAIL] {e}")
