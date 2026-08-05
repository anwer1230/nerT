/**
 * pwa_install.js — آلية التثبيت كتطبيق PWA
 * تعمل على Android (beforeinstallprompt) وiOS (دليل يدوي)
 */
'use strict';

(function () {

  // ── تسجيل Service Worker ──────────────────────────────────────
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/sw.js', { scope: '/' })
        .then(function (reg) {
          // تحقق من وجود تحديث
          reg.addEventListener('updatefound', function () {
            var newWorker = reg.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', function () {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  // يمكن إضافة إشعار "تحديث متوفر" هنا إن أردت
                }
              });
            }
          });
        })
        .catch(function (err) {
          console.warn('[PWA] Service Worker registration failed:', err);
        });
    });
  }

  // ── حدث beforeinstallprompt (Android / Chrome / Edge) ────────
  var _deferredPrompt = null;
  var _banner = null;
  var _shown = false;

  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    _deferredPrompt = e;
    if (!_shown) {
      setTimeout(showBanner, 1500); // تأخير بسيط حتى تكتمل الصفحة
    }
  });

  // ── تحقق iOS Safari ─────────────────────────────────────────
  function isIOS() {
    return /iphone|ipad|ipod/i.test(navigator.userAgent);
  }

  function isInStandaloneMode() {
    return (window.matchMedia('(display-mode: standalone)').matches) ||
           (window.navigator.standalone === true);
  }

  // ── إنشاء البنر ──────────────────────────────────────────────
  function createBanner() {
    var banner = document.createElement('div');
    banner.id = 'pwa-install-banner';

    var isIos = isIOS();
    var btnLabel = isIos ? '📋 كيف أضيفه؟' : '⬇️ تثبيت التطبيق';
    var msgText  = isIos
      ? 'أضف التطبيق إلى الشاشة الرئيسية للوصول السريع'
      : 'ثبّت التطبيق على جهازك للوصول إليه بدون إنترنت';

    banner.innerHTML =
      '<div class="pwa-banner-inner">' +
        '<img src="/static/icons/icon-192.png" class="pwa-banner-icon" alt="App Icon">' +
        '<div class="pwa-banner-text">' +
          '<strong>مركز سرعة إنجاز</strong>' +
          '<span>' + msgText + '</span>' +
        '</div>' +
        '<div class="pwa-banner-actions">' +
          '<button id="pwa-install-btn" class="pwa-btn-install">' + btnLabel + '</button>' +
          '<button id="pwa-dismiss-btn" class="pwa-btn-dismiss" title="إغلاق">✕</button>' +
        '</div>' +
      '</div>';

    return banner;
  }

  // ── إضافة الأنماط CSS ────────────────────────────────────────
  function injectStyles() {
    if (document.getElementById('pwa-install-style')) return;
    var style = document.createElement('style');
    style.id = 'pwa-install-style';
    style.textContent = [
      '#pwa-install-banner {',
      '  position: fixed;',
      '  bottom: 0; left: 0; right: 0;',
      '  z-index: 99999;',
      '  padding: 0 0 env(safe-area-inset-bottom, 0) 0;',
      '  animation: pwa-slide-up 0.4s cubic-bezier(0.4,0,0.2,1) forwards;',
      '}',
      '@keyframes pwa-slide-up {',
      '  from { transform: translateY(100%); opacity: 0; }',
      '  to   { transform: translateY(0);    opacity: 1; }',
      '}',
      '#pwa-install-banner.pwa-hiding {',
      '  animation: pwa-slide-down 0.35s cubic-bezier(0.4,0,0.2,1) forwards;',
      '}',
      '@keyframes pwa-slide-down {',
      '  from { transform: translateY(0);    opacity: 1; }',
      '  to   { transform: translateY(100%); opacity: 0; }',
      '}',
      '.pwa-banner-inner {',
      '  display: flex;',
      '  align-items: center;',
      '  gap: 12px;',
      '  padding: 14px 16px;',
      '  background: #1e3c78;',
      '  box-shadow: 0 -4px 24px rgba(0,0,0,0.35);',
      '  border-radius: 18px 18px 0 0;',
      '  direction: rtl;',
      '}',
      '.pwa-banner-icon {',
      '  width: 48px; height: 48px;',
      '  border-radius: 12px;',
      '  flex-shrink: 0;',
      '  box-shadow: 0 2px 8px rgba(0,0,0,0.3);',
      '}',
      '.pwa-banner-text {',
      '  flex: 1;',
      '  display: flex;',
      '  flex-direction: column;',
      '  gap: 2px;',
      '  min-width: 0;',
      '}',
      '.pwa-banner-text strong {',
      '  font-size: 14px;',
      '  font-weight: 700;',
      '  color: #ffffff;',
      '  white-space: nowrap;',
      '  overflow: hidden;',
      '  text-overflow: ellipsis;',
      '}',
      '.pwa-banner-text span {',
      '  font-size: 12px;',
      '  color: rgba(255,255,255,0.75);',
      '  line-height: 1.3;',
      '}',
      '.pwa-banner-actions {',
      '  display: flex;',
      '  align-items: center;',
      '  gap: 8px;',
      '  flex-shrink: 0;',
      '}',
      '.pwa-btn-install {',
      '  background: #2AABEE;',
      '  color: #fff;',
      '  border: none;',
      '  border-radius: 20px;',
      '  padding: 8px 16px;',
      '  font-size: 13px;',
      '  font-weight: 600;',
      '  cursor: pointer;',
      '  white-space: nowrap;',
      '  font-family: inherit;',
      '  transition: background 0.2s, transform 0.15s;',
      '  -webkit-tap-highlight-color: transparent;',
      '}',
      '.pwa-btn-install:active { transform: scale(0.96); background: #179CDE; }',
      '.pwa-btn-dismiss {',
      '  background: rgba(255,255,255,0.15);',
      '  color: rgba(255,255,255,0.85);',
      '  border: none;',
      '  border-radius: 50%;',
      '  width: 32px; height: 32px;',
      '  font-size: 14px;',
      '  cursor: pointer;',
      '  display: flex;',
      '  align-items: center;',
      '  justify-content: center;',
      '  flex-shrink: 0;',
      '  font-family: inherit;',
      '  transition: background 0.2s;',
      '  -webkit-tap-highlight-color: transparent;',
      '}',
      '.pwa-btn-dismiss:active { background: rgba(255,255,255,0.3); }',

      /* ── iOS instruction sheet ── */
      '#pwa-ios-sheet {',
      '  position: fixed;',
      '  bottom: 0; left: 0; right: 0;',
      '  z-index: 100000;',
      '  background: #1e3c78;',
      '  border-radius: 20px 20px 0 0;',
      '  padding: 20px 20px calc(20px + env(safe-area-inset-bottom, 0));',
      '  box-shadow: 0 -4px 32px rgba(0,0,0,0.4);',
      '  color: #fff;',
      '  direction: rtl;',
      '  animation: pwa-slide-up 0.4s cubic-bezier(0.4,0,0.2,1) forwards;',
      '}',
      '#pwa-ios-sheet h3 { font-size: 17px; font-weight: 700; margin: 0 0 12px; }',
      '.pwa-ios-steps { list-style: none; padding: 0; margin: 0 0 16px; display: flex; flex-direction: column; gap: 12px; }',
      '.pwa-ios-steps li { display: flex; align-items: center; gap: 10px; font-size: 14px; line-height: 1.4; }',
      '.pwa-ios-steps .step-num { background: #2AABEE; color: #fff; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px; flex-shrink: 0; }',
      '.pwa-ios-close { width: 100%; padding: 12px; background: rgba(255,255,255,0.15); border: none; border-radius: 12px; color: #fff; font-size: 15px; font-weight: 600; cursor: pointer; font-family: inherit; }',
    ].join('\n');
    document.head.appendChild(style);
  }

  // ── عرض البنر ────────────────────────────────────────────────
  function showBanner() {
    if (_shown || isInStandaloneMode()) return;
    _shown = true;

    injectStyles();
    _banner = createBanner();
    document.body.appendChild(_banner);

    document.getElementById('pwa-install-btn').addEventListener('click', onInstallClick);
    document.getElementById('pwa-dismiss-btn').addEventListener('click', hideBanner);
  }

  function hideBanner() {
    if (!_banner) return;
    _banner.classList.add('pwa-hiding');
    _banner.addEventListener('animationend', function () {
      if (_banner && _banner.parentNode) _banner.parentNode.removeChild(_banner);
      _banner = null;
    }, { once: true });
  }

  // ── iOS: ورقة التعليمات ──────────────────────────────────────
  function showIOSSheet() {
    if (document.getElementById('pwa-ios-sheet')) return;
    injectStyles();

    var sheet = document.createElement('div');
    sheet.id = 'pwa-ios-sheet';
    sheet.innerHTML =
      '<h3>📱 أضف التطبيق إلى الشاشة الرئيسية</h3>' +
      '<ol class="pwa-ios-steps">' +
        '<li><span class="step-num">1</span><span>اضغط على زر المشاركة <strong>⎙</strong> في شريط Safari السفلي</span></li>' +
        '<li><span class="step-num">2</span><span>مرِّر للأسفل واختر <strong>"إضافة إلى الشاشة الرئيسية"</strong></span></li>' +
        '<li><span class="step-num">3</span><span>اضغط <strong>إضافة</strong> — سيظهر التطبيق على شاشتك مباشرة</span></li>' +
      '</ol>' +
      '<button class="pwa-ios-close" id="pwa-ios-close-btn">فهمت، شكراً ✓</button>';

    document.body.appendChild(sheet);
    document.getElementById('pwa-ios-close-btn').addEventListener('click', function () {
      if (sheet.parentNode) sheet.parentNode.removeChild(sheet);
    });
  }

  // ── معالج زر التثبيت ─────────────────────────────────────────
  function onInstallClick() {
    if (isIOS()) {
      hideBanner();
      setTimeout(showIOSSheet, 400);
      return;
    }

    if (!_deferredPrompt) return;

    hideBanner();
    _deferredPrompt.prompt();
    _deferredPrompt.userChoice.then(function (choice) {
      _deferredPrompt = null;
    });
  }

  // ── iOS: اعرض البنر بعد 2.5 ثانية إذا لم يُثبَّت بعد ───────
  if (isIOS() && !isInStandaloneMode()) {
    // لا نُظهر في كل زيارة — نحفظ في localStorage
    var iosKey = 'pwa_ios_banner_shown';
    var lastShown = parseInt(localStorage.getItem(iosKey) || '0', 10);
    var now = Date.now();
    var ONE_DAY = 86400000;

    if (now - lastShown > ONE_DAY) {
      localStorage.setItem(iosKey, String(now));
      setTimeout(showBanner, 2500);
    }
  }

  // ── إذا ثُبِّت التطبيق: أخفِ البنر ──────────────────────────
  window.addEventListener('appinstalled', function () {
    hideBanner();
    _deferredPrompt = null;
  });

})();
