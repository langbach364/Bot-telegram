import hmac
import os

import httpx
from fastapi import FastAPI, Header, HTTPException, Request

from coordinates import normalize_coordinates


app = FastAPI()
EXAMPLE = "10,90242° B, 106,59664° Đ"
USAGE = f"Nhắn riêng: {EXAMPLE}\nTrong nhóm: /toado {EXAMPLE}"


def _environment(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise HTTPException(status_code=500, detail=f"Chưa cấu hình {name}")
    return value


async def _set_webhook(url: str, secret: str) -> None:
    token = _environment("TELEGRAM_BOT_TOKEN")
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            f"https://api.telegram.org/bot{token}/setWebhook",
            json={"url": url, "secret_token": secret},
        )
        response.raise_for_status()
        result = response.json()
        if not result.get("ok"):
            raise HTTPException(status_code=502, detail="Telegram từ chối webhook")


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "Bot đang hoạt động"}


@app.get("/setup")
async def setup(request: Request, secret: str) -> dict[str, str]:
    webhook_secret = _environment("WEBHOOK_SECRET")
    if not hmac.compare_digest(secret, webhook_secret):
        raise HTTPException(status_code=403, detail="Khóa thiết lập không đúng")

    webhook_url = str(request.url_for("webhook"))
    await _set_webhook(webhook_url, webhook_secret)
    return {"status": "Đã kết nối bot với Telegram", "webhook": webhook_url}


@app.post("/webhook", name="webhook")
async def webhook(
    update: dict,
    telegram_secret: str | None = Header(
        default=None, alias="X-Telegram-Bot-Api-Secret-Token"
    ),
) -> dict:
    webhook_secret = _environment("WEBHOOK_SECRET")
    if telegram_secret is None or not hmac.compare_digest(
        telegram_secret, webhook_secret
    ):
        raise HTTPException(status_code=403, detail="Yêu cầu không hợp lệ")

    message = update.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("text"), str):
        return {"ok": True}

    text = message["text"].strip()
    chat = message.get("chat", {})
    if text.startswith("/start"):
        reply = USAGE
    else:
        parts = text.split(maxsplit=1)
        command = parts[0].split("@", 1)[0].lower()
        if command == "/toado":
            if len(parts) == 1:
                reply = USAGE
            else:
                text = parts[1]
                try:
                    reply = normalize_coordinates(text)
                except ValueError:
                    reply = f"Không đọc được tọa độ. {USAGE}"
        elif chat.get("type") in {"group", "supergroup"}:
            return {"ok": True}
        else:
            try:
                reply = normalize_coordinates(text)
            except ValueError:
                reply = f"Không đọc được tọa độ. {USAGE}"

    return {
        "method": "sendMessage",
        "chat_id": chat["id"],
        "text": reply,
    }
