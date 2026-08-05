// static/js/sync.js — مركز سرعة إنجاز
// المزامنة الفورية الكاملة بين الأجهزة

class SyncManager {
    constructor() {
        this.devices      = [];
        this.isSyncing    = false;
        this.lastSyncTime = null;
        this.syncInterval = 30000; // 30 ثانية
        this._intervalId  = null;
        this.deviceId     = null;
    }

    init() {
        this._loadDeviceId();
        this.loadDevices();
        this._intervalId = setInterval(() => this.sync(), this.syncInterval);
        this._bindSocketEvents();
        this._subscribeSync();
        console.log('🔄 SyncManager: جاهز — device_id:', this.deviceId);
    }

    destroy() {
        if (this._intervalId) clearInterval(this._intervalId);
    }

    // ─── معرف الجهاز ─────────────────────────────────────────────
    _loadDeviceId() {
        let id = localStorage.getItem('device_id');
        if (!id) {
            id = 'dev_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
            localStorage.setItem('device_id', id);
        }
        this.deviceId = id;
    }

    _deviceType() {
        return /Mobi|Android/i.test(navigator.userAgent) ? 'mobile' : 'desktop';
    }

    _deviceName() {
        const ua  = navigator.userAgent;
        const os  = /Android/i.test(ua) ? 'Android'
                  : /iPhone|iPad/i.test(ua) ? 'iOS'
                  : /Windows/i.test(ua) ? 'Windows'
                  : /Mac/i.test(ua) ? 'Mac'
                  : /Linux/i.test(ua) ? 'Linux'
                  : 'جهاز';
        const br  = /Chrome/i.test(ua) ? 'Chrome'
                  : /Firefox/i.test(ua) ? 'Firefox'
                  : /Safari/i.test(ua) ? 'Safari'
                  : /Edge/i.test(ua) ? 'Edge'
                  : 'متصفح';
        return `${os} — ${br}`;
    }

    // ─── الاشتراك في المزامنة مع الخادم ─────────────────────────
    _subscribeSync() {
        const s = window.socket;
        if (!s) return;
        s.emit('sync_subscribe', {
            device_id:   this.deviceId,
            device_name: this._deviceName(),
            device_type: this._deviceType(),
        });
    }

    // ─── ربط Socket.IO ───────────────────────────────────────────
    _bindSocketEvents() {
        const s = window.socket;
        if (!s) return;

        // ── تحديثات المزامنة العامة ──
        s.on('sync_update', (data) => {
            this._applyChanges(data.changes);
            this._showToast('🔄 تمت مزامنة من جهاز آخر', 'info');
        });

        // ── إدارة الأجهزة ──
        s.on('device_connected', (data) => {
            this._showToast(`📱 جهاز "${data.device_name}" متصل الآن`, 'info');
            this.loadDevices();
        });

        s.on('device_disconnected', (data) => {
            this._showToast(`📴 جهاز "${data.device_name}" غير متصل`, 'warning');
            this.loadDevices();
        });

        s.on('session_terminated', (data) => {
            this._showToast('🚫 تم إنهاء جلستك من جهاز آخر', 'error');
            // إعادة توجيه بعد ثانيتين
            setTimeout(() => { window.location.href = '/'; }, 2000);
        });

        // ── تعديل الرسائل (من TDLib) ──
        s.on('message_edited', (data) => {
            this._handleMessageEdited(data);
        });

        // ── حذف الرسائل (من TDLib) ──
        s.on('messages_deleted', (data) => {
            this._handleMessagesDeleted(data);
        });

        // ── تحديث حالة القراءة (من TDLib) ──
        s.on('read_history', (data) => {
            this._handleReadHistory(data);
        });
    }

    // ─── تطبيق تعديل رسالة على الواجهة ──────────────────────────
    _handleMessageEdited(data) {
        if (!data || !data.msg_id) return;
        // تحديث نص الرسالة في الـ DOM إذا كانت ظاهرة
        const msgEl = document.querySelector(`[data-msg-id="${data.msg_id}"]`);
        if (msgEl) {
            const textEl = msgEl.querySelector('.msg-text, .message-text, .text-content');
            if (textEl && data.new_text != null) {
                textEl.textContent = data.new_text;
                // إضافة علامة "تم التعديل"
                if (!msgEl.querySelector('.edited-label')) {
                    const label = document.createElement('span');
                    label.className = 'edited-label';
                    label.textContent = ' (تم التعديل)';
                    label.style.cssText = 'font-size:11px;color:var(--text2,#888);';
                    textEl.appendChild(label);
                }
            }
        }
        // إعادة بناء قائمة المحادثة إذا توفرت الدالة
        if (typeof window.refreshCurrentChat === 'function') {
            window.refreshCurrentChat(data.chat_id);
        }
    }

    // ─── تطبيق حذف الرسائل على الواجهة ──────────────────────────
    _handleMessagesDeleted(data) {
        if (!data || !data.ids) return;
        (data.ids || []).forEach(mid => {
            const el = document.querySelector(`[data-msg-id="${mid}"]`);
            if (el) {
                el.style.transition = 'opacity 0.3s';
                el.style.opacity = '0';
                setTimeout(() => el.remove(), 300);
            }
        });
        // تحديث آخر رسالة في قائمة المحادثات
        if (typeof window.refreshChatPreview === 'function') {
            window.refreshChatPreview(data.chat_id);
        }
    }

    // ─── تحديث حالة القراءة في الواجهة ──────────────────────────
    _handleReadHistory(data) {
        if (!data || !data.chat_id) return;
        // مسح عداد الرسائل غير المقروءة للمحادثة
        const badge = document.querySelector(
            `[data-chat-id="${data.chat_id}"] .unread-badge,` +
            `[data-chat-id="${data.chat_id}"] .unread-count`
        );
        if (badge) badge.remove();
        // تحديث علامة القراءة على الرسائل المُرسَلة
        document.querySelectorAll(
            `[data-chat-id="${data.chat_id}"] .msg-status.sent,` +
            `[data-chat-id="${data.chat_id}"] .msg-status.delivered`
        ).forEach(el => {
            el.classList.remove('sent', 'delivered');
            el.classList.add('read');
        });
    }

    // ─── تحميل الأجهزة المتصلة ──────────────────────────────────
    async loadDevices() {
        try {
            const res  = await fetch('/api/sync/devices');
            const data = await res.json();
            if (data.success) {
                this.devices = data.devices || [];
                this._renderDevices();
            }
        } catch (e) {
            console.error('SyncManager: فشل تحميل الأجهزة:', e);
        }
    }

    // ─── إنهاء جلسة جهاز ─────────────────────────────────────────
    async terminateDevice(sid) {
        if (!confirm('هل تريد إنهاء جلسة هذا الجهاز؟')) return;
        try {
            const res  = await fetch(`/api/sync/device/${encodeURIComponent(sid)}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                this._showToast('✅ تم إنهاء جلسة الجهاز', 'success');
                await this.loadDevices();
            } else {
                this._showToast('⚠️ ' + (data.message || 'فشل الإنهاء'), 'warning');
            }
        } catch (e) {
            this._showToast('❌ خطأ في الاتصال', 'error');
        }
    }

    // ─── مزامنة دورية ────────────────────────────────────────────
    async sync() {
        if (this.isSyncing) return;
        this.isSyncing = true;
        try {
            const res  = await fetch('/api/sync/status');
            const data = await res.json();
            if (data.success) {
                this.lastSyncTime = data.last_sync;
                this._updateSyncUI(true);
            }
        } catch (e) {
            this._updateSyncUI(false);
        } finally {
            this.isSyncing = false;
        }
    }

    // ─── مزامنة يدوية مع GitHub ─────────────────────────────────
    async syncToGitHub() {
        try {
            this._updateSyncUI(null, 'جاري الرفع إلى GitHub...');
            const res  = await fetch('/api/sync/github', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                this._showToast('☁️ تمت المزامنة مع GitHub', 'success');
                this._updateSyncUI(true);
            } else {
                this._showToast('⚠️ فشلت المزامنة', 'warning');
                this._updateSyncUI(false);
            }
        } catch (e) {
            this._updateSyncUI(false);
        }
    }

    // ─── تصدير البيانات ──────────────────────────────────────────
    async exportData() {
        try {
            const res  = await fetch('/api/sync/export');
            const data = await res.json();
            if (data.success) {
                const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
                const url  = URL.createObjectURL(blob);
                const a    = document.createElement('a');
                a.href     = url;
                a.download = `backup_${Date.now()}.json`;
                a.click();
                URL.revokeObjectURL(url);
                this._showToast('✅ تم تصدير البيانات', 'success');
            }
        } catch (e) {
            this._showToast('❌ فشل التصدير', 'error');
        }
    }

    // ─── استيراد البيانات ────────────────────────────────────────
    async importData(file) {
        try {
            const text = await file.text();
            const json = JSON.parse(text);
            const res  = await fetch('/api/sync/import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ data: json })
            });
            const data = await res.json();
            if (data.success) {
                this._showToast(`✅ تم استيراد ${data.imported} عنصر`, 'success');
            }
        } catch (e) {
            this._showToast('❌ فشل الاستيراد', 'error');
        }
    }

    // ─── تطبيق التغييرات الواردة ─────────────────────────────────
    _applyChanges(changes) {
        if (!changes) return;
        // تحديث إعدادات السمة
        if (changes.settings?.theme && window.setTheme) {
            window.setTheme(changes.settings.theme);
        }
        // إعادة رسم قائمة المحادثات إذا تغيّرت
        if (changes.chats && window.renderChatList) {
            window.renderChatList(changes.chats);
        }
    }

    // ─── واجهة الأجهزة ───────────────────────────────────────────
    _renderDevices() {
        const el = document.getElementById('devicesList');
        if (!el) return;

        if (!this.devices.length) {
            el.innerHTML = '<p style="color:#555;font-size:13px;text-align:center;padding:16px 0;">لا توجد أجهزة أخرى متصلة حالياً</p>';
            return;
        }

        el.innerHTML = this.devices.map(d => {
            const icon     = d.type === 'mobile' ? 'mobile-alt' : 'laptop';
            const onlineC  = d.is_online ? '#2ecc71' : '#555';
            const bgBadge  = d.is_online ? 'rgba(46,204,113,0.12)' : 'rgba(255,255,255,0.05)';
            const txtBadge = d.is_online ? '#2ecc71' : '#666';
            const statusTx = d.is_online ? '● متصل' : '○ غير متصل';
            const isCur    = (d.id === this.deviceId);

            const terminateBtn = (!isCur && d.is_online)
                ? `<button onclick="window.syncManager.terminateDevice('${d.sid}')"
                      style="background:rgba(231,76,60,0.15);color:#e74c3c;border:1px solid rgba(231,76,60,0.3);
                             border-radius:8px;padding:4px 10px;font-size:12px;cursor:pointer;
                             font-family:inherit;transition:background .2s;"
                      title="إنهاء هذه الجلسة">
                      <i class="fas fa-sign-out-alt"></i> إنهاء
                   </button>`
                : '';

            return `
            <div style="display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.04)">
                <i class="fas fa-${icon} fa-lg" style="color:${onlineC};width:24px;text-align:center;"></i>
                <div style="flex:1;min-width:0;">
                    <div style="font-size:14px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                        ${d.name || 'جهاز'}
                        ${isCur ? '<span style="color:#00d2ff;font-size:11px;margin-right:6px;">(هذا الجهاز)</span>' : ''}
                    </div>
                    <div style="font-size:12px;color:#777;margin-top:2px;">${d.last_active || ''}</div>
                </div>
                <span style="font-size:12px;padding:3px 10px;border-radius:12px;background:${bgBadge};color:${txtBadge};white-space:nowrap;">
                    ${statusTx}
                </span>
                ${terminateBtn}
            </div>`;
        }).join('');
    }

    // ─── تحديث مؤشر المزامنة ─────────────────────────────────────
    _updateSyncUI(success, msg = null) {
        const el = document.getElementById('syncIndicator');
        if (!el) return;
        if (success === null) {
            el.textContent = msg || '🔄 جاري المزامنة...';
            el.style.color = '#f9ca24';
        } else if (success) {
            const t = this.lastSyncTime || new Date().toLocaleTimeString('ar');
            el.innerHTML = `<i class="fas fa-check-circle" style="color:#2ecc71"></i> متزامن — ${t}`;
            el.style.color = '#2ecc71';
        } else {
            el.innerHTML = `<i class="fas fa-exclamation-circle" style="color:#f9ca24"></i> فشل — جاري المحاولة`;
            el.style.color = '#f9ca24';
        }
    }

    // ─── إشعار بسيط ──────────────────────────────────────────────
    _showToast(msg, type = 'info') {
        if (window.showToast) { window.showToast(msg, type); return; }
        console.log(`[SyncManager] ${msg}`);
    }
}

// ─── تصدير عام ──────────────────────────────────────────────────
window.syncManager = new SyncManager();
document.addEventListener('DOMContentLoaded', () => {
    // تأخير قصير للسماح للـ Socket.IO بالاتصال أولاً
    setTimeout(() => window.syncManager.init(), 1500);
});
