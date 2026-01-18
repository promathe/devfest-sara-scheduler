import requests
import json

url = 'http://localhost:8000/chat'
data = {
    'messages': [{'role': 'user', 'content': 'Schedule a meeting tomorrow at 10 AM'}],
    'user_token': 'test_token',
    'current_time': '2024-01-15T09:00:00+05:30',
    'user_timezone': 'Asia/Calcutta'
}

try:
    response = requests.post(url, json=data, timeout=10)
    print('Status Code:', response.status_code)
    print('Response:', response.json())
except Exception as e:
    print('Error:', e)