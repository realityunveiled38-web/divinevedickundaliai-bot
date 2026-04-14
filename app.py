import os
import json
import logging
from fastapi import FastAPI, Request, HTTPException
import requests
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
QWEN_API_KEY = os.getenv("OPENROUTER_API_KEY")
PORT = int(os.getenv("PORT", 8000))

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

SYSTEM_PROMPT = """You are a 100+ years experienced Vedic astrologer. You speak in Hinglish. You give deep and accurate predictions based on astrology and numerology. Always structure your answers in: Past, Present, Future, and Remedies. Be confident and detailed."""


@app.get("/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = None,
    hub_challenge: Optional[str] = None,
    hub_verify_token: Optional[str] = None
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("✅ Webhook verified!")
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Forbidden")


@app.post("/webhook")
async def receive_message(request: Request):
    try:
        body = await request.json()
        logger.info(f"Received webhook: {json.dumps(body)}")

        if "entry" not in body or not body["entry"]:
            return {"status": "ok"}

        entry = body["entry"][0]
        if "changes" not in entry or not entry["changes"]:
            return {"status": "ok"}

        change = entry["changes"][0]
        if "value" not in change or "messages" not in change["value"]:
            return {"status": "ok"}

        messages = change["value"]["messages"]
        if not messages:
            return {"status": "ok"}

        message = messages[0]
        sender_phone = message.get("from")

        if message.get("type") != "text":
            return {"status": "ok"}

        user_message = message.get("text", {}).get("body", "")
        if not user_message:
            return {"status": "ok"}

        logger.info(f"Message from {sender_phone}: {user_message}")

        ai_response = await get_ai_response(user_message)
        await send_whatsapp_message(sender_phone, ai_response)

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"status": "error"}


async def get_ai_response(user_message: str) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {QWEN_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen/qwen2.5-7b-instruct",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 2000
        }
        response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"AI Error: {str(e)}")
        return "🙏 क्षमा करें, मैं आपका प्रश्न प्रोसेस नहीं कर सका। कृपया पुनः प्रयास करें।"


async def send_whatsapp_message(phone_number: str, message_text: str) -> bool:
    try:
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message_text}
        }
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(f"✅ Message sent to {phone_number}")
        return True
    except Exception as e:
        logger.error(f"WhatsApp Error: {str(e)}")
        return False


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "🙏 DivineVedic AI Bot is running!",
        "webhook": "/webhook"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "services": {
            "qwen_configured": bool(QWEN_API_KEY),
            "whatsapp_configured": bool(WHATSAPP_TOKEN and PHONE_NUMBER_ID)
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
