"""
gunicorn.conf.py — إعدادات Gunicorn للإنتاج
متوافق مع Flask-SocketIO + gevent
"""
import os

# ── المنفذ والعنوان ──────────────────────────────────────────────────
bind        = f"0.0.0.0:{os.environ.get('PORT', 5000)}"

# ── Worker: geventwebsocket يدعم WebSocket / Socket.IO ─────────────
worker_class = "geventwebsocket.gunicorn.workers.GeventWebSocketWorker"
workers      = 1          # Socket.IO يتطلب worker واحد فقط
worker_connections = 1000

# ── المهلات ─────────────────────────────────────────────────────────
timeout      = 120        # 2 دقيقة للطلبات الثقيلة (رفع ملفات)
keepalive    = 5
graceful_timeout = 30

# ── السجلات ─────────────────────────────────────────────────────────
loglevel     = "info"
accesslog    = "-"        # stdout
errorlog     = "-"        # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)sμs'

# ── الأداء ──────────────────────────────────────────────────────────
max_requests = 1000       # إعادة تشغيل Worker تلقائياً بعد 1000 طلب
max_requests_jitter = 100
preload_app  = False      # لا preload مع gevent

# ── Hook: طباعة معلومات عند البدء ───────────────────────────────────
def on_starting(server):
    print("🚀 Gunicorn (gevent-websocket) بدأ — Abu_Malk Services")

def worker_init(worker):
    from gevent import monkey
    monkey.patch_all()
