// A VERSAO é carimbada com o commit pelo deploy; o celular percebe a atualização sozinho.
const VERSAO = 'dev';
const CACHE = 'paiva-ai-' + VERSAO;
const ARQUIVOS = [
  './',
  'index.html',
  'css/app.css',
  'js/app.js',
  'manifest.webmanifest',
  'fonts/bricolage-grotesque-latin-wght-normal.woff2',
  'fonts/hanken-grotesk-latin-wght-normal.woff2',
  'icons/icon-192.png',
  'icons/icon-512.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ARQUIVOS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request)));
});
