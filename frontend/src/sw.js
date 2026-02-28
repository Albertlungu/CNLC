const CACHE_NAME = "discovereye-v14";
const STATIC_ASSETS = [
    "/agent.html",
    "/businesses.html",
    "/business-detail.html",
    "/deals.html",
    "/friends.html",
    "/saved.html",
    "/trending.html",
    "/map.html",
    "/reservations.html",
    "/profile.html",
    "/auth.html",
    "/css/agent.css",
    "/css/agent-widget.css",
    "/css/businesses.css",
    "/css/business-detail.css",
    "/css/deals.css",
    "/css/friends.css",
    "/css/saved.css",
    "/css/trending.css",
    "/css/map.css",
    "/css/reservations.css",
    "/css/notifications.css",
    "/css/profile.css",
    "/css/auth-styles.css",
    "/css/theme.css",
    "/css/mobile.css",
    "/css/mobile-nav.css",
    "/css/voice-control.css",
    "/css/tts.css",
    "/js/api-client.js",
    "/js/agent.js",
    "/js/agent-widget.js",
    "/js/voice-control.js",
    "/js/tts.js",
    "/js/theme.js",
    "/js/mobile.js",
    "/js/pwa.js",
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener("fetch", (event) => {
    const url = new URL(event.request.url);

    // Let cross-origin requests (e.g. backend API on a different port) bypass
    // the service worker entirely so they reach the network directly.
    if (url.origin !== self.location.origin) return;

    // Network-first for API calls, JS, CSS, and HTML (so code updates take effect immediately)
    if (url.pathname.startsWith("/api/") || url.pathname.endsWith(".js") || url.pathname.endsWith(".css") || url.pathname.endsWith(".html") || url.pathname === "/") {
        event.respondWith(
            fetch(event.request).then((response) => {
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                }
                return response;
            }).catch(() => caches.match(event.request))
        );
        return;
    }

    // Cache-first for other static assets (HTML, images, fonts)
    event.respondWith(
        caches.match(event.request).then((cached) => {
            return cached || fetch(event.request).then((response) => {
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                }
                return response;
            });
        })
    );
});
