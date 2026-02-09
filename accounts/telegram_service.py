import httpx
from django.conf import settings

API = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


async def create_topic(name: str) -> int | None:
    """
    Создать топик (тему) в группе поддержки.
    Возвращает message_thread_id.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{API}/createForumTopic", json={
            "chat_id": settings.TELEGRAM_SUPPORT_CHAT_ID,
            "name": name,
        })
        data = resp.json()
        if data.get("ok"):
            return data["result"]["message_thread_id"]
    return None


async def send_to_telegram(text: str, topic_id: int) -> bool:
    """Отправить сообщение в конкретный топик группы."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{API}/sendMessage", json={
            "chat_id": settings.TELEGRAM_SUPPORT_CHAT_ID,
            "message_thread_id": topic_id,
            "text": text,
            "parse_mode": "HTML",
        })
        return resp.json().get("ok", False)


def send_to_telegram_sync(text: str, topic_id: int) -> bool:
    """Синхронная версия (для Django views)."""
    with httpx.Client(timeout=10) as client:
        resp = client.post(f"{API}/sendMessage", json={
            "chat_id": settings.TELEGRAM_SUPPORT_CHAT_ID,
            "message_thread_id": topic_id,
            "text": text,
            "parse_mode": "HTML",
        })
        return resp.json().get("ok", False)


def set_webhook(url: str) -> bool:
    """Установить webhook для бота."""
    with httpx.Client(timeout=10) as client:
        resp = client.post(f"{API}/setWebhook", json={
            "url": url,
            "allowed_updates": ["message"],
        })
        data = resp.json()
        print(f"setWebhook: {data}")
        return data.get("ok", False)


def delete_webhook() -> bool:
    with httpx.Client(timeout=10) as client:
        resp = client.post(f"{API}/deleteWebhook")
        return resp.json().get("ok", False)