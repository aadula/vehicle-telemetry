const CACHE_NAME = "vehicle-telemetry-v1";
const ASSETS = [
  "./",
  "./index.html",
  "./style.css",
  "./app.js",
  "./manifest.json"
];

// Install: cache core assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
});

// Activate: cleanup old caches if we version later
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      )
    )
  );
});

// Fetch: try cache first, then network
self.addEventListener("fetch", (event) => {
  const req = event.request;

  // Don't try to cache WebSocket or non-GET
  if (req.url.startsWith("ws://") || req.method !== "GET") {
    return;
  }

  event.respondWith(
    caches.match(req).then((cached) => {
      return (
        cached ||
        fetch(req).catch(() => {
          // optional: we could serve a fallback page here
        })
      );
    })
  );
});
