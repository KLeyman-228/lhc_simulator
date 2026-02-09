import httpx
from django.conf import settings


def _api_base() -> str:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in Django settings")
    return f"https://api.telegram.org/bot{token}"


def _support_chat_id():
    chat_id = getattr(settings, "TELEGRAM_SUPPORT_CHAT_ID", None)
    if not chat_id:
        raise RuntimeError("TELEGRAM_SUPPORT_CHAT_ID is not set in Django settings")
    return chat_id


async def create_topic(name: str) -> int | None:
    """
    Создать топик (тему) в группе поддержки.
    Возвращает message_thread_id.
    """
    api = _api_base()
    chat_id = _support_chat_id()

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{api}/createForumTopic", json={
            "chat_id": chat_id,
            "name": name,
        })
        data = resp.json()
        if data.get("ok"):
            return data["result"]["message_thread_id"]
    return None


async def send_to_telegram(text: str, topic_id: int) -> bool:
    """Отправить сообщение в конкретный топик группы."""
    api = _api_base()
    chat_id = _support_chat_id()

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{api}/sendMessage", json={
            "chat_id": chat_id,
            "message_thread_id": topic_id,
            "text": text,
            "parse_mode": "HTML",
        })
        return resp.json().get("ok", False)


def send_to_telegram_sync(text: str, topic_id: int) -> bool:
    """Синхронная версия (для Django views)."""
    api = _api_base()
    chat_id = _support_chat_id()

    with httpx.Client(timeout=10) as client:
        resp = client.post(f"{api}/sendMessage", json={
            "chat_id": chat_id,
            "message_thread_id": topic_id,
            "text": text,
            "parse_mode": "HTML",
        })
        return resp.json().get("ok", False)


def set_webhook(url: str) -> bool:
    """Установить webhook для бота."""
    api = _api_base()

    with httpx.Client(timeout=10) as client:
        resp = client.post(f"{api}/setWebhook", json={
            "url": url,
            "allowed_updates": ["message"],
        })
        data = resp.json()
        print(f"setWebhook: {data}")
        return data.get("ok", False)


def delete_webhook() -> bool:
    api = _api_base()
    with httpx.Client(timeout=10) as client:
        resp = client.post(f"{api}/deleteWebhook")
        return resp.json().get("ok", False)