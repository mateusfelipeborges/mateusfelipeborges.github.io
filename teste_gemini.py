import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"


headers = {
    "Content-Type": "application/json"
}

data = {
    "contents": [
        {
            "parts": [
                {"text": "Quem é você?"}
            ]
        }
    ]
}

response = requests.post(url, headers=headers, json=data)

print("Status:", response.status_code)
print("Resposta:")
print(response.text)
