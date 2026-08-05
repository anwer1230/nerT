---
name: Abu_Malk Flask App
description: Flask+Telethon Telegram web client with TDLib integration layer; runs on port 5000 via "Flask TG App" workflow
---

# Abu_Malk Flask App — Project Overview

**Why:** نُسخ المشروع من https://github.com/anwer1230/Abu_Mlk ودُمج مع طبقة TDLib.

## Run Command
`cd /home/runner/workspace && python3 main.py` — workflow: `Flask TG App`

## Key Architecture
- **Entry**: `main.py` → imports `app.py` → `socketio.run()`
- **Auth (Telethon)**: `auth.py` → `TelegramLogin` class
- **Auth (TDLib)**: `auth_tdlib.py` → `TDLibAuth` class
- **TDLib Manager**: `config_tdlib.py` — graceful fallback when `tdjson` not available
- **Chat (TDLib)**: `chat_manager_tdlib.py` → `ChatManagerTDLib`
- **Sync (TDLib)**: `sync_handler_tdlib.py` → `TDLibSyncManager` (started at app init)
- **Legacy bridge**: `legacy_integration.py` → `LegacyIntegration`
- **GitHub stub**: `github_db.py` — local fallback for card_system.py

## TDLib Status
- `tdjson` Python package NOT available in this Replit environment
- All TDLib integration files created with graceful fallback to Telethon
- TDLib API routes (`/api/tdlib/*`) are registered but return `{"message": "TDLib غير متاح"}` when unavailable
- To enable TDLib: install `tdjson` package with native libtdjson.so

## Files from Repo
Python: app.py, auth.py, card_system.py, db_migration.py, gps_tracking.py,
        isolation_system.py, main.py, saved_links.py, saved_messages.py, install_tracker.py
New: config_tdlib.py, auth_tdlib.py, chat_manager_tdlib.py, sync_handler_tdlib.py, legacy_integration.py, github_db.py
Static: templates/, static/, data/

## TDLib Routes Added
- POST `/api/tdlib/login` — بدء مصادقة TDLib
- POST `/api/tdlib/verify_code` — تحقق كود
- POST `/api/tdlib/verify_password` — تحقق 2FA
- GET  `/api/tdlib/status` — حالة TDLib
- GET  `/api/tdlib/chats` — جلب محادثات
- GET  `/api/tdlib/chats/<id>/messages` — رسائل محادثة
- POST `/api/tdlib/send` — إرسال رسالة
- POST `/api/tdlib/send_bulk` — إرسال جماعي (send_monitor)
- POST `/api/tdlib/join_groups` — انضمام مجموعات (auto_join)

## Preserved Functions (لم تتأثر)
send_monitor, auto_reply, academic, formatter, auto_join, sent_batches, learning — كل الوظائف المميزة سليمة.

**How to apply:** عند تعديل أي وظيفة Telethon في app.py، تأكد من عدم تكسير الاستيرادات في الجزء العلوي (السطر 145 تقريباً). TDLib fallback آمن تلقائياً.
