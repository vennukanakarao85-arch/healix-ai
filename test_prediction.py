import requests
import json

url = "http://127.0.0.1:5000/predict"
payload = {
    "message": "मुझे बहुत प्यास लग रही है और थकान महसूस हो रही है",
    "language": "hi-IN",
    "age": 50,
    "bmi": 30,
    "bp": 140,
    "glucose": 150,
    "chol": 240,
    "max_heart_rate": 120,
    "questionnaire": {"thirst": 1, "fatigue": 1}
}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
