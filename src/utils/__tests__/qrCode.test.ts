import { vi } from 'vitest';
import {
  generateQRCode,
  generateTimetableData,
  storeTimetableOffline,
  getTimetableOffline,
  clearExpiredTimetables,
  type QRCodeData,
  type TimetableData,
} from '../qrCode';

// Mock canvas
const mockCanvas = {
  width: 0,
  height: 0,
  getContext: vi.fn(),
  toDataURL: vi.fn(),
};

const mockContext = {
  fillStyle: '',
  fillRect: vi.fn(),
};

Object.defineProperty(document, 'createElement', {
  value: vi.fn((tagName) => {
    if (tagName === 'canvas') {
      return mockCanvas;
    }
    return {};
  }),
});

// Mock IndexedDB
const mockDB = {
  transaction: vi.fn(),
  objectStoreNames: { contains: vi.fn() },
  createObjectStore: vi.fn(),
};

const mockTransaction = {
  objectStore: vi.fn(),
};

const mockStore = {
  put: vi.fn(),
  get: vi.fn(),
  getAll: vi.fn(),
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

Object.defineProperty(window, 'indexedDB', {
  value: {
    open: vi.fn(() => mockRequest),
  },
});

describe('QR Code Utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup canvas mocks
    mockCanvas.getContext.mockReturnValue(mockContext);
    mockCanvas.toDataURL.mockReturnValue('data:image/png;base64,mock-qr-code');
    
    // Setup IndexedDB mocks
    mockDB.transaction.mockReturnValue(mockTransaction);
    mockTransaction.objectStore.mockReturnValue(mockStore);
    mockDB.objectStoreNames.contains.mockReturnValue(false);
  });

  describe('generateQRCode', () => {
    it('should generate QR code data URL', async () => {
      const qrData: QRCodeData = {
        stopId: 'STOP001',
        stopName: 'Test Stop',
        routes: ['V-500', 'G-4'],
        location: { lat: 12.9716, lng: 77.5946 },
        timestamp: Date.now(),
        version: '1.0',
      };

      const result = await generateQRCode(qrData, 200);

      expect(mockCanvas.width).toBe(200);
      expect(mockCanvas.height).toBe(200);
      expect(mockCanvas.getContext).toHaveBeenCalledWith('2d');
      expect(mockContext.fillRect).toHaveBeenCalled();
      expect(result).toBe('data:image/png;base64,mock-qr-code');
    });

    it('should handle canvas context error', async () => {
      mockCanvas.getContext.mockReturnValue(null);

      const qrData: QRCodeData = {
        stopId: 'STOP001',
        stopName: 'Test Stop',
        routes: ['V-500'],
        location: { lat: 12.9716, lng: 77.5946 },
        timestamp: Date.now(),
        version: '1.0',
      };

      await expect(generateQRCode(qrData)).rejects.toThrow('Canvas context not available');
    });

    it('should use custom size', async () => {
      const qrData: QRCodeData = {
        stopId: 'STOP001',
        stopName: 'Test Stop',
        routes: ['V-500'],
        location: { lat: 12.9716, lng: 77.5946 },
        timestamp: Date.now(),
        version: '1.0',
      };

      await generateQRCode(qrData, 300);

      expect(mockCanvas.width).toBe(300);
      expect(mockCanvas.height).toBe(300);
    });
  });

  describe('generateTimetableData', () => {
    it('should generate mock timetable data', async () => {
      const stopId = 'STOP001';
      const result = await generateTimetableData(stopId);

      expect(result.stopId).toBe(stopId);
      expect(result.stopName).toBe(`Stop ${stopId}`);
      expect(result.stopNameKannada).toBe(`ನಿಲ್ದಾಣ ${stopId}`);
      expect(result.routes).toHaveLength(2);
      expect(result.routes[0].routeId).toBe('V-500');
      expect(result.routes[1].routeId).toBe('G-4');
      expect(result.lastUpdated).toBeGreaterThan(0);
      expect(result.validUntil).toBeGreaterThan(result.lastUpdated);
    });

    it('should generate schedule entries', async () => {
      const result = await generateTimetableData('STOP001');
      const route = result.routes[0];

      expect(route.schedule).toBeInstanceOf(Array);
      expect(route.schedule.length).toBeGreaterThan(0);
      expect(route.schedule[0]).toHaveProperty('time');
      expect(route.schedule[0]).toHaveProperty('isRealTime');
      expect(route.schedule[0].isRealTime).toBe(false);
    });
  });

  describe('storeTimetableOffline', () => {
    it('should store timetable data', async () => {
      const timetableData: TimetableData = {
        stopId: 'STOP001',
        stopName: 'Test Stop',
        routes: [],
        lastUpdated: Date.now(),
        validUntil: Date.now() + 86400000,
      };

      // Setup successful store operation
      const putRequest = { onsuccess: null as any, onerror: null as any };
      mockStore.put.mockReturnValue(putRequest);

      const storePromise = storeTimetableOffline(timetableData);

      // Simulate successful IndexedDB operations
      if (mockRequest.onsuccess) {
        mockRequest.onsuccess();
      }
      if (putRequest.onsuccess) {
        putRequest.onsuccess();
      }

      await expect(storePromise).resolves.toBeUndefined();
      expect(mockStore.put).toHaveBeenCalledWith(timetableData);
    });

    it('should handle store errors', async () => {
      const timetableData: TimetableData = {
        stopId: 'STOP001',
        stopName: 'Test Stop',
        routes: [],
        lastUpdated: Date.now(),
        validUntil: Date.now() + 86400000,
      };

      const putRequest = { onsuccess: null as any, onerror: null as any, error: new Error('Store failed') };
      mockStore.put.mockReturnValue(putRequest);

      const storePromise = storeTimetableOffline(timetableData);

      // Simulate IndexedDB error
      if (mockRequest.onsuccess) {
        mockRequest.onsuccess();
      }
      if (putRequest.onerror) {
        putRequest.onerror();
      }

      await expect(storePromise).rejects.toThrow('Store failed');
    });
  });

  describe('getTimetableOffline', () => {
    it('should retrieve valid timetable data', async () => {
      const timetableData: TimetableData = {
        stopId: 'STOP001',
        stopName: 'Test Stop',
        routes: [],
        lastUpdated: Date.now(),
        validUntil: Date.now() + 86400000, // Valid for 24 hours
      };

      const getRequest = { onsuccess: null as any, onerror: null as any, result: timetableData };
      mockStore.get.mockReturnValue(getRequest);

      const retrievePromise = getTimetableOffline('STOP001');

      // Simulate successful operations
      if (mockRequest.onsuccess) {
        mockRequest.onsuccess();
      }
      if (getRequest.onsuccess) {
        getRequest.onsuccess();
      }

      const result = await retrievePromise;
      expect(result).toEqual(timetableData);
    });

    it('should return null for expired data', async () => {
      const expiredData: TimetableData = {
        stopId: 'STOP001',
        stopName: 'Test Stop',
        routes: [],
        lastUpdated: Date.now() - 86400000,
        validUntil: Date.now() - 3600000, // Expired 1 hour ago
      };

      const getRequest = { onsuccess: null as any, onerror: null as any, result: expiredData };
      mockStore.get.mockReturnValue(getRequest);

      const retrievePromise = getTimetableOffline('STOP001');

      // Simulate successful operations
      if (mockRequest.onsuccess) {
        mockRequest.onsuccess();
      }
      if (getRequest.onsuccess) {
        getRequest.onsuccess();
      }

      const result = await retrievePromise;
      expect(result).toBeNull();
    });

    it('should return null when no data found', async () => {
      const getRequest = { onsuccess: null as any, onerror: null as any, result: null };
      mockStore.get.mockReturnValue(getRequest);

      const retrievePromise = getTimetableOffline('STOP001');

      // Simulate successful operations
      if (mockRequest.onsuccess) {
        mockRequest.onsuccess();
      }
      if (getRequest.onsuccess) {
        getRequest.onsuccess();
      }

      const result = await retrievePromise;
      expect(result).toBeNull();
    });
  });

  describe('clearExpiredTimetables', () => {
    it('should delete expired timetables', async () => {
      const validData: TimetableData = {
        stopId: 'STOP001',
        stopName: 'Valid Stop',
        routes: [],
        lastUpdated: Date.now(),
        validUntil: Date.now() + 86400000,
      };

      const expiredData: TimetableData = {
        stopId: 'STOP002',
        stopName: 'Expired Stop',
        routes: [],
        lastUpdated: Date.now() - 86400000,
        validUntil: Date.now() - 3600000,
      };

      const getAllRequest = { 
        onsuccess: null as any, 
        onerror: null as any, 
        result: [validData, expiredData] 
      };
      const deleteRequest = { onsuccess: null as any, onerror: null as any };
      
      mockStore.getAll.mockReturnValue(getAllRequest);
      mockStore.delete.mockReturnValue(deleteRequest);

      const clearPromise = clearExpiredTimetables();

      // Simulate successful operations
      if (mockRequest.onsuccess) {
        mockRequest.onsuccess();
      }
      if (getAllRequest.onsuccess) {
        getAllRequest.onsuccess();
      }
      if (deleteRequest.onsuccess) {
        deleteRequest.onsuccess();
      }

      await clearPromise;

      expect(mockStore.delete).toHaveBeenCalledWith('STOP002');
      expect(mockStore.delete).not.toHaveBeenCalledWith('STOP001');
    });
  });
});