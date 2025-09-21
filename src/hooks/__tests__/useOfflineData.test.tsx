import { renderHook, act, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { useOfflineData } from '../useOfflineData';

// Mock IndexedDB
const mockDB = {
  transaction: vi.fn(),
  objectStoreNames: { contains: vi.fn() },
  createObjectStore: vi.fn(),
  result: null as any,
};

const mockTransaction = {
  objectStore: vi.fn(),
};

const mockStore = {
  put: vi.fn(),
  get: vi.fn(),
  delete: vi.fn(),
  createIndex: vi.fn(),
};

const mockRequest = {
  onsuccess: null as any,
  onerror: null as any,
  onupgradeneeded: null as any,
  result: mockDB,
  error: null,
};

// Mock indexedDB
Object.defineProperty(window, 'indexedDB', {
  value: {
    open: vi.fn(() => mockRequest),
  },
});

// Mock connectivity
vi.mock('../useConnectivity', () => ({
  useConnectivity: () => ({
    isOnline: true,
    isOffline: false,
  }),
}));

describe('useOfflineData', () => {
  const mockFetcher = vi.fn();
  const testKey = 'test-key';
  const testData = { id: 1, name: 'Test Data' };
  
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mock behavior
    mockDB.transaction.mockReturnValue(mockTransaction);
    mockTransaction.objectStore.mockReturnValue(mockStore);
    mockDB.objectStoreNames.contains.mockReturnValue(false);
    
    // Setup successful requests
    mockStore.put.mockImplementation(() => ({
      onsuccess: null,
      onerror: null,
    }));
    
    mockStore.get.mockImplementation(() => ({
      onsuccess: null,
      onerror: null,
      result: null,
    }));
    
    mockFetcher.mockResolvedValue(testData);
  });

  it('should initialize with loading state', () => {
    const { result } = renderHook(() =>
      useOfflineData(testKey, mockFetcher, { storeName: 'test' })
    );

    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBe(null);
    expect(result.current.error).toBe(null);
  });

  it('should fetch data when online and no cached data', async () => {
    const { result } = renderHook(() =>
      useOfflineData(testKey, mockFetcher, { storeName: 'test' })
    );

    // Simulate IndexedDB operations
    act(() => {
      if (mockRequest.onsuccess) {
        mockRequest.onsuccess();
      }
    });

    // Simulate get request returning no data
    act(() => {
      const getRequest = mockStore.get();
      getRequest.result = null;
      if (getRequest.onsuccess) {
        getRequest.onsuccess();
      }
    });

    await waitFor(() => {
      expect(mockFetcher).toHaveBeenCalled();
    });

    // Simulate successful fetch and store
    act(() => {
      const putRequest = mockStore.put();
      if (putRequest.onsuccess) {
        putRequest.onsuccess();
      }
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toEqual(testData);
    });
  });

  it('should use cached data when available', async () => {
    const cachedItem = {
      id: testKey,
      data: testData,
      timestamp: Date.now(),
      expiresAt: Date.now() + 1000000,
      version: '1.0',
    };

    const { result } = renderHook(() =>
      useOfflineData(testKey, mockFetcher, { storeName: 'test' })
    );

    // Simulate IndexedDB operations
    act(() => {
      if (mockRequest.onsuccess) {
        mockRequest.onsuccess();
      }
    });

    // Simulate get request returning cached data
    act(() => {
      const getRequest = mockStore.get();
      getRequest.result = cachedItem;
      if (getRequest.onsuccess) {
        getRequest.onsuccess();
      }
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toEqual(testData);
      expect(mockFetcher).not.toHaveBeenCalled();
    });
  });

  it('should handle expired cached data', async () => {
    const expiredItem = {
      id: testKey,
      data: testData,
      timestamp: Date.now() - 2000000,
      expiresAt: Date.now() - 1000000, // Expired
      version: '1.0',
    };

    const { result } = renderHook(() =>
      useOfflineData(testKey, mockFetcher, { storeName: 'test' })
    );

    // Simulate IndexedDB operations
    act(() => {
      if (mockRequest.onsuccess) {
        mockRequest.onsuccess();
      }
    });

    // Simulate get request returning expired data
    act(() => {
      const getRequest = mockStore.get();
      getRequest.result = expiredItem;
      if (getRequest.onsuccess) {
        getRequest.onsuccess();
      }
    });

    // Should delete expired data and fetch fresh
    await waitFor(() => {
      expect(mockStore.delete).toHaveBeenCalledWith(testKey);
      expect(mockFetcher).toHaveBeenCalled();
    });
  });

  it('should handle fetch errors', async () => {
    const fetchError = new Error('Fetch failed');
    mockFetcher.mockRejectedValue(fetchError);

    const { result } = renderHook(() =>
      useOfflineData(testKey, mockFetcher, { storeName: 'test' })
    );

    // Simulate IndexedDB operations
    act(() => {
      if (mockRequest.onsuccess) {
        mockRequest.onsuccess();
      }
    });

    // Simulate get request returning no data
    act(() => {
      const getRequest = mockStore.get();
      getRequest.result = null;
      if (getRequest.onsuccess) {
        getRequest.onsuccess();
      }
    });

    await waitFor(() => {
      expect(result.current.error).toEqual(fetchError);
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('should refresh data when requested', async () => {
    const { result } = renderHook(() =>
      useOfflineData(testKey, mockFetcher, { storeName: 'test' })
    );

    // Initial setup
    act(() => {
      if (mockRequest.onsuccess) {
        mockRequest.onsuccess();
      }
    });

    act(() => {
      const getRequest = mockStore.get();
      getRequest.result = null;
      if (getRequest.onsuccess) {
        getRequest.onsuccess();
      }
    });

    await waitFor(() => {
      expect(result.current.data).toEqual(testData);
    });

    // Clear mock calls
    mockFetcher.mockClear();

    // Refresh
    await act(async () => {
      await result.current.refresh();
    });

    expect(mockFetcher).toHaveBeenCalledTimes(1);
  });

  it('should clear offline data', async () => {
    const { result } = renderHook(() =>
      useOfflineData(testKey, mockFetcher, { storeName: 'test' })
    );

    await act(async () => {
      await result.current.clearOffline();
    });

    expect(result.current.data).toBe(null);
  });

  it('should handle IndexedDB errors gracefully', async () => {
    const dbError = new Error('IndexedDB error');
    mockRequest.error = dbError;

    const { result } = renderHook(() =>
      useOfflineData(testKey, mockFetcher, { storeName: 'test' })
    );

    // Simulate IndexedDB error
    act(() => {
      if (mockRequest.onerror) {
        mockRequest.onerror();
      }
    });

    // Should still try to fetch from network
    await waitFor(() => {
      expect(mockFetcher).toHaveBeenCalled();
    });
  });
});