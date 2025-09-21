import { useState, useEffect, useCallback } from 'react';
import { useConnectivity } from './useConnectivity';

export interface OfflineDataItem {
  id: string;
  data: any;
  timestamp: number;
  expiresAt: number;
  version: string;
}

export interface UseOfflineDataOptions {
  storeName: string;
  defaultExpiry?: number; // milliseconds
  syncOnReconnect?: boolean;
}

export function useOfflineData<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: UseOfflineDataOptions
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [isStale, setIsStale] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);
  
  const connectivity = useConnectivity();
  const {
    storeName,
    defaultExpiry = 24 * 60 * 60 * 1000, // 24 hours
    syncOnReconnect = true
  } = options;

  // Initialize IndexedDB
  const initDB = useCallback((): Promise<IDBDatabase> => {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(`bmtc-${storeName}`, 1);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
      
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains('data')) {
          const store = db.createObjectStore('data', { keyPath: 'id' });
          store.createIndex('timestamp', 'timestamp');
          store.createIndex('expiresAt', 'expiresAt');
        }
      };
    });
  }, [storeName]);

  // Store data offline
  const storeOffline = useCallback(async (itemData: T): Promise<void> => {
    try {
      const db = await initDB();
      const transaction = db.transaction(['data'], 'readwrite');
      const store = transaction.objectStore('data');
      
      const item: OfflineDataItem = {
        id: key,
        data: itemData,
        timestamp: Date.now(),
        expiresAt: Date.now() + defaultExpiry,
        version: '1.0'
      };
      
      await new Promise<void>((resolve, reject) => {
        const request = store.put(item);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });
      
      setLastUpdated(item.timestamp);
    } catch (err) {
      console.error('Failed to store data offline:', err);
    }
  }, [key, defaultExpiry, initDB]);

  // Retrieve data from offline storage
  const getOffline = useCallback(async (): Promise<T | null> => {
    try {
      const db = await initDB();
      const transaction = db.transaction(['data'], 'readonly');
      const store = transaction.objectStore('data');
      
      const item = await new Promise<OfflineDataItem | null>((resolve, reject) => {
        const request = store.get(key);
        request.onsuccess = () => resolve(request.result || null);
        request.onerror = () => reject(request.error);
      });
      
      if (!item) return null;
      
      // Check if data has expired
      if (item.expiresAt < Date.now()) {
        await deleteOffline();
        return null;
      }
      
      setLastUpdated(item.timestamp);
      setIsStale(Date.now() - item.timestamp > defaultExpiry / 2);
      
      return item.data;
    } catch (err) {
      console.error('Failed to get data offline:', err);
      return null;
    }
  }, [key, defaultExpiry, initDB]);

  // Delete data from offline storage
  const deleteOffline = useCallback(async (): Promise<void> => {
    try {
      const db = await initDB();
      const transaction = db.transaction(['data'], 'readwrite');
      const store = transaction.objectStore('data');
      
      await new Promise<void>((resolve, reject) => {
        const request = store.delete(key);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });
    } catch (err) {
      console.error('Failed to delete data offline:', err);
    }
  }, [key, initDB]);

  // Fetch fresh data
  const fetchFresh = useCallback(async (): Promise<T | null> => {
    if (!connectivity.isOnline) {
      return null;
    }

    try {
      setError(null);
      const freshData = await fetcher();
      await storeOffline(freshData);
      setIsStale(false);
      return freshData;
    } catch (err) {
      setError(err as Error);
      return null;
    }
  }, [connectivity.isOnline, fetcher, storeOffline]);

  // Load data (offline first, then online if needed)
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Try offline first
      const offlineData = await getOffline();
      if (offlineData) {
        setData(offlineData);
        setIsLoading(false);
        
        // If online and data is stale, fetch fresh data in background
        if (connectivity.isOnline && isStale) {
          const freshData = await fetchFresh();
          if (freshData) {
            setData(freshData);
          }
        }
        return;
      }

      // If no offline data and online, fetch fresh
      if (connectivity.isOnline) {
        const freshData = await fetchFresh();
        if (freshData) {
          setData(freshData);
        }
      }
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [getOffline, connectivity.isOnline, isStale, fetchFresh]);

  // Refresh data (force fetch from network)
  const refresh = useCallback(async () => {
    if (!connectivity.isOnline) {
      throw new Error('Cannot refresh while offline');
    }

    setIsLoading(true);
    try {
      const freshData = await fetchFresh();
      if (freshData) {
        setData(freshData);
      }
    } finally {
      setIsLoading(false);
    }
  }, [connectivity.isOnline, fetchFresh]);

  // Clear offline data
  const clearOffline = useCallback(async () => {
    await deleteOffline();
    setData(null);
    setLastUpdated(null);
    setIsStale(false);
  }, [deleteOffline]);

  // Initial load
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Sync when coming back online
  useEffect(() => {
    if (connectivity.isOnline && syncOnReconnect && data && isStale) {
      fetchFresh().then(freshData => {
        if (freshData) {
          setData(freshData);
        }
      });
    }
  }, [connectivity.isOnline, syncOnReconnect, data, isStale, fetchFresh]);

  return {
    data,
    isLoading,
    error,
    isStale,
    lastUpdated,
    isOffline: connectivity.isOffline,
    refresh,
    clearOffline,
    storeOffline
  };
}

// Hook for managing multiple offline data items
export function useOfflineDataList<T>(
  storeName: string,
  options: { defaultExpiry?: number } = {}
) {
  const [items, setItems] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  const { defaultExpiry = 24 * 60 * 60 * 1000 } = options;

  const initDB = useCallback((): Promise<IDBDatabase> => {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(`bmtc-${storeName}`, 1);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
      
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains('data')) {
          const store = db.createObjectStore('data', { keyPath: 'id' });
          store.createIndex('timestamp', 'timestamp');
          store.createIndex('expiresAt', 'expiresAt');
        }
      };
    });
  }, [storeName]);

  const getAllItems = useCallback(async (): Promise<T[]> => {
    try {
      setIsLoading(true);
      const db = await initDB();
      const transaction = db.transaction(['data'], 'readonly');
      const store = transaction.objectStore('data');
      
      const allItems = await new Promise<OfflineDataItem[]>((resolve, reject) => {
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
      
      // Filter out expired items
      const now = Date.now();
      const validItems = allItems
        .filter(item => item.expiresAt > now)
        .map(item => item.data);
      
      setItems(validItems);
      return validItems;
    } catch (err) {
      setError(err as Error);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [initDB]);

  const addItem = useCallback(async (id: string, data: T): Promise<void> => {
    try {
      const db = await initDB();
      const transaction = db.transaction(['data'], 'readwrite');
      const store = transaction.objectStore('data');
      
      const item: OfflineDataItem = {
        id,
        data,
        timestamp: Date.now(),
        expiresAt: Date.now() + defaultExpiry,
        version: '1.0'
      };
      
      await new Promise<void>((resolve, reject) => {
        const request = store.put(item);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });
      
      // Update local state
      setItems(prev => {
        const existing = prev.findIndex((item: any) => item.id === id);
        if (existing >= 0) {
          const updated = [...prev];
          updated[existing] = data;
          return updated;
        }
        return [...prev, data];
      });
    } catch (err) {
      setError(err as Error);
    }
  }, [initDB, defaultExpiry]);

  const removeItem = useCallback(async (id: string): Promise<void> => {
    try {
      const db = await initDB();
      const transaction = db.transaction(['data'], 'readwrite');
      const store = transaction.objectStore('data');
      
      await new Promise<void>((resolve, reject) => {
        const request = store.delete(id);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });
      
      // Update local state
      setItems(prev => prev.filter((item: any) => item.id !== id));
    } catch (err) {
      setError(err as Error);
    }
  }, [initDB]);

  const clearAll = useCallback(async (): Promise<void> => {
    try {
      const db = await initDB();
      const transaction = db.transaction(['data'], 'readwrite');
      const store = transaction.objectStore('data');
      
      await new Promise<void>((resolve, reject) => {
        const request = store.clear();
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });
      
      setItems([]);
    } catch (err) {
      setError(err as Error);
    }
  }, [initDB]);

  useEffect(() => {
    getAllItems();
  }, [getAllItems]);

  return {
    items,
    isLoading,
    error,
    addItem,
    removeItem,
    clearAll,
    refresh: getAllItems
  };
}