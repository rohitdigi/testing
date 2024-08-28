# test.py

import requests
import json

API_URL = 'http://localhost:8000/execute-command/'

def send_command(command):
    headers = {'Content-Type': 'application/json'}
    data = {'command': command}
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Raise HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except ValueError as e:
        print(f"JSON decode error: {e}")
    return None

if __name__ == "__main__":
    command = input("Enter the command to execute: ")
    result = send_command(command)
    if result:
        print("API Response:", result)
    else:
        print("No response or error occurred.")
