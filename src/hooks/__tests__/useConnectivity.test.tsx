import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import { useConnectivity, useSlowConnection } from '../useConnectivity';

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true,
});

// Mock connection API
const mockConnection = {
  effectiveType: '4g',
  downlink: 10,
  rtt: 50,
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
};

Object.defineProperty(navigator, 'connection', {
  writable: true,
  value: mockConnection,
});

describe('useConnectivity', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    navigator.onLine = true;
    mockConnection.effectiveType = '4g';
    mockConnection.downlink = 10;
    mockConnection.rtt = 50;
  });

  it('should return online status when connected', () => {
    const { result } = renderHook(() => useConnectivity());

    expect(result.current.isOnline).toBe(true);
    expect(result.current.isOffline).toBe(false);
    expect(result.current.effectiveType).toBe('4g');
    expect(result.current.downlink).toBe(10);
    expect(result.current.rtt).toBe(50);
  });

  it('should return offline status when disconnected', () => {
    navigator.onLine = false;

    const { result } = renderHook(() => useConnectivity());

    expect(result.current.isOnline).toBe(false);
    expect(result.current.isOffline).toBe(true);
  });

  it('should update when connection changes', () => {
    const { result } = renderHook(() => useConnectivity());

    expect(result.current.isOnline).toBe(true);

    // Simulate going offline
    act(() => {
      navigator.onLine = false;
      window.dispatchEvent(new Event('offline'));
    });

    expect(result.current.isOnline).toBe(false);
    expect(result.current.isOffline).toBe(true);

    // Simulate coming back online
    act(() => {
      navigator.onLine = true;
      window.dispatchEvent(new Event('online'));
    });

    expect(result.current.isOnline).toBe(true);
    expect(result.current.isOffline).toBe(false);
  });

  it('should handle connection quality changes', () => {
    const { result } = renderHook(() => useConnectivity());

    expect(result.current.effectiveType).toBe('4g');

    // Simulate connection quality change
    act(() => {
      mockConnection.effectiveType = '2g';
      mockConnection.downlink = 0.5;
      mockConnection.rtt = 200;
      
      // Trigger connection change event
      const changeHandler = mockConnection.addEventListener.mock.calls
        .find(call => call[0] === 'change')?.[1];
      if (changeHandler) {
        changeHandler();
      }
    });

    expect(result.current.effectiveType).toBe('2g');
    expect(result.current.downlink).toBe(0.5);
    expect(result.current.rtt).toBe(200);
  });
});

describe('useSlowConnection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    navigator.onLine = true;
    mockConnection.effectiveType = '4g';
    mockConnection.downlink = 10;
  });

  it('should detect fast connection', () => {
    mockConnection.effectiveType = '4g';
    mockConnection.downlink = 10;

    const { result } = renderHook(() => useSlowConnection());

    expect(result.current.isSlowConnection).toBe(false);
  });

  it('should detect slow connection by effective type', () => {
    mockConnection.effectiveType = '2g';
    mockConnection.downlink = 10; // High downlink but slow effective type

    const { result } = renderHook(() => useSlowConnection());

    expect(result.current.isSlowConnection).toBe(true);
  });

  it('should detect slow connection by downlink speed', () => {
    mockConnection.effectiveType = '4g';
    mockConnection.downlink = 1; // Below default threshold of 1.5

    const { result } = renderHook(() => useSlowConnection());

    expect(result.current.isSlowConnection).toBe(true);
  });

  it('should use custom threshold', () => {
    mockConnection.effectiveType = '4g';
    mockConnection.downlink = 2; // Above 1.5 but below 3

    const { result } = renderHook(() => useSlowConnection(3));

    expect(result.current.isSlowConnection).toBe(true);
  });

  it('should handle missing connection API', () => {
    // @ts-ignore
    delete navigator.connection;

    const { result } = renderHook(() => useSlowConnection());

    expect(result.current.isSlowConnection).toBe(false);
    expect(result.current.effectiveType).toBe(null);
    expect(result.current.downlink).toBe(null);
  });
});