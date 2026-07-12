// PWA Service Worker — 缓存静态资源
const CACHE_NAME = "zettaranc-v1";
const CACHE_URLS = ["/", "/static/css/app.css", "/static/js/api.js"];

self.addEventListener("install", (e) => {
    e.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(CACHE_URLS)));
});

self.addEventListener("fetch", (e) => {
    e.respondWith(
        caches.match(e.request).then((response) => response || fetch(e.request))
    );
});
