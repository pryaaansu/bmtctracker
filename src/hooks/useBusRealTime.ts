import { useState, useEffect, useCallback } from 'react';
import { useWebSocket, WebSocketMessage } from './useWebSocket';
import { BusData } from '../components/ui/BusDetailCard';

export interface BusLocationUpdate {
  vehicle_id: number;
  vehicle_number: string;
  location: {
    latitude: number;
    longitude: number;
    speed: number;
    bearing: number;
    recorded_at: string;
    age_minutes: number;
  };
  occupancy?: {
    level: 'low' | 'medium' | 'high';
    percentage: number;
    passenger_count: number;
  };
  eta_updates?: Array<{
    stop_id: number;
    eta_seconds: number;
    eta_minutes: number;
  }>;
}

export interface UseBusRealTimeOptions {
  busId?: number;
  onLocationUpdate?: (update: BusLocationUpdate) => void;
  onETAUpdate?: (busId: number, stopId: number, eta: any) => void;
  autoConnect?: boolean;
}

export interface UseBusRealTimeReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  subscribeToBus: (busId: number) => void;
  unsubscribeFromBus: (busId: number) => void;
  subscribedBuses: Set<number>;
  lastUpdate: BusLocationUpdate | null;
}

export const useBusRealTime = (options: UseBusRealTimeOptions = {}): UseBusRealTimeReturn => {
  const { busId, onLocationUpdate, onETAUpdate, autoConnect = true } = options;
  
  const [subscribedBuses, setSubscribedBuses] = useState<Set<number>>(new Set());
  const [lastUpdate, setLastUpdate] = useState<BusLocationUpdate | null>(null);

  // Determine WebSocket URL based on environment
  const getWebSocketUrl = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws/realtime`;
  };

  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'location_update') {
      const update = message.data as BusLocationUpdate;
      setLastUpdate(update);
      
      // Only process updates for subscribed buses
      if (subscribedBuses.has(update.vehicle_id)) {
        onLocationUpdate?.(update);
        
        // Handle ETA updates if present
        if (update.eta_updates) {
          update.eta_updates.forEach(eta => {
            onETAUpdate?.(update.vehicle_id, eta.stop_id, eta);
          });
        }
      }
    }
  }, [subscribedBuses, onLocationUpdate, onETAUpdate]);

  const handleConnect = useCallback(() => {
    console.log('Connected to bus real-time updates');
    
    // Re-subscribe to buses after reconnection
    subscribedBuses.forEach(busId => {
      sendMessage({
        type: 'subscribe_vehicle',
        vehicle_id: busId
      });
    });
  }, [subscribedBuses]);

  const handleDisconnect = useCallback(() => {
    console.log('Disconnected from bus real-time updates');
  }, []);

  const handleError = useCallback((error: Event) => {
    console.error('WebSocket error:', error);
  }, []);

  const { isConnected, isConnecting, error, sendMessage } = useWebSocket({
    url: getWebSocketUrl(),
    onMessage: handleMessage,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
    onError: handleError,
    autoConnect,
    reconnectAttempts: 5,
    reconnectInterval: 3000
  });

  const subscribeToBus = useCallback((busId: number) => {
    setSubscribedBuses(prev => {
      const newSet = new Set(prev);
      newSet.add(busId);
      return newSet;
    });

    if (isConnected) {
      sendMessage({
        type: 'subscribe_vehicle',
        vehicle_id: busId
      });
    }
  }, [isConnected, sendMessage]);

  const unsubscribeFromBus = useCallback((busId: number) => {
    setSubscribedBuses(prev => {
      const newSet = new Set(prev);
      newSet.delete(busId);
      return newSet;
    });

    if (isConnected) {
      sendMessage({
        type: 'unsubscribe_vehicle',
        vehicle_id: busId
      });
    }
  }, [isConnected, sendMessage]);

  // Auto-subscribe to initial bus if provided
  useEffect(() => {
    if (busId && isConnected) {
      subscribeToBus(busId);
    }
  }, [busId, isConnected, subscribeToBus]);

  return {
    isConnected,
    isConnecting,
    error,
    subscribeToBus,
    unsubscribeFromBus,
    subscribedBuses,
    lastUpdate
  };
};

export default useBusRealTime;