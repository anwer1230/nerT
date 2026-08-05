/**
 * push_manager.js — إدارة Web Push Notifications
 * مركز سرعة إنجاز
 */
'use strict';

(function() {
    // التحقق من دعم Service Worker و Push API
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.warn('Push notifications not supported in this browser');
        return;
    }

    // تسجيل Service Worker
    navigator.serviceWorker.register('/static/pwa-sw.js')
        .then(function(reg) {
            console.log('✅ Service Worker registered:', reg.scope);
        })
        .catch(function(err) {
            console.warn('Service Worker registration failed:', err);
        });

    // طلب إذن الإشعارات
    window.requestPushPermission = async function() {
        try {
            const perm = await Notification.requestPermission();
            if (perm === 'granted') {
                await subscribePush();
            }
        } catch (e) {
            console.warn('Push permission error:', e);
        }
    };

    // الاشتراك في Push
    async function subscribePush() {
        try {
            const reg = await navigator.serviceWorker.ready;
            // جلب مفتاح VAPID من الخادم
            const keyResp = await fetch('/api/push/vapid-public-key');
            const keyData = await keyResp.json();
            if (!keyData.publicKey) return;

            const vapidKey = urlBase64ToUint8Array(keyData.publicKey);
            const subscription = await reg.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: vapidKey
            });

            // إرسال الاشتراك للخادم
            await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(subscription)
            });

            console.log('✅ Push subscription active');
        } catch (e) {
            console.warn('Push subscription failed:', e);
        }
    }

    // تحويل مفتاح base64url إلى Uint8Array
    function urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    // تهيئة تلقائية عند تحميل الصفحة
    window.addEventListener('load', function() {
        if (Notification.permission === 'default') {
            // لا نطلب الإذن تلقائياً — ننتظر مشاركة المستخدم
        } else if (Notification.permission === 'granted') {
            subscribePush().catch(() => {});
        }
    });
})();
