const CACHE = 'apk-store-v1';
const FILES = ['./', './index.html', './manifest.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  if(e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).then(r => {
      if(r && r.status === 200 && r.type === 'basic'){
        const cl = r.clone();
        caches.open(CACHE).then(c => c.put(e.request, cl));
      }
      return r;
    }).catch(() => caches.match(e.request).then(c => c || caches.match('./index.html')))
  );
});
