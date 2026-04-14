from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import requests
import os

app = FastAPI()

# 🔐 Tokens (yaha apna daalna hai)
VERIFY_TOKEN = "myverify123"
WHATSAPP_TOKEN = "EAAVPWZCGwbnoBRNLnJ43AijC3eXQ56nAGDEBfGYUzP0eDHMlwqUFZAL0eUVMiYQIJiDhZAO9BvrBgGLUDsZBN7vZCagwB8zZAvxVypdOsQvvvmnQpkqiSph5kR3gXIzo2tFCuwNSnpARFO6uCWyLwZAHvCjTw8RodTu1rxBoPz4SO7dofOjMx0okZAzIxDAqfX9JXD2Sr4UNvNrhrTZCEZBGZBmWPAle8nlkfkxzKKZBBC9NPdUGn73yFUUOHjY1s2koIJhxuhT33ZBRYmIZBdnZATqCm7ZBlaRW"
PHONE_NUMBER_ID = "1002070723000831"

# ✅ Health check
@app.get("/")
def home():
    return {"status": "ok", "message": "🚀 DivineVedic AI Bot is running!", "webhook": "/webhook"}


# ✅ Webhook Verification (Meta ke liye)
@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)

    return {"error": "Verification failed"}


# ✅ Webhook Receive Messages
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = message["from"]
        text = message["text"]["body"]

        reply = get_ai_reply(text)

        send_whatsapp_message(sender, reply)

    except Exception as e:
        print("Error:", e)

    return {"status": "ok"}


# 🤖 AI Reply (simple)
def get_ai_reply(user_text):
    return f"🙏 Aapne kaha: {user_text}\n\n🔮 Divine Vedic AI aapki sahayata ke liye yahan hai."


# 📤 Send Message to WhatsApp
def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=data)
    print(response.text)
