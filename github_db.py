"""
github_db.py — بديل محلي لوظائف GitHub كقاعدة بيانات
يُستخدم كـ fallback عندما لا تتوفر بيانات اعتماد GitHub
"""

import os
import json
import logging

logger = logging.getLogger(__name__)


def gh_load(remote_path: str, local_path: str, default=None):
    """تحميل بيانات من الملف المحلي (بديل GitHub)."""
    try:
        if os.path.exists(local_path):
            with open(local_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.debug(f"gh_load local fallback failed for {local_path}: {e}")
    return default


def gh_save(remote_path: str, local_path: str, data, commit_msg: str = "") -> bool:
    """حفظ بيانات في الملف المحلي (بديل GitHub)."""
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"gh_save local fallback failed for {local_path}: {e}")
        return False


def gh_file_exists(remote_path: str) -> bool:
    """التحقق من وجود ملف محلياً."""
    return False


def gh_delete(remote_path: str) -> bool:
    """حذف ملف (بديل محلي — لا عملية)."""
    return True
