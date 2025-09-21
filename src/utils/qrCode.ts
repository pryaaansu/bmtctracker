// QR Code generation utilities for offline timetables

export interface QRCodeData {
  stopId: string;
  stopName: string;
  routes: string[];
  location: {
    lat: number;
    lng: number;
  };
  timestamp: number;
  version: string;
}

export interface TimetableData {
  stopId: string;
  stopName: string;
  stopNameKannada?: string;
  routes: RouteSchedule[];
  lastUpdated: number;
  validUntil: number;
}

export interface RouteSchedule {
  routeId: string;
  routeName: string;
  direction: string;
  schedule: ScheduleEntry[];
  frequency: number; // minutes
  operatingHours: {
    start: string;
    end: string;
  };
}

export interface ScheduleEntry {
  time: string;
  estimatedArrival?: string;
  isRealTime: boolean;
  confidence?: number;
}

// Generate QR code data URL using canvas
export function generateQRCode(data: QRCodeData, size: number = 200): Promise<string> {
  return new Promise((resolve, reject) => {
    try {
      // Create a simple QR code pattern using canvas
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        reject(new Error('Canvas context not available'));
        return;
      }

      canvas.width = size;
      canvas.height = size;
      
      // Fill background
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, size, size);
      
      // Create a simple pattern (in real implementation, use a proper QR library)
      const dataString = JSON.stringify(data);
      const hash = simpleHash(dataString);
      
      // Generate pattern based on hash
      ctx.fillStyle = '#000000';
      const cellSize = size / 25;
      
      for (let i = 0; i < 25; i++) {
        for (let j = 0; j < 25; j++) {
          const index = i * 25 + j;
          if ((hash >> (index % 32)) & 1) {
            ctx.fillRect(i * cellSize, j * cellSize, cellSize, cellSize);
          }
        }
      }
      
      // Add corner markers
      drawCornerMarker(ctx, 0, 0, cellSize);
      drawCornerMarker(ctx, size - 7 * cellSize, 0, cellSize);
      drawCornerMarker(ctx, 0, size - 7 * cellSize, cellSize);
      
      resolve(canvas.toDataURL('image/png'));
    } catch (error) {
      reject(error);
    }
  });
}

// Simple hash function for demo purposes
function simpleHash(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}

// Draw QR code corner marker
function drawCornerMarker(ctx: CanvasRenderingContext2D, x: number, y: number, cellSize: number) {
  // Outer square
  ctx.fillRect(x, y, 7 * cellSize, 7 * cellSize);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(x + cellSize, y + cellSize, 5 * cellSize, 5 * cellSize);
  ctx.fillStyle = '#000000';
  ctx.fillRect(x + 2 * cellSize, y + 2 * cellSize, 3 * cellSize, 3 * cellSize);
}

// Generate timetable data for a stop
export async function generateTimetableData(stopId: string): Promise<TimetableData> {
  try {
    // In a real implementation, this would fetch from the API
    // For now, we'll generate mock data
    const mockData: TimetableData = {
      stopId,
      stopName: `Stop ${stopId}`,
      stopNameKannada: `ನಿಲ್ದಾಣ ${stopId}`,
      routes: [
        {
          routeId: 'V-500',
          routeName: 'Kempegowda Bus Station - Electronic City',
          direction: 'Electronic City',
          frequency: 15,
          operatingHours: {
            start: '05:30',
            end: '23:00'
          },
          schedule: generateScheduleEntries('05:30', '23:00', 15)
        },
        {
          routeId: 'G-4',
          routeName: 'Shivajinagar - Banashankari',
          direction: 'Banashankari',
          frequency: 20,
          operatingHours: {
            start: '06:00',
            end: '22:30'
          },
          schedule: generateScheduleEntries('06:00', '22:30', 20)
        }
      ],
      lastUpdated: Date.now(),
      validUntil: Date.now() + (24 * 60 * 60 * 1000) // Valid for 24 hours
    };

    return mockData;
  } catch (error) {
    console.error('Failed to generate timetable data:', error);
    throw error;
  }
}

// Generate schedule entries based on frequency
function generateScheduleEntries(startTime: string, endTime: string, frequency: number): ScheduleEntry[] {
  const entries: ScheduleEntry[] = [];
  const start = parseTime(startTime);
  const end = parseTime(endTime);
  
  let current = start;
  while (current <= end) {
    entries.push({
      time: formatTime(current),
      isRealTime: false
    });
    current += frequency;
  }
  
  return entries;
}

// Parse time string to minutes
function parseTime(timeStr: string): number {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours * 60 + minutes;
}

// Format minutes to time string
function formatTime(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
}

// Store timetable data offline
export async function storeTimetableOffline(data: TimetableData): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('bmtc-timetables', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['timetables'], 'readwrite');
      const store = transaction.objectStore('timetables');
      
      const putRequest = store.put(data);
      putRequest.onsuccess = () => resolve();
      putRequest.onerror = () => reject(putRequest.error);
    };
    
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('timetables')) {
        const store = db.createObjectStore('timetables', { keyPath: 'stopId' });
        store.createIndex('lastUpdated', 'lastUpdated');
      }
    };
  });
}

// Retrieve timetable data from offline storage
export async function getTimetableOffline(stopId: string): Promise<TimetableData | null> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('bmtc-timetables', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['timetables'], 'readonly');
      const store = transaction.objectStore('timetables');
      
      const getRequest = store.get(stopId);
      getRequest.onsuccess = () => {
        const result = getRequest.result;
        
        // Check if data is still valid
        if (result && result.validUntil > Date.now()) {
          resolve(result);
        } else {
          resolve(null);
        }
      };
      getRequest.onerror = () => reject(getRequest.error);
    };
  });
}

// Get all stored timetables
export async function getAllTimetablesOffline(): Promise<TimetableData[]> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('bmtc-timetables', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['timetables'], 'readonly');
      const store = transaction.objectStore('timetables');
      
      const getAllRequest = store.getAll();
      getAllRequest.onsuccess = () => {
        const results = getAllRequest.result.filter(
          (timetable: TimetableData) => timetable.validUntil > Date.now()
        );
        resolve(results);
      };
      getAllRequest.onerror = () => reject(getAllRequest.error);
    };
  });
}

// Clear expired timetables
export async function clearExpiredTimetables(): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('bmtc-timetables', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['timetables'], 'readwrite');
      const store = transaction.objectStore('timetables');
      
      const getAllRequest = store.getAll();
      getAllRequest.onsuccess = () => {
        const now = Date.now();
        const deletePromises = getAllRequest.result
          .filter((timetable: TimetableData) => timetable.validUntil <= now)
          .map((timetable: TimetableData) => {
            return new Promise<void>((resolveDelete, rejectDelete) => {
              const deleteRequest = store.delete(timetable.stopId);
              deleteRequest.onsuccess = () => resolveDelete();
              deleteRequest.onerror = () => rejectDelete(deleteRequest.error);
            });
          });
        
        Promise.all(deletePromises)
          .then(() => resolve())
          .catch(reject);
      };
      getAllRequest.onerror = () => reject(getAllRequest.error);
    };
  });
}

// Download timetable as PDF (mock implementation)
export async function downloadTimetablePDF(data: TimetableData): Promise<void> {
  // In a real implementation, this would generate a proper PDF
  // For now, we'll create a simple text representation
  const content = generateTimetableText(data);
  
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = `timetable-${data.stopId}-${new Date().toISOString().split('T')[0]}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
}

// Generate text representation of timetable
function generateTimetableText(data: TimetableData): string {
  let content = `BMTC Bus Timetable\n`;
  content += `Stop: ${data.stopName}\n`;
  if (data.stopNameKannada) {
    content += `ನಿಲ್ದಾಣ: ${data.stopNameKannada}\n`;
  }
  content += `Last Updated: ${new Date(data.lastUpdated).toLocaleString()}\n`;
  content += `Valid Until: ${new Date(data.validUntil).toLocaleString()}\n\n`;
  
  data.routes.forEach(route => {
    content += `Route: ${route.routeName} (${route.routeId})\n`;
    content += `Direction: ${route.direction}\n`;
    content += `Frequency: Every ${route.frequency} minutes\n`;
    content += `Operating Hours: ${route.operatingHours.start} - ${route.operatingHours.end}\n`;
    content += `Schedule:\n`;
    
    route.schedule.forEach(entry => {
      content += `  ${entry.time}`;
      if (entry.estimatedArrival) {
        content += ` (Est: ${entry.estimatedArrival})`;
      }
      content += `\n`;
    });
    content += `\n`;
  });
  
  return content;
}