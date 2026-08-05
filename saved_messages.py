"""
╔══════════════════════════════════════════════════════════════════════╗
║          آلية "الرسائل المحفوظة" — Saved Messages Mechanism         ║
║   مستوحاة من الكود المصدري لتطبيق تيليجرام الرسمي لأندرويد          ║
╚══════════════════════════════════════════════════════════════════════╝

هذه الوحدة تُنفّذ آلية "الرسائل المحفوظة" بنفس المنطق الذي يعتمده
تطبيق تيليجرام الرسمي:
  - مقارنة Peer الخاص بالمحادثة مع معرف المستخدم نفسه
  - إرسال رسائل إلى "الرسائل المحفوظة" عبر inputPeerSelf ('me')
  - الحصول على/حفظ معرف المستخدم الحالي

يستخدم Telethon بدلاً من Java/TLRPC لأن التطبيق مبني بـ Python/Flask.
"""

import os
import json
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════
#  UserConfig — حفظ واستعادة معرف المستخدم الحالي
#  يعادل UserConfig.java في تطبيق تيليجرام الرسمي
# ══════════════════════════════════════════════════════════════════════

class UserConfig:
    """
    يُخزّن معرف المستخدم الحالي لكل حساب (بالمثل تماماً لـ UserConfig.java).
    يحفظ البيانات في ملف JSON دائم ويستعيدها عند بدء التشغيل.
    """
    _instances: dict = {}

    def __init__(self, user_id: str, sessions_dir: str = "sessions"):
        self.user_id = user_id
        self.sessions_dir = sessions_dir
        self._config_file = os.path.join(sessions_dir, f"{user_id}_userconfig.json")
        self._data: dict = {}
        self.load_config()

    @classmethod
    def get_instance(cls, user_id: str, sessions_dir: str = "sessions") -> "UserConfig":
        """نمط Singleton — مثيل واحد لكل مستخدم (كـ UserConfig.getInstance() في Java)"""
        if user_id not in cls._instances:
            cls._instances[user_id] = cls(user_id, sessions_dir)
        return cls._instances[user_id]

    @classmethod
    def invalidate(cls, user_id: str):
        """إلغاء المثيل المخزّن (عند تسجيل الخروج)"""
        cls._instances.pop(user_id, None)

    def get_client_user_id(self) -> int:
        """
        معرف مستخدم تيليجرام الحالي.
        يعادل UserConfig.getClientUserId() في Java.
        """
        return self._data.get("client_user_id", 0)

    def set_client_user_id(self, uid: int):
        """تعيين معرف المستخدم وحفظه فوراً"""
        self._data["client_user_id"] = uid
        self.save_config()

    def get_auth_key(self) -> Optional[str]:
        """مفتاح الجلسة (StringSession) — يعادل authKey في Java"""
        return self._data.get("auth_key")

    def set_auth_key(self, key: str):
        self._data["auth_key"] = key
        self.save_config()

    def get_dc_id(self) -> int:
        return self._data.get("dc_id", 0)

    def set_dc_id(self, dc_id: int):
        self._data["dc_id"] = dc_id
        self.save_config()

    def save_config(self):
        """
        حفظ إعدادات المستخدم في ملف JSON دائم.
        يعادل UserConfig.saveConfig() الذي يحفظ في SharedPreferences + auth_key.dat.
        """
        try:
            os.makedirs(self.sessions_dir, exist_ok=True)
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"UserConfig.save_config failed for {self.user_id}: {e}")

    def load_config(self):
        """
        استعادة إعدادات المستخدم من الملف.
        يعادل UserConfig.loadConfig() الذي يقرأ من SharedPreferences + auth_key.dat.
        """
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            else:
                self._data = {}
        except Exception as e:
            logger.error(f"UserConfig.load_config failed for {self.user_id}: {e}")
            self._data = {}

    def has_valid_session(self) -> bool:
        """
        التحقق من وجود جلسة صالحة.
        يُستخدم في ApplicationLoader.onCreate() قبل عرض أي واجهة.
        """
        return (
            self.get_client_user_id() != 0
            and self.get_auth_key() is not None
            and len(self.get_auth_key()) > 10
        )


# ══════════════════════════════════════════════════════════════════════
#  SavedMessagesHelper — آلية "الرسائل المحفوظة"
#  يعادل منطق MessagesController.isSavedMessages() في Java
# ══════════════════════════════════════════════════════════════════════

class SavedMessagesHelper:
    """
    يُنفّذ آلية "الرسائل المحفوظة" بنفس منطق تيليجرام الرسمي:
      - is_saved_messages_dialog()  ← يعادل isSavedMessages(dialog) في Java
      - send_to_saved_messages()    ← يعادل sendMessageToSelf() في Java
    """

    SAVED_MESSAGES_TITLE = "الرسائل المحفوظة"

    @staticmethod
    def is_saved_messages_dialog(dialog_entity, client_user_id: int) -> bool:
        """
        التحقق من كون المحادثة هي "الرسائل المحفوظة".

        المنطق (كما في MessagesController.isSavedMessages() بتيليجرام الرسمي):
          إذا كان الـ Peer من نوع مستخدم (User) ويساوي معرف المستخدم الحالي
          ← هذه هي "الرسائل المحفوظة".

        Args:
            dialog_entity: كائن Dialog من Telethon (يحتوي على entity)
            client_user_id: معرف المستخدم الحالي (من UserConfig)

        Returns:
            True إذا كانت المحادثة هي الرسائل المحفوظة
        """
        if dialog_entity is None or client_user_id == 0:
            return False

        try:
            # في Telethon: Dialog.entity هو User/Chat/Channel
            # نتحقق إذا كان المستخدم وإذا كان معرفه مطابقاً لمعرف المستخدم الحالي
            from telethon.tl.types import User
            if isinstance(dialog_entity, User):
                return dialog_entity.id == client_user_id
        except ImportError:
            # fallback: تحقق مباشر من الـ id
            entity_id = getattr(dialog_entity, 'id', None)
            if entity_id is not None:
                return entity_id == client_user_id

        return False

    @staticmethod
    def get_dialog_display_name(dialog_entity, client_user_id: int) -> str:
        """
        يرجع اسم العرض للمحادثة.
        إذا كانت "رسائل محفوظة" يرجع النص المخصص.
        يعادل المنطق في DialogCell.java:
          if (isSavedMessages(dialog)) chatTitle = "الرسائل المحفوظة"
        """
        if SavedMessagesHelper.is_saved_messages_dialog(dialog_entity, client_user_id):
            return SavedMessagesHelper.SAVED_MESSAGES_TITLE

        # العرض العادي للمستخدم/المجموعة
        first_name = getattr(dialog_entity, 'first_name', '') or ''
        last_name  = getattr(dialog_entity, 'last_name', '') or ''
        title      = getattr(dialog_entity, 'title', '') or ''
        username   = getattr(dialog_entity, 'username', '') or ''

        full_name = f"{first_name} {last_name}".strip()
        return full_name or title or username or str(getattr(dialog_entity, 'id', ''))

    @staticmethod
    async def send_to_saved_messages(client, message_text: str) -> bool:
        """
        إرسال رسالة إلى "الرسائل المحفوظة" عبر inputPeerSelf.
        يعادل SendMessagesHelper.sendMessageToSelf() في Java.

        في Telethon يُستخدم 'me' كـ inputPeerSelf تلقائياً.
        """
        try:
            await client.send_message('me', message_text)
            logger.info("✅ تم إرسال الرسالة إلى الرسائل المحفوظة")
            return True
        except Exception as e:
            logger.error(f"❌ فشل إرسال الرسالة إلى الرسائل المحفوظة: {e}")
            return False

    @staticmethod
    async def get_saved_messages_history(client, limit: int = 20) -> list:
        """
        جلب سجل الرسائل المحفوظة.
        """
        try:
            messages = []
            async for msg in client.iter_messages('me', limit=limit):
                messages.append({
                    'id': msg.id,
                    'text': msg.text or '',
                    'date': str(msg.date),
                    'media': msg.media is not None,
                })
            return messages
        except Exception as e:
            logger.error(f"خطأ في جلب الرسائل المحفوظة: {e}")
            return []


# ══════════════════════════════════════════════════════════════════════
#  SessionBootstrap — استعادة الجلسة عند بدء التشغيل
#  يعادل ApplicationLoader.onCreate() في Java
# ══════════════════════════════════════════════════════════════════════

class SessionBootstrap:
    """
    يستعيد جلسة تيليجرام فوراً عند بدء التطبيق قبل عرض أي واجهة.
    يعادل:
      ApplicationLoader.onCreate() → UserConfig.loadConfig() → connectWithAuthKey()
    """

    @staticmethod
    def restore_session_on_startup(user_id: str, sessions_dir: str = "sessions") -> dict:
        """
        التحقق من وجود جلسة سابقة صالحة عند بدء التشغيل.

        Returns:
            dict مع:
              'has_session': bool
              'client_user_id': int
              'auth_key': str|None
              'dc_id': int
        """
        config = UserConfig.get_instance(user_id, sessions_dir)
        config.load_config()  # تحميل من الملف الدائم

        has_session = config.has_valid_session()

        result = {
            'has_session': has_session,
            'client_user_id': config.get_client_user_id(),
            'auth_key': config.get_auth_key() if has_session else None,
            'dc_id': config.get_dc_id(),
        }

        if has_session:
            logger.info(
                f"[SessionBootstrap] ✅ جلسة صالحة موجودة للمستخدم {user_id} "
                f"(TG_ID={result['client_user_id']})"
            )
        else:
            logger.info(
                f"[SessionBootstrap] ℹ️ لا توجد جلسة سابقة للمستخدم {user_id} "
                "— سيُعرض نموذج تسجيل الدخول"
            )

        return result

    @staticmethod
    def save_session_after_login(user_id: str, tg_user_id: int,
                                  auth_key: str, dc_id: int = 0,
                                  sessions_dir: str = "sessions"):
        """
        حفظ بيانات الجلسة بعد تسجيل الدخول بنجاح.
        يعادل UserConfig.saveConfig() الذي يحفظ في SharedPreferences + auth_key.dat.
        """
        config = UserConfig.get_instance(user_id, sessions_dir)
        config.set_client_user_id(tg_user_id)
        config.set_auth_key(auth_key)
        config.set_dc_id(dc_id)
        logger.info(
            f"[SessionBootstrap] 💾 تم حفظ الجلسة للمستخدم {user_id} "
            f"(TG_ID={tg_user_id})"
        )

    @staticmethod
    def clear_session(user_id: str, sessions_dir: str = "sessions"):
        """حذف الجلسة (عند تسجيل الخروج)"""
        UserConfig.invalidate(user_id)
        config_file = os.path.join(sessions_dir, f"{user_id}_userconfig.json")
        if os.path.exists(config_file):
            try:
                os.remove(config_file)
                logger.info(f"[SessionBootstrap] 🗑️ تم حذف الجلسة للمستخدم {user_id}")
            except Exception as e:
                logger.error(f"[SessionBootstrap] خطأ في حذف الجلسة: {e}")
