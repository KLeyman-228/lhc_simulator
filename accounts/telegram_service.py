import httpx
import html
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
    api = _api_base()
    chat_id = _support_chat_id()

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{api}/createForumTopic",
            json={"chat_id": chat_id, "name": name},
        )
        data = resp.json()
        if data.get("ok"):
            return data["result"]["message_thread_id"]

        print("TG createForumTopic failed:", data)
    return None


async def send_to_telegram(text: str, topic_id: int, user_name: str | None = None) -> bool:
    """
    Совместимо с двумя вариантами вызова:
      - send_to_telegram(tg_text, topic_id)
      - send_to_telegram(text, topic_id, user_name)
    Если user_name передан — оформляем красиво.
    Если text уже содержит HTML/префиксы — просто отправляем как есть.
    """
    api = _api_base()
    chat_id = _support_chat_id()

    # Если пришёл user_name — собираем безопасный HTML.
    if user_name is not None:
        safe_name = html.escape(user_name or "Пользователь")
        safe_text = html.escape(text or "")
        tg_text = f"[WEB] <b>{safe_name}:</b>\n{safe_text}"
        parse_mode = "HTML"
    else:
        # Иначе отправляем ровно то, что передали (как раньше)
        tg_text = text or ""
        parse_mode = "HTML"  # можно оставить, раз у тебя так настроено

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{api}/sendMessage",
            json={
                "chat_id": chat_id,
                "message_thread_id": topic_id,
                "text": tg_text,
                "parse_mode": parse_mode,
            },
        )
        data = resp.json()
        if not data.get("ok"):
            print("TG sendMessage failed:", data)
        return data.get("ok", False)
