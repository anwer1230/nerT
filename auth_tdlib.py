"""
auth_tdlib.py
══════════════════════════════════════════════════════════════
نظام المصادقة عبر TDLib — يُدمج مع Flask و Socket.IO
يعمل بجانب auth.py (Telethon) دون أي تعارض
══════════════════════════════════════════════════════════════
"""

import threading
import logging
from typing import Optional

from config_tdlib import tdlib_manager

logger = logging.getLogger(__name__)

# API معرّفات تيليجرام (نفس auth.py)
API_ID   = 22043994
API_HASH = "56f64582b363d367280db96586b97801"


class TDLibAuth:
    """
    مدير مصادقة TDLib لمستخدم واحد.
    يدعم: رقم الهاتف → كود التحقق → كلمة المرور (2FA).
    """

    def __init__(self, user_id: str):
        self.user_id    = user_id
        self.auth_state = "waiting"   # waiting | code | password | ready | error
        self.client_id: Optional[int] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._socketio  = None        # يُضبط لاحقاً من app.py

    # ── إعداد Socket.IO للإشعارات ────────────────────────────────
    def set_socketio(self, socketio_instance):
        self._socketio = socketio_instance

    def _emit(self, event: str, data: dict):
        """إرسال حدث Socket.IO إلى غرفة المستخدم (إن توفرت)."""
        if self._socketio:
            try:
                self._socketio.emit(event, data, room=f"user_{self.user_id}")
            except Exception as e:
                logger.error(f"TDLibAuth emit error: {e}")

    # ── الخطوة 1: بدء المصادقة برقم الهاتف ──────────────────────
    def start_auth(
        self,
        phone_number: str,
        api_id: int = API_ID,
        api_hash: str = API_HASH,
        session_dir: str = "sessions",
    ) -> dict:
        if not tdlib_manager.available:
            return {
                "success": False,
                "message": "TDLib غير متاح في هذه البيئة — استخدم تسجيل الدخول عبر Telethon",
            }

        self.client_id = tdlib_manager.create_client(
            self.user_id, api_id, api_hash, session_dir
        )
        if self.client_id is None:
            return {"success": False, "message": "فشل إنشاء عميل TDLib"}

        # إرسال رقم الهاتف
        ok = tdlib_manager.send(self.user_id, {
            "@type": "setAuthenticationPhoneNumber",
            "phone_number": phone_number,
            "settings": {},
        })

        if ok:
            self._start_update_loop()
            return {"success": True, "status": "code_sent", "message": "تم إرسال كود التحقق"}

        return {"success": False, "message": "فشل إرسال رقم الهاتف إلى TDLib"}

    # ── الخطوة 2: التحقق من الكود ────────────────────────────────
    def verify_code(self, code: str) -> dict:
        if self.auth_state != "code":
            return {"success": False, "message": "لم يُطلب كود تحقق بعد"}
        ok = tdlib_manager.send(self.user_id, {
            "@type": "checkAuthenticationCode",
            "code": code,
        })
        return {"success": ok, "status": "verifying"}

    # ── الخطوة 3: التحقق من كلمة المرور (2FA) ────────────────────
    def verify_password(self, password: str) -> dict:
        if self.auth_state != "password":
            return {"success": False, "message": "لم يُطلب رمز 2FA"}
        ok = tdlib_manager.send(self.user_id, {
            "@type": "checkAuthenticationPassword",
            "password": password,
        })
        return {"success": ok, "status": "verifying"}

    # ── حلقة معالجة تحديثات TDLib ────────────────────────────────
    def _start_update_loop(self):
        def _loop():
            while self.auth_state not in ("ready", "error"):
                update = tdlib_manager.receive(self.client_id, timeout=1.0)
                if update:
                    self._handle_update(update)

        self._loop_thread = threading.Thread(target=_loop, daemon=True)
        self._loop_thread.start()

    def _handle_update(self, update: dict):
        update_type = update.get("@type", "")

        if update_type == "updateAuthorizationState":
            state = update.get("authorization_state", {})
            stype = state.get("@type", "")

            if stype == "authorizationStateWaitCode":
                self.auth_state = "code"
                self._emit("auth_state", {
                    "state": "code_required",
                    "message": "أدخل كود التحقق الوارد على تطبيق تيليجرام",
                })

            elif stype == "authorizationStateWaitPassword":
                self.auth_state = "password"
                self._emit("auth_state", {
                    "state": "password_required",
                    "message": "أدخل كلمة مرور التحقق بخطوتين",
                })

            elif stype == "authorizationStateReady":
                self.auth_state = "ready"
                tdlib_manager.mark_authenticated(self.user_id, True)
                tdlib_manager.send(self.user_id, {"@type": "getMe"})
                self._emit("auth_state", {
                    "state": "ready",
                    "message": "✅ تم تسجيل الدخول عبر TDLib بنجاح",
                })

            elif stype == "authorizationStateWaitTdlibParameters":
                # طبيعي — TDLib يطلب المعاملات (تم إرسالها في create_client)
                pass

            elif stype in (
                "authorizationStateLoggingOut",
                "authorizationStateClosing",
                "authorizationStateClosed",
            ):
                self.auth_state = "error"

        elif update_type == "error":
            logger.error(f"TDLib auth error: {update}")
            self._emit("auth_error", {
                "message": update.get("message", "خطأ غير معروف"),
            })
