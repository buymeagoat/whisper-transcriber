/**
 * Service Worker for Whisper Transcriber Frontend
 * Provides caching and offline capabilities
 */

const CACHE_NAME = 'whisper-transcriber-v1.0.0';
const STATIC_CACHE_NAME = 'whisper-static-v1.0.0';

// Assets to cache immediately
const STATIC_ASSETS = [
  '/static/',
  '/static/index.html',
  '/static/assets/js/',
  '/static/assets/css/',
  '/static/assets/images/'
];

// API endpoints to cache
const CACHEABLE_APIS = [
  '/health',
  '/metrics',
  '/admin/stats',
  '/models'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .catch((error) => {
        console.error('Service Worker: Failed to cache static assets', error);
      })
  );
  
  // Activate immediately
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && cacheName !== STATIC_CACHE_NAME) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        // Take control of all pages
        return self.clients.claim();
      })
  );
});

// Fetch event - implement caching strategy
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Handle static assets with cache-first strategy
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request)
        .then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          
          return fetch(request)
            .then((response) => {
              // Only cache successful responses
              if (response.status === 200) {
                const responseClone = response.clone();
                caches.open(STATIC_CACHE_NAME)
                  .then((cache) => {
                    cache.put(request, responseClone);
                  });
              }
              return response;
            })
            .catch(() => {
              // Return offline fallback for HTML requests
              if (request.headers.get('accept').includes('text/html')) {
                return new Response(
                  `<!DOCTYPE html>
                   <html>
                     <head>
                       <title>Offline - Whisper Transcriber</title>
                       <style>
                         body { 
                           font-family: sans-serif; 
                           text-align: center; 
                           background: #18181b; 
                           color: #fff; 
                           padding: 2rem; 
                         }
                         .offline-message { 
                           max-width: 400px; 
                           margin: 2rem auto; 
                         }
                       </style>
                     </head>
                     <body>
                       <div class="offline-message">
                         <h1>You're offline</h1>
                         <p>Please check your internet connection and try again.</p>
                         <button onclick="window.location.reload()">Retry</button>
                       </div>
                     </body>
                   </html>`,
                  {
                    headers: { 'Content-Type': 'text/html' }
                  }
                );
              }
            });
        })
    );
    return;
  }
  
  // Handle API requests with network-first strategy
  if (url.pathname.startsWith('/api/') || CACHEABLE_APIS.some(api => url.pathname.startsWith(api))) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful API responses for a short time
          if (response.status === 200 && CACHEABLE_APIS.some(api => url.pathname.startsWith(api))) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(request, responseClone);
              });
          }
          return response;
        })
        .catch(() => {
          // Try to serve from cache if network fails
          return caches.match(request)
            .then((cachedResponse) => {
              if (cachedResponse) {
                return cachedResponse;
              }
              
              // Return offline API response
              return new Response(
                JSON.stringify({
                  error: 'offline',
                  message: 'This request failed because you are offline'
                }),
                {
                  status: 503,
                  headers: { 'Content-Type': 'application/json' }
                }
              );
            });
        })
    );
    return;
  }
  
  // For all other requests, use default browser behavior
});

// Message event - handle messages from main thread
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
      .then(() => {
        event.ports[0].postMessage({ success: true });
      })
      .catch((error) => {
        event.ports[0].postMessage({ success: false, error: error.message });
      });
  }
});

// Background sync for offline actions (if supported)
if ('sync' in self.registration) {
  self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
      console.log('Service Worker: Background sync triggered');
      // Handle background sync logic here
    }
  });
}

// Push notifications (if needed in future)
if ('push' in self.registration) {
  self.addEventListener('push', (event) => {
    const options = {
      body: event.data ? event.data.text() : 'New notification',
      icon: '/static/icon-192x192.png',
      badge: '/static/badge-72x72.png',
      data: {
        url: '/static/'
      }
    };
    
    event.waitUntil(
      self.registration.showNotification('Whisper Transcriber', options)
    );
  });
}

console.log('Service Worker: Loaded and ready');
