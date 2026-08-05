"""
╔══════════════════════════════════════════════════════════════════════╗
║         آلية ترحيل قاعدة البيانات — Database Migration              ║
║   مستوحاة من MessagesStorage.java في تطبيق تيليجرام الرسمي          ║
╚══════════════════════════════════════════════════════════════════════╝

القواعد الذهبية للترحيل الآمن (كما في تيليجرام الرسمي):
  🔴 لا تستخدم DROP TABLE أبداً في التحديثات العادية
  🟢 استخدم ALTER TABLE فقط لإضافة أعمدة جديدة
  🟢 زِد DATABASE_VERSION مع كل تحديث
  🟢 تحقق من وجود العمود قبل إضافته (لتجنب الأخطاء)
"""

import sqlite3
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# رقم إصدار قاعدة البيانات — يزداد مع كل تحديث (كـ DATABASE_VERSION في Java)
DATABASE_VERSION = 5
DATABASE_NAME    = "messages.db"


class DatabaseMigration:
    """
    مدير ترحيل قاعدة البيانات.
    يعادل SQLiteOpenHelper مع onUpgrade() في تطبيق تيليجرام الرسمي.
    """

    def __init__(self, db_path: str = DATABASE_NAME):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── مساعد: التحقق من وجود عمود ──────────────────────────────────────
    def column_exists(self, table_name: str, column_name: str) -> bool:
        """
        التحقق من وجود عمود في جدول معين قبل إضافته.
        يعادل columnExists() في المصدر الرسمي لتيليجرام.

        Args:
            table_name:  اسم الجدول
            column_name: اسم العمود المراد التحقق منه

        Returns:
            True إذا كان العمود موجوداً
        """
        try:
            conn = self.get_connection()
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            for row in cursor.fetchall():
                if row["name"] == column_name:
                    return True
            return False
        except Exception as e:
            logger.error(f"column_exists({table_name}, {column_name}): {e}")
            return False

    # ── مساعد: التحقق من وجود جدول ──────────────────────────────────────
    def table_exists(self, table_name: str) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"table_exists({table_name}): {e}")
            return False

    # ── إضافة عمود بشكل آمن ──────────────────────────────────────────────
    def add_column_safe(self, table_name: str, column_name: str,
                         column_def: str) -> bool:
        """
        إضافة عمود جديد فقط إذا لم يكن موجوداً.
        يعادل النمط الآمن في onUpgrade():
          if (!columnExists(db, table, col)) db.execSQL("ALTER TABLE ...")

        Args:
            table_name:  اسم الجدول
            column_name: اسم العمود الجديد
            column_def:  تعريف العمود (مثال: "INTEGER DEFAULT 0")

        Returns:
            True إذا تم إضافة العمود أو كان موجوداً بالفعل
        """
        if not self.table_exists(table_name):
            logger.warning(f"add_column_safe: الجدول '{table_name}' غير موجود")
            return False

        if self.column_exists(table_name, column_name):
            logger.debug(f"العمود '{column_name}' موجود بالفعل في '{table_name}'")
            return True

        try:
            conn = self.get_connection()
            conn.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"
            )
            conn.commit()
            logger.info(f"✅ تمت إضافة العمود '{column_name}' إلى '{table_name}'")
            return True
        except Exception as e:
            logger.error(f"❌ فشل إضافة العمود '{column_name}': {e}")
            return False

    # ── الحصول على رقم الإصدار الحالي ────────────────────────────────────
    def get_current_version(self) -> int:
        """يعادل db.getVersion() في SQLiteOpenHelper"""
        try:
            conn = self.get_connection()
            cursor = conn.execute("PRAGMA user_version")
            row = cursor.fetchone()
            return row[0] if row else 0
        except Exception as e:
            logger.error(f"get_current_version: {e}")
            return 0

    def set_version(self, version: int):
        """يعادل db.setVersion(newVersion) في SQLiteOpenHelper"""
        try:
            conn = self.get_connection()
            conn.execute(f"PRAGMA user_version = {version}")
            conn.commit()
        except Exception as e:
            logger.error(f"set_version({version}): {e}")

    # ── إنشاء الجداول للمرة الأولى ───────────────────────────────────────
    def on_create(self):
        """
        إنشاء الجداول لأول مرة.
        يعادل SQLiteOpenHelper.onCreate() في Java.
        """
        conn = self.get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS messages (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         TEXT    NOT NULL,
                    chat_id         TEXT    NOT NULL,
                    message_text    TEXT    DEFAULT '',
                    message_date    TEXT    DEFAULT '',
                    is_outgoing     INTEGER DEFAULT 0,
                    media_type      TEXT    DEFAULT '',
                    forwarded_from  TEXT    DEFAULT '',
                    reaction_count  INTEGER DEFAULT 0,
                    saved_to_github INTEGER DEFAULT 0,
                    created_at      TEXT    DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS dialogs (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         TEXT    NOT NULL,
                    dialog_id       TEXT    NOT NULL,
                    dialog_type     TEXT    DEFAULT 'user',
                    title           TEXT    DEFAULT '',
                    is_saved_msgs   INTEGER DEFAULT 0,
                    last_message    TEXT    DEFAULT '',
                    last_date       TEXT    DEFAULT '',
                    UNIQUE(user_id, dialog_id)
                );

                CREATE TABLE IF NOT EXISTS user_sessions (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         TEXT    NOT NULL UNIQUE,
                    tg_user_id      INTEGER DEFAULT 0,
                    auth_key        TEXT    DEFAULT '',
                    dc_id           INTEGER DEFAULT 0,
                    is_active       INTEGER DEFAULT 0,
                    last_seen       TEXT    DEFAULT (datetime('now')),
                    created_at      TEXT    DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS sync_log (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation       TEXT    NOT NULL,
                    target          TEXT    DEFAULT '',
                    status          TEXT    DEFAULT 'pending',
                    error_msg       TEXT    DEFAULT '',
                    created_at      TEXT    DEFAULT (datetime('now'))
                );
            """)
            conn.commit()
            logger.info("✅ تم إنشاء جداول قاعدة البيانات للمرة الأولى")
        except Exception as e:
            logger.error(f"on_create failed: {e}")
            raise

    # ── ترحيل قاعدة البيانات ─────────────────────────────────────────────
    def on_upgrade(self, old_version: int, new_version: int):
        """
        ترحيل قاعدة البيانات من إصدار قديم إلى جديد.
        يعادل SQLiteOpenHelper.onUpgrade() في Java.

        🔴 القاعدة الذهبية: لا تستخدم DROP TABLE
        🟢 استخدم ALTER TABLE فقط لإضافة أعمدة جديدة
        """
        logger.info(f"[Migration] ترحيل قاعدة البيانات من v{old_version} → v{new_version}")

        # الإصدار 2: إضافة عمود reaction_count لجدول messages
        if old_version < 2:
            self.add_column_safe("messages", "reaction_count", "INTEGER DEFAULT 0")

        # الإصدار 3: إضافة عمود forwarded_from
        if old_version < 3:
            self.add_column_safe("messages", "forwarded_from", "TEXT DEFAULT ''")

        # الإصدار 4: إضافة عمود is_saved_msgs لجدول dialogs
        if old_version < 4:
            self.add_column_safe("dialogs", "is_saved_msgs", "INTEGER DEFAULT 0")

        # الإصدار 5: إضافة عمود saved_to_github لجدول messages
        if old_version < 5:
            self.add_column_safe("messages", "saved_to_github", "INTEGER DEFAULT 0")

        # ── أضف تحديثات الإصدارات المستقبلية هنا ──
        # if old_version < 6:
        #     self.add_column_safe("messages", "new_column", "TEXT DEFAULT ''")

        self.set_version(new_version)
        logger.info(f"[Migration] ✅ اكتمل الترحيل إلى v{new_version}")

    # ── نقطة الدخول الرئيسية ─────────────────────────────────────────────
    def initialize(self):
        """
        نقطة الدخول الرئيسية — يُستدعى عند بدء التطبيق.
        يعادل SQLiteOpenHelper constructor في Java:
          • يُنشئ الجداول إذا كانت قاعدة البيانات جديدة
          • يُرحّل إذا كان الإصدار الحالي أقل من المطلوب
        """
        try:
            current_version = self.get_current_version()

            if current_version == 0:
                # قاعدة بيانات جديدة — أنشئ الجداول
                self.on_create()
                self.set_version(DATABASE_VERSION)
                logger.info(f"[Migration] ✅ قاعدة بيانات جديدة v{DATABASE_VERSION}")
            elif current_version < DATABASE_VERSION:
                # قاعدة بيانات قديمة — رحّلها
                self.on_upgrade(current_version, DATABASE_VERSION)
            else:
                logger.info(f"[Migration] ✅ قاعدة البيانات محدّثة (v{current_version})")

        except Exception as e:
            logger.error(f"[Migration] ❌ خطأ في تهيئة قاعدة البيانات: {e}")
            raise


# ══════════════════════════════════════════════════════════════════════
#  مثيل عالمي — singleton للاستخدام في جميع أنحاء التطبيق
# ══════════════════════════════════════════════════════════════════════
_db_instance: Optional[DatabaseMigration] = None


def get_db(db_path: str = DATABASE_NAME) -> DatabaseMigration:
    """إرجاع مثيل DatabaseMigration — singleton"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseMigration(db_path)
        _db_instance.initialize()
    return _db_instance


def init_database(db_path: str = DATABASE_NAME):
    """تهيئة قاعدة البيانات عند بدء التطبيق"""
    db = get_db(db_path)
    return db
