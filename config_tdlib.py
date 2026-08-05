"""
config_tdlib.py
══════════════════════════════════════════════════════════════
إعدادات TDLib الأساسية — طبقة التوافق مع Telethon الحالي
══════════════════════════════════════════════════════════════
يوفر هذا الملف:
  - TDLibManager: مدير عملاء TDLib (واجهة موحدة)
  - fallback تلقائي لـ Telethon إذا لم يتوفر TDLib
"""

import json
import os
import logging
import threading
from typing import Dict, Optional, Callable

logger = logging.getLogger(__name__)

# ── محاولة استيراد tdjson ──────────────────────────────────────────
_TDLIB_AVAILABLE = False
try:
    import tdjson as _tdjson
    _TDLIB_AVAILABLE = True
    logger.info("✅ TDLib (tdjson) متاح ومُحمَّل")
except ImportError:
    logger.warning("⚠️  tdjson غير متاح — سيتم استخدام Telethon كبديل")


class TDLibManager:
    """
    مدير عملاء TDLib المتعددة — نمط Singleton.
    يدعم عدة مستخدمين متزامنين (مثل Telethon multi-session).
    إذا لم يتوفر TDLib، تُسجَّل رسائل تحذيرية فقط ولا يُرفع خطأ.
    """
    _instance: Optional["TDLibManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.clients: Dict[str, int] = {}          # {user_id: client_id}
        self.client_data: Dict[int, dict] = {}     # {client_id: {...}}
        self.lock = threading.Lock()
        self.available = _TDLIB_AVAILABLE

    # ──────────────────────────────────────────────────────────────
    def create_client(
        self,
        user_id: str,
        api_id: int,
        api_hash: str,
        session_dir: str = "sessions",
    ) -> Optional[int]:
        """إنشاء عميل TDLib جديد لمستخدم معيّن."""
        if not self.available:
            logger.warning(f"TDLib غير متاح — تجاهل create_client لـ {user_id}")
            return None

        client_id = _tdjson.td_create_client_id()

        # إعداد معاملات TDLib
        db_dir = os.path.join(session_dir, f"tdlib_{user_id}")
        files_dir = os.path.join(db_dir, "files")
        os.makedirs(db_dir, exist_ok=True)
        os.makedirs(files_dir, exist_ok=True)

        _tdjson.td_send(client_id, json.dumps({
            "@type": "setTdlibParameters",
            "database_directory": db_dir,
            "files_directory": files_dir,
            "use_file_database": True,
            "use_chat_info_database": True,
            "use_message_database": True,
            "api_id": api_id,
            "api_hash": api_hash,
            "system_language_code": "ar",
            "device_model": "Web",
            "application_version": "2.0",
        }).encode("utf-8"))

        with self.lock:
            self.clients[user_id] = client_id
            self.client_data[client_id] = {
                "user_id": user_id,
                "handlers": {},
                "authenticated": False,
                "queue": [],
            }

        logger.info(f"TDLib client created for user {user_id} (id={client_id})")
        return client_id

    def send(self, user_id: str, query: dict) -> bool:
        """إرسال أمر إلى عميل TDLib الخاص بالمستخدم."""
        if not self.available:
            logger.debug(f"TDLib unavailable — skip send for {user_id}")
            return False
        client_id = self.clients.get(user_id)
        if client_id is None:
            logger.error(f"No TDLib client found for user {user_id}")
            return False
        _tdjson.td_send(client_id, json.dumps(query).encode("utf-8"))
        return True

    def receive(self, client_id: int, timeout: float = 1.0) -> Optional[dict]:
        """استقبال رد من TDLib (non-blocking مع timeout)."""
        if not self.available:
            return None
        try:
            response = _tdjson.td_receive(timeout)
            if response:
                return json.loads(response.decode("utf-8"))
        except Exception as e:
            logger.error(f"TDLib receive error: {e}")
        return None

    def register_handler(
        self, user_id: str, event_type: str, callback: Callable
    ) -> bool:
        """تسجيل معالج لنوع حدث معيّن من TDLib."""
        client_id = self.clients.get(user_id)
        if client_id is None:
            return False
        with self.lock:
            self.client_data[client_id]["handlers"][event_type] = callback
        return True

    def get_client_id(self, user_id: str) -> Optional[int]:
        return self.clients.get(user_id)

    def is_authenticated(self, user_id: str) -> bool:
        client_id = self.clients.get(user_id)
        if not client_id:
            return False
        return self.client_data.get(client_id, {}).get("authenticated", False)

    def mark_authenticated(self, user_id: str, value: bool = True):
        client_id = self.clients.get(user_id)
        if client_id and client_id in self.client_data:
            self.client_data[client_id]["authenticated"] = value

    def close_client(self, user_id: str):
        """إغلاق عميل TDLib وتنظيف الذاكرة."""
        if not self.available:
            return
        client_id = self.clients.get(user_id)
        if client_id:
            self.send(user_id, {"@type": "close"})
            with self.lock:
                self.clients.pop(user_id, None)
                self.client_data.pop(client_id, None)


# ── مثيل مشترك للاستيراد من الوحدات الأخرى ──────────────────────────
tdlib_manager = TDLibManager()
