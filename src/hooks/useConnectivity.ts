import { useState, useEffect } from 'react';
import { setupConnectivityListeners, isOnline } from '../utils/serviceWorker';

export interface ConnectivityState {
  isOnline: boolean;
  isOffline: boolean;
  connectionType: string | null;
  effectiveType: string | null;
  downlink: number | null;
  rtt: number | null;
}

export function useConnectivity() {
  const [connectivity, setConnectivity] = useState<ConnectivityState>(() => ({
    isOnline: isOnline(),
    isOffline: !isOnline(),
    connectionType: null,
    effectiveType: null,
    downlink: null,
    rtt: null
  }));

  useEffect(() => {
    const updateConnectivity = () => {
      const online = navigator.onLine;
      const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
      
      setConnectivity({
        isOnline: online,
        isOffline: !online,
        connectionType: connection?.type || null,
        effectiveType: connection?.effectiveType || null,
        downlink: connection?.downlink || null,
        rtt: connection?.rtt || null
      });
    };

    // Initial update
    updateConnectivity();

    // Setup listeners
    const cleanup = setupConnectivityListeners({
      onOnline: updateConnectivity,
      onOffline: updateConnectivity
    });

    // Listen for connection changes
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
    if (connection) {
      connection.addEventListener('change', updateConnectivity);
    }

    return () => {
      cleanup?.();
      if (connection) {
        connection.removeEventListener('change', updateConnectivity);
      }
    };
  }, []);

  return connectivity;
}

// Hook for detecting slow connections
export function useSlowConnection(threshold: number = 1.5) {
  const connectivity = useConnectivity();
  
  const isSlowConnection = connectivity.effectiveType === 'slow-2g' || 
                          connectivity.effectiveType === '2g' ||
                          (connectivity.downlink !== null && connectivity.downlink < threshold);
  
  return {
    ...connectivity,
    isSlowConnection
  };
}

// Hook for offline-first data management
export function useOfflineFirst<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: {
    staleTime?: number;
    cacheTime?: number;
    refetchOnReconnect?: boolean;
  } = {}
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [isStale, setIsStale] = useState(false);
  const connectivity = useConnectivity();

  const {
    staleTime = 5 * 60 * 1000, // 5 minutes
    cacheTime = 24 * 60 * 60 * 1000, // 24 hours
    refetchOnReconnect = true
  } = options;

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Try to load from cache first
        const cachedData = await getCachedData<T>(key);
        if (cachedData) {
          setData(cachedData.data);
          setIsStale(Date.now() - cachedData.timestamp > staleTime);
          setIsLoading(false);

          // If data is fresh enough and we're offline, don't fetch
          if (!connectivity.isOnline && Date.now() - cachedData.timestamp < cacheTime) {
            return;
          }
        }

        // If online, try to fetch fresh data
        if (connectivity.isOnline) {
          const freshData = await fetcher();
          setData(freshData);
          setIsStale(false);
          
          // Cache the fresh data
          await setCachedData(key, freshData);
        }
      } catch (err) {
        setError(err as Error);
        
        // If we have cached data, use it even if stale
        const cachedData = await getCachedData<T>(key);
        if (cachedData) {
          setData(cachedData.data);
          setIsStale(true);
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [key, connectivity.isOnline]);

  // Refetch when coming back online
  useEffect(() => {
    if (connectivity.isOnline && refetchOnReconnect && data) {
      const refetch = async () => {
        try {
          const freshData = await fetcher();
          setData(freshData);
          setIsStale(false);
          await setCachedData(key, freshData);
        } catch (err) {
          console.error('Refetch on reconnect failed:', err);
        }
      };
      
      refetch();
    }
  }, [connectivity.isOnline, refetchOnReconnect]);

  const refetch = async () => {
    if (!connectivity.isOnline) {
      throw new Error('Cannot refetch while offline');
    }
    
    try {
      setIsLoading(true);
      const freshData = await fetcher();
      setData(freshData);
      setIsStale(false);
      await setCachedData(key, freshData);
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    data,
    isLoading,
    error,
    isStale,
    refetch,
    isOffline: connectivity.isOffline
  };
}

// IndexedDB helpers for caching
async function getCachedData<T>(key: string): Promise<{ data: T; timestamp: number } | null> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('bmtc-cache', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['cache'], 'readonly');
      const store = transaction.objectStore('cache');
      const getRequest = store.get(key);
      
      getRequest.onsuccess = () => resolve(getRequest.result || null);
      getRequest.onerror = () => reject(getRequest.error);
    };
    
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('cache')) {
        db.createObjectStore('cache', { keyPath: 'key' });
      }
    };
  });
}

async function setCachedData<T>(key: string, data: T): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('bmtc-cache', 1);
    
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['cache'], 'readwrite');
      const store = transaction.objectStore('cache');
      
      const putRequest = store.put({
        key,
        data,
        timestamp: Date.now()
      });
      
      putRequest.onsuccess = () => resolve();
      putRequest.onerror = () => reject(putRequest.error);
    };
  });
}