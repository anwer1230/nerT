"""
sync_handler_tdlib.py
══════════════════════════════════════════════════════════════
نظام المزامنة الآنية عبر TDLib + Socket.IO
يعمل جنباً إلى جنب مع نظام Telethon الحالي
══════════════════════════════════════════════════════════════
"""

import threading
import time
import logging
from typing import Optional

from config_tdlib import tdlib_manager
from chat_manager_tdlib import ChatManagerTDLib

logger = logging.getLogger(__name__)


class TDLibSyncManager:
    """
    يعالج تحديثات TDLib في الخلفية ويبثها عبر Socket.IO.
    مثيل واحد لجميع المستخدمين.
    """
    _instance: Optional["TDLibSyncManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._socketio = None
        self._running  = False
        self._thread: Optional[threading.Thread] = None

    # ── تهيئة مع Socket.IO ───────────────────────────────────────
    def start(self, socketio_instance):
        """يجب استدعاؤه مرة واحدة عند بدء التطبيق."""
        if not tdlib_manager.available:
            logger.info("TDLib غير متاح — SyncManager لن يبدأ")
            return
        self._socketio = socketio_instance
        if not self._running:
            self._running = True
            self._thread  = threading.Thread(
                target=self._worker, daemon=True, name="TDLibSyncWorker"
            )
            self._thread.start()
            logger.info("✅ TDLibSyncManager بدأ")

    def stop(self):
        self._running = False

    # ── حلقة معالجة التحديثات ────────────────────────────────────
    def _worker(self):
        while self._running:
            for client_id, data in list(tdlib_manager.client_data.items()):
                update = tdlib_manager.receive(client_id, timeout=0.1)
                if update:
                    try:
                        self._process(client_id, update)
                    except Exception as e:
                        logger.error(f"TDLibSyncManager process error: {e}")
            time.sleep(0.03)

    def _process(self, client_id: int, update: dict):
        user_id = tdlib_manager.client_data.get(client_id, {}).get("user_id")
        if not user_id:
            return

        utype = update.get("@type", "")

        # ── رسالة جديدة ──────────────────────────────────────────
        if utype == "updateNewMessage":
            msg = update.get("message", {})
            chat_id = msg.get("chat_id")
            fmt = ChatManagerTDLib.format_message(msg)

            self._emit(f"chat_{chat_id}", "new_message", {"message": fmt})
            self._emit(f"user_{user_id}", "chat_list_update", {"chat_id": chat_id})

            # تشغيل معالجات المستخدم المخصصة (auto_reply إلخ)
            handlers = tdlib_manager.client_data.get(client_id, {}).get("handlers", {})
            handler = handlers.get("updateNewMessage")
            if handler:
                try:
                    handler(fmt)
                except Exception as e:
                    logger.error(f"custom handler error: {e}")

        # ── تحديث محادثة ─────────────────────────────────────────
        elif utype == "updateChat":
            chat = update.get("chat", {})
            self._emit(f"user_{user_id}", "chat_update", chat)

        # ── تأكيد إرسال ──────────────────────────────────────────
        elif utype == "updateMessageSendSucceeded":
            msg = update.get("message", {})
            self._emit(f"user_{user_id}", "message_sent", {
                "success":    True,
                "message_id": msg.get("id"),
                "chat_id":    msg.get("chat_id"),
            })

        # ── حالة القراءة ─────────────────────────────────────────
        elif utype == "updateMessageReadHistory":
            self._emit(f"user_{user_id}", "read_history", {
                "chat_id":      update.get("chat_id"),
                "unread_count": update.get("unread_count", 0),
            })

        # ── تحديث المستخدم ───────────────────────────────────────
        elif utype == "updateUser":
            self._emit(f"user_{user_id}", "user_update", update.get("user", {}))

    def _emit(self, room: str, event: str, data: dict):
        if self._socketio:
            try:
                self._socketio.emit(event, data, room=room)
            except Exception as e:
                logger.debug(f"TDLibSyncManager emit error: {e}")


# ── مثيل مشترك ──────────────────────────────────────────────────────
tdlib_sync = TDLibSyncManager()
