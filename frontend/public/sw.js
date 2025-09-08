const CACHE_NAME = 'chatconnect-v1';
const STATIC_CACHE = 'static-v1';
const DYNAMIC_CACHE = 'dynamic-v1';

// Files to cache immediately
const STATIC_FILES = [
  '/',
  '/favicon.ico',
  '/manifest.json',
  '/_next/static/css/app.css',
  '/_next/static/js/app.js',
];

// Install event - cache static files
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(STATIC_FILES);
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch event - serve from cache when possible
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Bypass SW for SSE requests (text/event-stream)
  const accept = request.headers.get('accept') || '';
  if (accept.includes('text/event-stream')) {
    return; // let browser handle SSE directly
  }

  // Handle API requests with caching strategy
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/chat/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Handle static assets with cache-first strategy
  if (request.destination === 'script' || request.destination === 'style' || request.destination === 'image') {
    event.respondWith(handleStaticRequest(request));
    return;
  }

  // Handle HTML pages with network-first strategy
  if (request.destination === 'document') {
    event.respondWith(handleDocumentRequest(request));
    return;
  }
});

// Handle API requests with stale-while-revalidate
async function handleApiRequest(request) {
  const cache = await caches.open(DYNAMIC_CACHE);
  const cachedResponse = await cache.match(request);

  const networkPromise = fetch(request)
    .then(async (networkResponse) => {
      if (networkResponse && networkResponse.ok) {
        await cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    })
    .catch(() => null);

  // Serve cached immediately if present, and update in background
  if (cachedResponse) {
    // Kick off network update but don't await it
    networkPromise.catch(() => {});
    return cachedResponse;
  }

  // No cache: fall back to network
  const networkResponse = await networkPromise;
  if (networkResponse) return networkResponse;

  // Offline fallback for chat endpoints
  if (request.url.includes('/chat/')) {
    return new Response(JSON.stringify({
      error: 'Offline',
      message: 'You are currently offline. Please check your connection.'
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  return new Response('Offline', { status: 503 });
}

// Handle static assets with cache-first strategy
async function handleStaticRequest(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    // Return a default response for critical assets
    if (request.destination === 'script') {
      return new Response('console.log("Asset not available offline");', {
        headers: { 'Content-Type': 'application/javascript' }
      });
    }
    throw error;
  }
}

// Handle HTML pages with network-first strategy
async function handleDocumentRequest(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page
    return caches.match('/offline.html') || new Response('You are offline', {
      status: 503,
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

// Background sync for offline messages
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync-messages') {
    event.waitUntil(syncOfflineMessages());
  }
});

// Sync offline messages when connection is restored
async function syncOfflineMessages() {
  try {
    const cache = await caches.open(DYNAMIC_CACHE);
    const requests = await cache.keys();
    
    for (const request of requests) {
      if (request.url.includes('/chat/') && request.method === 'POST') {
        try {
          const response = await fetch(request);
          if (response.ok) {
            await cache.delete(request);
          }
        } catch (error) {
          console.log('Failed to sync message:', error);
        }
      }
    }
  } catch (error) {
    console.log('Background sync failed:', error);
  }
}

// Push notification handling
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New message received',
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    }
  };
  
  event.waitUntil(
    self.registration.showNotification('ChatConnect', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow('/')
  );
});
