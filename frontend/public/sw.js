const CACHE = 'broke-proof-v1';
self.addEventListener('install', event => event.waitUntil(caches.open(CACHE)));
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
