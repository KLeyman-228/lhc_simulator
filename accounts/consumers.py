import json
import time
from channels.generic.websocket import AsyncWebsocketConsumer

from . import memory_store as store
from . import telegram_service as tg


class SupportConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        await self.accept()

        store.set_channel(self.session_id, self.channel_name)

        messages = store.get_messages(self.session_id)
        if messages:
            await self.send(text_data=json.dumps({
                "type": "history",
                "messages": messages,
            }))

        await self.send(text_data=json.dumps({
            "type": "system",
            "text": "Чат поддержки подключён. Напишите ваш вопрос!",
        }))

    async def disconnect(self, close_code):
        store.remove_channel(self.session_id)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        text = (data.get("text") or "").strip()
        if not text:
            return

        user_name = data.get("user_name") or "Гость"

        session = store.get_session(self.session_id)
        if not session:
            session = store.create_session(self.session_id, user_name)

        if not session.topic_id:
            topic_name = f"💬 {user_name} ({self.session_id[:8]})"
            topic_id = await tg.create_topic(topic_name)
            if not topic_id:
                await self.send(text_data=json.dumps({
                    "type": "system",
                    "text": "Ошибка подключения к поддержке. Попробуйте позже.",
                }))
                return

            store.link_topic(self.session_id, topic_id)
            session.topic_id = topic_id

        # сохраняем для истории
        store.add_message(self.session_id, "user", text)

        # ✅ В TG отправляем красиво и всегда с [WEB]
        ok = await tg.send_to_telegram(text, session.topic_id, user_name)

        # если Telegram не принял — покажем системку (чтобы ты видел проблему)
        if not ok:
            await self.send(text_data=json.dumps({
                "type": "system",
                "text": "Telegram не принял сообщение (см. логи сервера).",
            }))

        # ❌ НЕ шлём это же сообщение назад на сайт (ты рисуешь его на фронте)
        return

    async def support_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "message",
            "sender": "support",
            "text": event["text"],
            "timestamp": event.get("timestamp", time.time()),
        }))
