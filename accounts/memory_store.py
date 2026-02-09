import time
import threading
from dataclasses import dataclass, field


@dataclass
class ChatSession:
    session_id: str
    topic_id: int | None = None          # message_thread_id в Telegram
    user_name: str = "Гость"
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    messages: list = field(default_factory=list)


# ──────────────────────── Хранилище ───────────────────────────

_sessions: dict[str, ChatSession] = {}           # session_id → ChatSession
_topic_to_session: dict[int, str] = {}            # topic_id → session_id
_channel_names: dict[str, str] = {}               # session_id → channel_name (WS)
_lock = threading.Lock()

SESSION_TTL = 60 * 60 * 24  # 24 часа


def _cleanup():
    """Удалить просроченные сессии."""
    now = time.time()
    with _lock:
        expired = [
            sid for sid, s in _sessions.items()
            if now - s.last_activity > SESSION_TTL
        ]
        for sid in expired:
            s = _sessions.pop(sid, None)
            if s and s.topic_id:
                _topic_to_session.pop(s.topic_id, None)
            _channel_names.pop(sid, None)


# ─────────────────── Публичное API ────────────────────────────

def create_session(session_id: str, user_name: str = "Гость") -> ChatSession:
    _cleanup()
    with _lock:
        if session_id in _sessions:
            return _sessions[session_id]
        session = ChatSession(session_id=session_id, user_name=user_name)
        _sessions[session_id] = session
        return session


def get_session(session_id: str) -> ChatSession | None:
    with _lock:
        s = _sessions.get(session_id)
        if s:
            s.last_activity = time.time()
        return s


def get_session_by_topic(topic_id: int) -> ChatSession | None:
    with _lock:
        sid = _topic_to_session.get(topic_id)
        if sid:
            return _sessions.get(sid)
    return None


def link_topic(session_id: str, topic_id: int):
    with _lock:
        if session_id in _sessions:
            _sessions[session_id].topic_id = topic_id
            _topic_to_session[topic_id] = session_id


def add_message(session_id: str, sender: str, text: str) -> dict:
    """sender: 'user' или 'support'"""
    msg = {
        "sender": sender,
        "text": text,
        "timestamp": time.time(),
    }
    with _lock:
        s = _sessions.get(session_id)
        if s:
            s.messages.append(msg)
            s.last_activity = time.time()
    return msg


def get_messages(session_id: str) -> list[dict]:
    with _lock:
        s = _sessions.get(session_id)
        return list(s.messages) if s else []


# ── Маппинг session_id ↔ WebSocket channel_name ──

def set_channel(session_id: str, channel_name: str):
    with _lock:
        _channel_names[session_id] = channel_name


def get_channel(session_id: str) -> str | None:
    with _lock:
        return _channel_names.get(session_id)


def remove_channel(session_id: str):
    with _lock:
        _channel_names.pop(session_id, None)