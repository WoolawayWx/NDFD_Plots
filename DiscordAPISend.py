import requests

BOT_SERVER_URL = "http://localhost:3000/notify"

def notify_bot():
    data = {"message": "Python Test Script"}
    response = requests.post(BOT_SERVER_URL, json=data)
    if response.status_code == 200:
        print("Notification sent successfully")
    else: 
        print("Failed to send notification") 

import time
print("Processing...")
time.sleep(120)

notify_bot()