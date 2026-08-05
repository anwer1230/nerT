"""
legacy_integration.py
══════════════════════════════════════════════════════════════
طبقة التوافق — تجسير وظائف TDLib مع الوظائف الحالية
يحافظ على:
  ① send_monitor     — الإرسال والمراقبة
  ② auto_reply       — الرد التلقائي
  ③ academic         — الأدوات الأكاديمية
  ④ auto_join        — الانضمام المتقدم
  ⑤ sent_batches     — رسائلي
  ⑥ learning         — نظام التعلم الذكي
══════════════════════════════════════════════════════════════
"""

import logging
import time
from typing import List, Dict, Optional

from config_tdlib import tdlib_manager
from chat_manager_tdlib import ChatManagerTDLib

logger = logging.getLogger(__name__)


class LegacyIntegration:
    """
    واجهة موحّدة تجمع TDLib مع الوظائف الحالية.
    إذا لم يتوفر TDLib، تُسجَّل رسائل تحذيرية وتُعاد نتائج فارغة.
    """

    def __init__(self, user_id: str):
        self.user_id  = user_id
        self.chat_mgr = ChatManagerTDLib(user_id)

    # ══════════════════════════════════════════════════════
    #  ① الإرسال والمراقبة (send_monitor)
    # ══════════════════════════════════════════════════════

    def send_to_groups(
        self,
        groups: List[str],
        message: str,
        delay: float = 1.5,
    ) -> List[Dict]:
        """إرسال رسالة إلى عدة مجموعات عبر TDLib."""
        if not tdlib_manager.available:
            logger.warning("TDLib unavailable — send_to_groups skipped")
            return [{"group": g, "success": False, "error": "TDLib غير متاح"} for g in groups]

        results = []
        for group in groups:
            try:
                chat_id = self._resolve_group(group)
                if chat_id:
                    self.chat_mgr.send_message(chat_id, message)
                    results.append({"group": group, "success": True})
                else:
                    results.append({"group": group, "success": False, "error": "لم يُعثر على المجموعة"})
            except Exception as e:
                logger.error(f"send_to_groups error for {group}: {e}")
                results.append({"group": group, "success": False, "error": str(e)})
            time.sleep(delay)

        return results

    def _resolve_group(self, identifier: str, timeout: float = 10.0) -> Optional[int]:
        """
        تحويل username/link إلى chat_id عبر TDLib.
        يستخدم Queue بسيطة للانتظار المتزامن.
        """
        import queue as _queue
        result_q: _queue.Queue = _queue.Queue(maxsize=1)

        def _handler(update):
            if update.get("@type") == "chat":
                result_q.put(update.get("id"))

        tdlib_manager.register_handler(self.user_id, "chat", _handler)
        self.chat_mgr.search_public_chat(identifier)

        try:
            return result_q.get(timeout=timeout)
        except _queue.Empty:
            return None

    # ══════════════════════════════════════════════════════
    #  ② الرد التلقائي (auto_reply)
    # ══════════════════════════════════════════════════════

    def setup_auto_reply(self, rules: List[Dict]) -> bool:
        """
        إعداد ردود تلقائية عبر TDLib.
        rules: [{"keyword": "...", "reply": "..."}, ...]
        """
        if not tdlib_manager.available:
            logger.warning("TDLib unavailable — auto_reply skipped")
            return False

        def _message_handler(formatted_msg: dict):
            text = formatted_msg.get("text", "")
            chat_id = formatted_msg.get("chat_id")
            if not chat_id:
                return
            for rule in rules:
                kw = rule.get("keyword", "")
                if kw and kw in text:
                    self.chat_mgr.send_message(chat_id, rule.get("reply", ""))
                    break

        tdlib_manager.register_handler(
            self.user_id, "updateNewMessage", _message_handler
        )
        return True

    # ══════════════════════════════════════════════════════
    #  ③ الأدوات الأكاديمية (academic)
    # ══════════════════════════════════════════════════════

    def send_academic_file(
        self, chat_id: int, file_path: str, caption: str = ""
    ) -> bool:
        """إرسال ملف أكاديمي (PDF/DOCX) عبر TDLib."""
        if not tdlib_manager.available:
            return False
        return tdlib_manager.send(self.user_id, {
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessageDocument",
                "document": {"@type": "inputFileLocal", "path": file_path},
                "caption":  {"@type": "formattedText", "text": caption},
            },
        })

    # ══════════════════════════════════════════════════════
    #  ④ الانضمام المتقدم (auto_join)
    # ══════════════════════════════════════════════════════

    def join_groups_batch(
        self,
        links: List[str],
        delay: float = 2.0,
    ) -> List[Dict]:
        """الانضمام إلى عدة مجموعات بالتسلسل."""
        results = []
        for link in links:
            try:
                ok = self.chat_mgr.join_chat_by_invite_link(link)
                results.append({"link": link, "success": ok})
            except Exception as e:
                results.append({"link": link, "success": False, "error": str(e)})
            time.sleep(delay)
        return results

    # ══════════════════════════════════════════════════════
    #  ⑤ رسائلي (sent_batches) — يستخدم قاعدة البيانات الحالية
    # ══════════════════════════════════════════════════════

    def save_sent_batch(self, batch_data: dict) -> bool:
        """حفظ دفعة إرسال في قاعدة البيانات الحالية."""
        try:
            import json, os
            data_dir = "data"
            os.makedirs(data_dir, exist_ok=True)
            batches_file = os.path.join(data_dir, f"batches_{self.user_id}.json")
            batches = []
            if os.path.exists(batches_file):
                with open(batches_file, "r", encoding="utf-8") as f:
                    batches = json.load(f)
            batches.append(batch_data)
            with open(batches_file, "w", encoding="utf-8") as f:
                json.dump(batches, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"save_sent_batch error: {e}")
            return False

    def get_sent_batches(self) -> List[Dict]:
        """جلب جميع دفعات الإرسال."""
        try:
            import json, os
            batches_file = os.path.join("data", f"batches_{self.user_id}.json")
            if os.path.exists(batches_file):
                with open(batches_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"get_sent_batches error: {e}")
        return []

    # ══════════════════════════════════════════════════════
    #  ⑥ نظام التعلم الذكي (learning) — يعيد استخدام الكود الحالي
    # ══════════════════════════════════════════════════════

    def get_learned_patterns(self) -> dict:
        """جلب أنماط التعلم المحفوظة للمستخدم."""
        try:
            import json, os
            path = os.path.join("data", "learning_memory", f"{self.user_id}.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"get_learned_patterns error: {e}")
        return {}

    def save_learned_patterns(self, patterns: dict) -> bool:
        """حفظ أنماط التعلم المحدّثة."""
        try:
            import json, os
            os.makedirs(os.path.join("data", "learning_memory"), exist_ok=True)
            path = os.path.join("data", "learning_memory", f"{self.user_id}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(patterns, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"save_learned_patterns error: {e}")
            return False
