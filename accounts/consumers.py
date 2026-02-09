import json
import time
from channels.generic.websocket import AsyncWebSocketConsumer
from . import memory_store as store
from . import telegram_service as tg


class SupportConsumer(AsyncWebSocketConsumer):

    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        await self.accept()

        # Сохраняем channel_name для отправки из webhook
        store.set_channel(self.session_id, self.channel_name)

        # Отправляем историю, если есть
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

        text = data.get("text", "").strip()
        if not text:
            return

        user_name = data.get("user_name", "Гость")

        # Получить или создать сессию
        session = store.get_session(self.session_id)
        if not session:
            session = store.create_session(self.session_id, user_name)

        # Создать топик в Telegram, если ещё нет
        if not session.topic_id:
            topic_name = f"💬 {user_name} ({self.session_id[:8]})"
            topic_id = await tg.create_topic(topic_name)
            if topic_id:
                store.link_topic(self.session_id, topic_id)
                session.topic_id = topic_id
            else:
                await self.send(text_data=json.dumps({
                    "type": "system",
                    "text": "Ошибка подключения к поддержке. Попробуйте позже.",
                }))
                return

        # Сохраняем в память
        msg = store.add_message(self.session_id, "user", text)

        # Отправляем в Telegram
        tg_text = f"<b>{user_name}:</b>\n{text}"
        await tg.send_to_telegram(tg_text, session.topic_id)

        # Подтверждаем пользователю
        await self.send(text_data=json.dumps({
            "type": "message",
            "sender": "user",
            "text": text,
            "timestamp": msg["timestamp"],
        }))

    async def support_message(self, event):

        await self.send(text_data=json.dumps({
            "type": "message",
            "sender": "support",
            "text": event["text"],
            "timestamp": event.get("timestamp", time.time()),
        }))