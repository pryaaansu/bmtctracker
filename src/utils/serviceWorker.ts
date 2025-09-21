// Service Worker registration and management utilities

export interface ServiceWorkerConfig {
  onUpdate?: (registration: ServiceWorkerRegistration) => void;
  onSuccess?: (registration: ServiceWorkerRegistration) => void;
  onOffline?: () => void;
  onOnline?: () => void;
}

// Register service worker
export async function registerServiceWorker(config: ServiceWorkerConfig = {}): Promise<void> {
  if (!('serviceWorker' in navigator)) {
    console.warn('Service Worker not supported in this browser');
    return;
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/'
    });

    console.log('Service Worker registered successfully:', registration);

    // Handle updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      if (!newWorker) return;

      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          // New content is available
          config.onUpdate?.(registration);
        }
      });
    });

    // Check if service worker is ready
    if (registration.active) {
      config.onSuccess?.(registration);
    }

    // Listen for messages from service worker
    navigator.serviceWorker.addEventListener('message', (event) => {
      console.log('Message from Service Worker:', event.data);
    });

  } catch (error) {
    console.error('Service Worker registration failed:', error);
  }
}

// Unregister service worker
export async function unregisterServiceWorker(): Promise<boolean> {
  if (!('serviceWorker' in navigator)) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (registration) {
      const result = await registration.unregister();
      console.log('Service Worker unregistered:', result);
      return result;
    }
    return false;
  } catch (error) {
    console.error('Service Worker unregistration failed:', error);
    return false;
  }
}

// Check if app is running in standalone mode (PWA)
export function isStandalone(): boolean {
  return window.matchMedia('(display-mode: standalone)').matches ||
         (window.navigator as any).standalone === true;
}

// Check if device is online
export function isOnline(): boolean {
  return navigator.onLine;
}

// Setup online/offline event listeners
export function setupConnectivityListeners(config: ServiceWorkerConfig): void {
  const handleOnline = () => {
    console.log('Connection restored');
    config.onOnline?.();
  };

  const handleOffline = () => {
    console.log('Connection lost');
    config.onOffline?.();
  };

  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);

  // Return cleanup function
  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  };
}

// Request background sync
export async function requestBackgroundSync(tag: string): Promise<void> {
  if (!('serviceWorker' in navigator) || !('sync' in window.ServiceWorkerRegistration.prototype)) {
    console.warn('Background Sync not supported');
    return;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    await registration.sync.register(tag);
    console.log('Background sync registered:', tag);
  } catch (error) {
    console.error('Background sync registration failed:', error);
  }
}

// Store offline action for later sync
export async function storeOfflineAction(action: {
  url: string;
  method: string;
  headers?: Record<string, string>;
  body?: string;
}): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('bmtc-offline', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['actions'], 'readwrite');
      const store = transaction.objectStore('actions');
      
      const addRequest = store.add({
        ...action,
        timestamp: Date.now()
      });
      
      addRequest.onsuccess = () => {
        resolve();
        // Request background sync
        requestBackgroundSync('sync-offline-actions');
      };
      addRequest.onerror = () => reject(addRequest.error);
    };
    
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('actions')) {
        db.createObjectStore('actions', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

// Clear all caches
export async function clearAllCaches(): Promise<void> {
  if (!('caches' in window)) {
    return;
  }

  try {
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames.map(cacheName => caches.delete(cacheName))
    );
    console.log('All caches cleared');
  } catch (error) {
    console.error('Failed to clear caches:', error);
  }
}

// Get cache size information
export async function getCacheInfo(): Promise<{
  staticSize: number;
  dynamicSize: number;
  totalSize: number;
}> {
  if (!('caches' in window)) {
    return { staticSize: 0, dynamicSize: 0, totalSize: 0 };
  }

  try {
    const staticCache = await caches.open('bmtc-static-v1');
    const dynamicCache = await caches.open('bmtc-dynamic-v1');
    
    const staticKeys = await staticCache.keys();
    const dynamicKeys = await dynamicCache.keys();
    
    return {
      staticSize: staticKeys.length,
      dynamicSize: dynamicKeys.length,
      totalSize: staticKeys.length + dynamicKeys.length
    };
  } catch (error) {
    console.error('Failed to get cache info:', error);
    return { staticSize: 0, dynamicSize: 0, totalSize: 0 };
  }
}

// Update service worker
export async function updateServiceWorker(): Promise<void> {
  if (!('serviceWorker' in navigator)) {
    return;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (registration) {
      await registration.update();
      console.log('Service Worker update requested');
    }
  } catch (error) {
    console.error('Service Worker update failed:', error);
  }
}