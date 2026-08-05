"""
chat_manager_tdlib.py
══════════════════════════════════════════════════════════════
إدارة المحادثات والرسائل عبر TDLib
يُكمِّل وظائف Telethon الحالية بدلاً من استبدالها
══════════════════════════════════════════════════════════════
"""

import logging
from typing import Optional, List

from config_tdlib import tdlib_manager

logger = logging.getLogger(__name__)


class ChatManagerTDLib:
    """إدارة المحادثات والرسائل عبر TDLib."""

    def __init__(self, user_id: str):
        self.user_id = user_id

    def _send(self, query: dict) -> bool:
        return tdlib_manager.send(self.user_id, query)

    # ── جلب المحادثات ────────────────────────────────────────────
    def load_chats(self, limit: int = 100) -> bool:
        """طلب جلب قائمة المحادثات الرئيسية."""
        return self._send({
            "@type": "getChats",
            "chat_list": {"@type": "chatListMain"},
            "limit": limit,
        })

    def get_chat(self, chat_id: int) -> bool:
        """جلب تفاصيل محادثة معيّنة."""
        return self._send({"@type": "getChat", "chat_id": chat_id})

    # ── جلب الرسائل ──────────────────────────────────────────────
    def load_messages(
        self,
        chat_id: int,
        limit: int = 50,
        from_message_id: int = 0,
    ) -> bool:
        """جلب تاريخ رسائل محادثة."""
        return self._send({
            "@type": "getChatHistory",
            "chat_id": chat_id,
            "from_message_id": from_message_id,
            "offset": 0,
            "limit": limit,
        })

    # ── إرسال الرسائل ────────────────────────────────────────────
    def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: int = 0,
    ) -> bool:
        """إرسال رسالة نصية."""
        query: dict = {
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessageText",
                "text": {"@type": "formattedText", "text": text},
            },
        }
        if reply_to_message_id:
            query["reply_to_message_id"] = reply_to_message_id
        return self._send(query)

    def send_photo(self, chat_id: int, file_path: str, caption: str = "") -> bool:
        """إرسال صورة من ملف محلي."""
        return self._send({
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessagePhoto",
                "photo": {"@type": "inputFileLocal", "path": file_path},
                "caption": {"@type": "formattedText", "text": caption},
            },
        })

    # ── تعديل وحذف الرسائل ───────────────────────────────────────
    def edit_message(self, chat_id: int, message_id: int, new_text: str) -> bool:
        return self._send({
            "@type": "editMessageText",
            "chat_id": chat_id,
            "message_id": message_id,
            "input_message_content": {
                "@type": "inputMessageText",
                "text": {"@type": "formattedText", "text": new_text},
            },
        })

    def delete_message(
        self, chat_id: int, message_id: int, revoke: bool = True
    ) -> bool:
        return self._send({
            "@type": "deleteMessages",
            "chat_id": chat_id,
            "message_ids": [message_id],
            "revoke": revoke,
        })

    # ── البحث عن محادثة عامة (username/link) ────────────────────
    def search_public_chat(self, username: str) -> bool:
        """البحث عن محادثة عامة بالاسم أو الرابط."""
        clean = username.replace("https://t.me/", "").replace("@", "").strip()
        return self._send({"@type": "searchPublicChat", "username": clean})

    # ── الانضمام إلى مجموعة ──────────────────────────────────────
    def join_chat_by_invite_link(self, invite_link: str) -> bool:
        return self._send({
            "@type": "joinChatByInviteLink",
            "invite_link": invite_link,
        })

    def join_chat(self, chat_id: int) -> bool:
        return self._send({"@type": "joinChat", "chat_id": chat_id})

    # ── تنسيق الرسائل الواردة ────────────────────────────────────
    @staticmethod
    def format_message(message: dict) -> dict:
        """تحويل كائن رسالة TDLib إلى تنسيق موحّد."""
        content = message.get("content", {})
        text = ""
        if content.get("@type") == "messageText":
            text = content.get("text", {}).get("text", "")
        elif content.get("@type") == "messagePhoto":
            text = content.get("caption", {}).get("text", "[صورة]")
        elif content.get("@type") == "messageDocument":
            text = "[ملف]"
        elif content.get("@type") == "messageSticker":
            text = "[ملصق]"
        else:
            text = f"[{content.get('@type', 'رسالة')}]"

        sender = message.get("sender_id", {})
        sender_id = sender.get("user_id") or sender.get("chat_id")

        return {
            "id":          message.get("id"),
            "chat_id":     message.get("chat_id"),
            "sender_id":   sender_id,
            "text":        text,
            "date":        message.get("date"),
            "is_outgoing": message.get("is_outgoing", False),
            "raw":         message,
        }
