"""
tdlib_features.py
══════════════════════════════════════════════════════════════
الميزات المتقدمة لـ TDLib — 12 وظيفة كاملة
══════════════════════════════════════════════════════════════
① الملصقات والـ GIFs
② الرسائل الصوتية
③ البث المباشر
④ المحادثات السرية
⑤ المجلدات والأرشفة
⑥ الأزرار التفاعلية (Inline Keyboards)
⑦ الإبلاغ عن المحتوى
⑧ الموقع الحي
⑨ تنسيق النص الغني
⑩ استطلاعات الرأي والاختبارات
⑪ البحث المضمن (Inline Mode)
⑫ تنزيل الملفات
"""

import logging
from typing import Optional, List, Dict, Any

from config_tdlib import tdlib_manager

logger = logging.getLogger(__name__)


class TDLibFeatures:
    """
    واجهة موحّدة لجميع ميزات TDLib المتقدمة.
    كل وظيفة تعمل عبر tdlib_manager.send() وتُعيد نتيجة TDLib.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id

    def _send(self, query: dict) -> bool:
        return tdlib_manager.send(self.user_id, query)

    # ══════════════════════════════════════════════════════
    # ① الملصقات (Stickers)
    # ══════════════════════════════════════════════════════

    def send_sticker_by_id(self, chat_id: int, sticker_file_id: int) -> bool:
        """إرسال ملصق عبر معرف الملف (من getStickers)."""
        return self._send({
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessageSticker",
                "sticker": {"@type": "inputFileId", "id": sticker_file_id},
            },
        })

    def send_sticker_local(self, chat_id: int, file_path: str) -> bool:
        """إرسال ملصق من ملف محلي (.webp / .tgs)."""
        return self._send({
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessageSticker",
                "sticker": {"@type": "inputFileLocal", "path": file_path},
            },
        })

    def get_stickers(self, emoji: str = "😊", limit: int = 20) -> bool:
        """جلب ملصقات مقترحة لإيموجي معيّن."""
        return self._send({
            "@type": "getStickers",
            "sticker_type": {"@type": "stickerTypeRegular"},
            "query": emoji,
            "limit": limit,
        })

    def get_sticker_sets(self) -> bool:
        """جلب مجموعات الملصقات المثبّتة."""
        return self._send({
            "@type": "getInstalledStickerSets",
            "sticker_type": {"@type": "stickerTypeRegular"},
        })

    # ══════════════════════════════════════════════════════
    # ② الـ GIFs والرسائل المتحركة
    # ══════════════════════════════════════════════════════

    def send_gif_local(self, chat_id: int, file_path: str, caption: str = "", duration: int = 0, width: int = 0, height: int = 0) -> bool:
        """إرسال GIF / فيديو متحرك من ملف محلي."""
        return self._send({
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessageAnimation",
                "animation": {"@type": "inputFileLocal", "path": file_path},
                "duration": duration,
                "width": width,
                "height": height,
                "caption": {"@type": "formattedText", "text": caption},
            },
        })

    def get_saved_animations(self) -> bool:
        """جلب الـ GIFs المحفوظة."""
        return self._send({"@type": "getSavedAnimations"})

    # ══════════════════════════════════════════════════════
    # ③ الرسائل الصوتية (Voice Notes)
    # ══════════════════════════════════════════════════════

    def send_voice_note(self, chat_id: int, file_path: str, duration: int = 0, waveform: bytes = b"") -> bool:
        """إرسال رسالة صوتية (.ogg Opus) من ملف محلي."""
        content: dict = {
            "@type": "inputMessageVoiceNote",
            "voice_note": {"@type": "inputFileLocal", "path": file_path},
            "duration": duration,
        }
        if waveform:
            content["waveform"] = list(waveform)
        return self._send({
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": content,
        })

    def send_audio(self, chat_id: int, file_path: str, caption: str = "", title: str = "", performer: str = "", duration: int = 0) -> bool:
        """إرسال ملف صوتي موسيقي (MP3/M4A)."""
        return self._send({
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessageAudio",
                "audio": {"@type": "inputFileLocal", "path": file_path},
                "album_cover_thumbnail": None,
                "duration": duration,
                "title": title,
                "performer": performer,
                "caption": {"@type": "formattedText", "text": caption},
            },
        })

    def download_file(self, file_id: int, priority: int = 1, offset: int = 0, limit: int = 0) -> bool:
        """تنزيل ملف (صوت/فيديو/صورة) من تيليجرام."""
        return self._send({
            "@type": "downloadFile",
            "file_id": file_id,
            "priority": priority,
            "offset": offset,
            "limit": limit,
        })

    # ══════════════════════════════════════════════════════
    # ④ البث المباشر (Live Streams)
    # ══════════════════════════════════════════════════════

    def get_group_call_info(self, group_call_id: int) -> bool:
        """جلب معلومات مكالمة جماعية أو بث مباشر."""
        return self._send({
            "@type": "getGroupCall",
            "group_call_id": group_call_id,
        })

    def create_voice_chat(self, chat_id: int) -> bool:
        """إنشاء مكالمة جماعية (Voice Chat) في مجموعة أو قناة."""
        return self._send({
            "@type": "createGroupCall",
            "chat_id": chat_id,
            "title": "",
            "start_date": 0,
            "is_rtmp_stream": True,
        })

    def get_rtmp_url(self, chat_id: int) -> bool:
        """الحصول على رابط RTMP ومفتاح البث المباشر للقناة."""
        return self._send({
            "@type": "getRtmpUrl",
            "chat_id": chat_id,
        })

    # ══════════════════════════════════════════════════════
    # ⑤ المحادثات السرية (Secret Chats - E2EE)
    # ══════════════════════════════════════════════════════

    def create_secret_chat(self, target_user_id: int) -> bool:
        """بدء محادثة سرية مشفرة من طرف إلى طرف."""
        return self._send({
            "@type": "createNewSecretChat",
            "user_id": target_user_id,
        })

    def close_secret_chat(self, secret_chat_id: int) -> bool:
        """إغلاق محادثة سرية وحذفها."""
        return self._send({
            "@type": "closeSecretChat",
            "secret_chat_id": secret_chat_id,
        })

    def get_secret_chat(self, secret_chat_id: int) -> bool:
        """جلب معلومات محادثة سرية."""
        return self._send({
            "@type": "getSecretChat",
            "secret_chat_id": secret_chat_id,
        })

    # ══════════════════════════════════════════════════════
    # ⑥ المجلدات والأرشفة (Chat Folders)
    # ══════════════════════════════════════════════════════

    def create_chat_folder(self, title: str, chat_ids: List[int], icon_name: str = "All", is_shareable: bool = False) -> bool:
        """إنشاء مجلد محادثات جديد."""
        return self._send({
            "@type": "createChatFolder",
            "folder": {
                "@type": "chatFolder",
                "title": title,
                "icon": {"@type": "chatFolderIcon", "name": icon_name},
                "pinned_chat_ids": [],
                "included_chat_ids": chat_ids,
                "excluded_chat_ids": [],
                "is_shareable": is_shareable,
                "include_contacts": False,
                "include_non_contacts": False,
                "include_bots": False,
                "include_groups": True,
                "include_channels": True,
            },
        })

    def get_chat_folders(self) -> bool:
        """جلب جميع مجلدات المحادثات."""
        return self._send({"@type": "getChatFolders"})

    def delete_chat_folder(self, chat_folder_id: int) -> bool:
        """حذف مجلد محادثات."""
        return self._send({
            "@type": "deleteChatFolder",
            "chat_folder_id": chat_folder_id,
        })

    def archive_chat(self, chat_id: int) -> bool:
        """أرشفة محادثة (نقلها لقائمة المؤرشفة)."""
        return self._send({
            "@type": "addChatToList",
            "chat_id": chat_id,
            "chat_list": {"@type": "chatListArchive"},
        })

    def unarchive_chat(self, chat_id: int) -> bool:
        """إلغاء أرشفة محادثة."""
        return self._send({
            "@type": "addChatToList",
            "chat_id": chat_id,
            "chat_list": {"@type": "chatListMain"},
        })

    # ══════════════════════════════════════════════════════
    # ⑦ الأزرار التفاعلية (Inline Keyboards)
    # ══════════════════════════════════════════════════════

    def send_message_with_buttons(self, chat_id: int, text: str, buttons: List[List[Dict]]) -> bool:
        """
        إرسال رسالة مع أزرار Inline.
        buttons: [[{"text": "...", "callback_data": "..."}], ...]
        """
        rows = []
        for row in buttons:
            row_buttons = []
            for btn in row:
                tdlib_btn: dict = {
                    "@type": "inlineKeyboardButton",
                    "text": btn.get("text", ""),
                }
                if "callback_data" in btn:
                    tdlib_btn["type"] = {
                        "@type": "inlineKeyboardButtonTypeCallback",
                        "data": btn["callback_data"].encode("utf-8").hex(),
                    }
                elif "url" in btn:
                    tdlib_btn["type"] = {
                        "@type": "inlineKeyboardButtonTypeUrl",
                        "url": btn["url"],
                    }
                elif "switch_inline_query" in btn:
                    tdlib_btn["type"] = {
                        "@type": "inlineKeyboardButtonTypeSwitchInline",
                        "query": btn["switch_inline_query"],
                        "in_current_chat": False,
                    }
                row_buttons.append(tdlib_btn)
            rows.append(row_buttons)

        return self._send({
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessageText",
                "text": {"@type": "formattedText", "text": text},
            },
            "reply_markup": {
                "@type": "replyMarkupInlineKeyboard",
                "rows": rows,
            },
        })

    def answer_callback_query(self, callback_query_id: str, text: str = "", show_alert: bool = False, url: str = "") -> bool:
        """الرد على ضغط زر Inline (Toast أو تنبيه)."""
        return self._send({
            "@type": "answerCallbackQuery",
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert,
            "url": url,
            "cache_time": 0,
        })

    # ══════════════════════════════════════════════════════
    # ⑧ الإبلاغ عن المحتوى
    # ══════════════════════════════════════════════════════

    def report_chat(self, chat_id: int, reason: str = "spam", message_ids: List[int] = None, text: str = "") -> bool:
        """
        الإبلاغ عن محادثة أو رسالة.
        reason: spam | violence | pornography | childAbuse | copyright | unrelatedLocation | fake | illegal | other
        """
        reason_map = {
            "spam":              "reportReasonSpam",
            "violence":          "reportReasonViolence",
            "porn":              "reportReasonPornography",
            "pornography":       "reportReasonPornography",
            "child":             "reportReasonChildAbuse",
            "copyright":         "reportReasonCopyright",
            "fake":              "reportReasonFake",
            "illegal":           "reportReasonIllegalDrugs",
            "other":             "reportReasonCustom",
        }
        tdlib_reason = reason_map.get(reason.lower(), "reportReasonCustom")
        query: dict = {
            "@type": "reportChat",
            "chat_id": chat_id,
            "reason": {"@type": tdlib_reason},
            "text": text,
        }
        if message_ids:
            query["message_ids"] = message_ids
        return self._send(query)

    def block_user(self, user_id_to_block: int) -> bool:
        """حظر مستخدم."""
        return self._send({
            "@type": "toggleMessageSenderIsBlocked",
            "sender_id": {"@type": "messageSenderUser", "user_id": user_id_to_block},
            "is_blocked": True,
        })

    def unblock_user(self, user_id_to_unblock: int) -> bool:
        """إلغاء حظر مستخدم."""
        return self._send({
            "@type": "toggleMessageSenderIsBlocked",
            "sender_id": {"@type": "messageSenderUser", "user_id": user_id_to_unblock},
            "is_blocked": False,
        })

    # ══════════════════════════════════════════════════════
    # ⑨ الموقع الحي (Live Location)
    # ══════════════════════════════════════════════════════

    def send_location(self, chat_id: int, latitude: float, longitude: float, live_period: int = 0, heading: int = 0, proximity_alert_radius: int = 0) -> bool:
        """
        إرسال موقع جغرافي.
        live_period: 0 = موقع ثابت، >0 = موقع حي (ثواني)
        """
        return self._send({
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessageLocation",
                "location": {
                    "@type": "location",
                    "latitude": latitude,
                    "longitude": longitude,
                    "horizontal_accuracy": 0.0,
                },
                "live_period": live_period,
                "heading": heading,
                "proximity_alert_radius": proximity_alert_radius,
            },
        })

    def stop_live_location(self, chat_id: int, message_id: int) -> bool:
        """إيقاف مشاركة الموقع الحي."""
        return self._send({
            "@type": "editMessageLiveLocation",
            "chat_id": chat_id,
            "message_id": message_id,
            "location": None,
        })

    # ══════════════════════════════════════════════════════
    # ⑩ تنسيق النص الغني (Rich Text Entities)
    # ══════════════════════════════════════════════════════

    def send_formatted_message(self, chat_id: int, text: str, entities: List[Dict]) -> bool:
        """
        إرسال رسالة بتنسيق غني.
        entities: [{"type": "bold"|"italic"|"code"|"url", "offset": 0, "length": 5, "url": "..."}]
        """
        tdlib_entities = []
        type_map = {
            "bold":          "textEntityTypeBold",
            "italic":        "textEntityTypeItalic",
            "underline":     "textEntityTypeUnderline",
            "strikethrough": "textEntityTypeStrikethrough",
            "code":          "textEntityTypeCode",
            "pre":           "textEntityTypePre",
            "spoiler":       "textEntityTypeSpoiler",
            "url":           "textEntityTypeUrl",
            "mention":       "textEntityTypeMention",
            "text_url":      "textEntityTypeTextUrl",
        }
        for e in entities:
            etype = type_map.get(e.get("type", "bold"), "textEntityTypeBold")
            entity: dict = {
                "@type": "textEntity",
                "offset": e.get("offset", 0),
                "length": e.get("length", 0),
                "type":   {"@type": etype},
            }
            if e.get("type") in ("text_url", "url") and e.get("url"):
                entity["type"] = {"@type": "textEntityTypeTextUrl", "url": e["url"]}
            tdlib_entities.append(entity)

        return self._send({
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessageText",
                "text": {
                    "@type": "formattedText",
                    "text": text,
                    "entities": tdlib_entities,
                },
            },
        })

    def parse_markdown(self, text: str) -> bool:
        """
        تحليل نص Markdown وتحويله لـ formattedText.
        مفيد لتحويل **عريض** و_مائل_ تلقائياً.
        """
        return self._send({
            "@type": "parseMarkdown",
            "text": {"@type": "formattedText", "text": text, "entities": []},
        })

    # ══════════════════════════════════════════════════════
    # ⑪ الاستطلاعات والاختبارات (Polls & Quizzes)
    # ══════════════════════════════════════════════════════

    def send_poll(
        self,
        chat_id: int,
        question: str,
        options: List[str],
        is_anonymous: bool = True,
        allows_multiple_answers: bool = False,
    ) -> bool:
        """إرسال استطلاع رأي متعدد الخيارات."""
        return self._send({
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessagePoll",
                "question": {"@type": "formattedText", "text": question, "entities": []},
                "options": [
                    {"@type": "inputPollOption", "text": {"@type": "formattedText", "text": opt, "entities": []}}
                    for opt in options
                ],
                "is_anonymous": is_anonymous,
                "type": {
                    "@type": "pollTypeRegular",
                    "allow_multiple_answers": allows_multiple_answers,
                },
                "open_period": 0,
            },
        })

    def send_quiz(
        self,
        chat_id: int,
        question: str,
        options: List[str],
        correct_option_id: int,
        explanation: str = "",
        is_anonymous: bool = True,
    ) -> bool:
        """إرسال اختبار (Quiz) مع إجابة صحيحة واحدة."""
        return self._send({
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessagePoll",
                "question": {"@type": "formattedText", "text": question, "entities": []},
                "options": [
                    {"@type": "inputPollOption", "text": {"@type": "formattedText", "text": opt, "entities": []}}
                    for opt in options
                ],
                "is_anonymous": is_anonymous,
                "type": {
                    "@type": "pollTypeQuiz",
                    "correct_option_id": correct_option_id,
                    "explanation": {"@type": "formattedText", "text": explanation, "entities": []},
                },
                "open_period": 0,
            },
        })

    def stop_poll(self, chat_id: int, message_id: int) -> bool:
        """إيقاف استطلاع رأي."""
        return self._send({
            "@type": "stopPoll",
            "chat_id": chat_id,
            "message_id": message_id,
        })

    # ══════════════════════════════════════════════════════
    # ⑫ البحث المضمن (Inline Mode)
    # ══════════════════════════════════════════════════════

    def get_inline_query_results(self, bot_user_id: int, query: str, chat_id: int = 0, offset: str = "") -> bool:
        """
        جلب نتائج بحث البوت المضمن.
        يُرسل كل حرف يكتبه المستخدم للحصول على نتائج فورية.
        """
        q: dict = {
            "@type": "getInlineQueryResults",
            "bot_user_id": bot_user_id,
            "query": query,
            "offset": offset,
        }
        if chat_id:
            q["chat_id"] = chat_id
        return self._send(q)

    def send_inline_query_result(
        self,
        chat_id: int,
        query_id: int,
        result_id: str,
        bot_user_id: int,
        hide_via_bot: bool = False,
    ) -> bool:
        """إرسال نتيجة Inline query (بعد اختيار المستخدم)."""
        return self._send({
            "@type": "sendInlineQueryResultMessage",
            "chat_id": chat_id,
            "inline_query_id": query_id,
            "result_id": result_id,
            "hide_via_bot": hide_via_bot,
        })

    # ══════════════════════════════════════════════════════
    # وظائف مساعدة إضافية
    # ══════════════════════════════════════════════════════

    def pin_message(self, chat_id: int, message_id: int, disable_notification: bool = False) -> bool:
        """تثبيت رسالة في محادثة."""
        return self._send({
            "@type": "pinChatMessage",
            "chat_id": chat_id,
            "message_id": message_id,
            "disable_notification": disable_notification,
        })

    def unpin_message(self, chat_id: int, message_id: int) -> bool:
        """إلغاء تثبيت رسالة."""
        return self._send({
            "@type": "unpinChatMessage",
            "chat_id": chat_id,
            "message_id": message_id,
        })

    def set_typing(self, chat_id: int, action: str = "typing") -> bool:
        """إرسال حالة الكتابة (يكتب...)."""
        action_map = {
            "typing":          "chatActionTyping",
            "recording_video": "chatActionRecordingVideo",
            "uploading_video": "chatActionUploadingVideo",
            "recording_voice": "chatActionRecordingVoiceNote",
            "uploading_voice": "chatActionUploadingVoiceNote",
            "uploading_photo": "chatActionUploadingPhoto",
            "uploading_doc":   "chatActionUploadingDocument",
            "choosing_sticker":"chatActionChoosingSticker",
            "cancel":          "chatActionCancel",
        }
        return self._send({
            "@type": "sendChatAction",
            "chat_id": chat_id,
            "action": {"@type": action_map.get(action, "chatActionTyping")},
        })

    def forward_message(self, from_chat_id: int, message_id: int, to_chat_id: int) -> bool:
        """إعادة توجيه رسالة."""
        return self._send({
            "@type": "forwardMessages",
            "chat_id": to_chat_id,
            "from_chat_id": from_chat_id,
            "message_ids": [message_id],
            "options": {"@type": "messageSendOptions"},
        })

    def search_messages(self, chat_id: int, query: str, limit: int = 20) -> bool:
        """البحث عن رسائل داخل محادثة."""
        return self._send({
            "@type": "searchChatMessages",
            "chat_id": chat_id,
            "query": query,
            "from_message_id": 0,
            "offset": 0,
            "limit": limit,
        })

    def get_user_full_info(self, user_id: int) -> bool:
        """جلب المعلومات الكاملة لمستخدم."""
        return self._send({"@type": "getUserFullInfo", "user_id": user_id})

    def get_chat_members(self, chat_id: int, limit: int = 200) -> bool:
        """جلب أعضاء مجموعة أو قناة."""
        return self._send({
            "@type": "getSupergroupMembers",
            "supergroup_id": chat_id,
            "filter": {"@type": "supergroupMembersFilterRecent"},
            "offset": 0,
            "limit": limit,
        })
