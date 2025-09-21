import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import BusDetailCard, { BusData } from '../BusDetailCard';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => children,
}));

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'en' }
  })
}));

// Mock hooks
vi.mock('../../hooks/useBusRealTime', () => ({
  useBusRealTime: () => ({
    subscribeToBus: vi.fn(),
    unsubscribeFromBus: vi.fn(),
    isConnected: true,
    subscribedBuses: new Set()
  })
}));

const mockBusData: BusData = {
  id: 1,
  vehicle_number: "KA-01-HB-1234",
  capacity: 40,
  status: "active",
  current_location: {
    latitude: 12.9716,
    longitude: 77.5946,
    speed: 25,
    bearing: 45,
    recorded_at: new Date().toISOString(),
    age_minutes: 2,
    is_recent: true
  },
  current_trip: {
    id: 1,
    route_id: 1,
    route_name: "Majestic to Electronic City",
    route_number: "335E",
    start_time: new Date().toISOString(),
    driver_id: 1
  },
  occupancy: {
    level: "medium",
    percentage: 65,
    passenger_count: 26
  },
  eta: {
    seconds: 420,
    minutes: 7,
    formatted: "7m 0s",
    arrival_time: new Date(Date.now() + 420000).toISOString()
  }
};

describe('BusDetailCard', () => {
  it('renders bus information correctly', () => {
    render(<BusDetailCard bus={mockBusData} />);
    
    expect(screen.getByText('KA-01-HB-1234')).toBeInTheDocument();
    expect(screen.getByText('335E')).toBeInTheDocument();
    expect(screen.getByText('65%')).toBeInTheDocument();
    expect(screen.getByText('26 bus.passengers')).toBeInTheDocument();
  });

  it('shows ETA countdown', () => {
    render(<BusDetailCard bus={mockBusData} />);
    
    // Should show initial ETA
    expect(screen.getByText('7:00')).toBeInTheDocument();
  });

  it('calls onSubscribe when subscribe button is clicked', () => {
    const onSubscribe = vi.fn();
    render(<BusDetailCard bus={mockBusData} onSubscribe={onSubscribe} />);
    
    const subscribeButton = screen.getByText('notifications.subscribe');
    fireEvent.click(subscribeButton);
    
    expect(onSubscribe).toHaveBeenCalledWith(1);
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn();
    render(<BusDetailCard bus={mockBusData} onClose={onClose} />);
    
    const closeButton = screen.getByLabelText('common.close');
    fireEvent.click(closeButton);
    
    expect(onClose).toHaveBeenCalled();
  });

  it('shows connection status when real-time updates are enabled', () => {
    render(<BusDetailCard bus={mockBusData} enableRealTimeUpdates={true} />);
    
    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  it('hides subscribe button when showSubscribeButton is false', () => {
    render(<BusDetailCard bus={mockBusData} showSubscribeButton={false} />);
    
    expect(screen.queryByText('notifications.subscribe')).not.toBeInTheDocument();
  });

  it('renders in compact mode', () => {
    render(<BusDetailCard bus={mockBusData} compact={true} />);
    
    // Next stops should not be visible in compact mode
    expect(screen.queryByText('bus.nextStops')).not.toBeInTheDocument();
  });

  it('updates ETA countdown over time', async () => {
    vi.useFakeTimers();
    
    render(<BusDetailCard bus={mockBusData} />);
    
    // Initial ETA
    expect(screen.getByText('7:00')).toBeInTheDocument();
    
    // Advance time by 1 second
    vi.advanceTimersByTime(1000);
    
    await waitFor(() => {
      expect(screen.getByText('6:59')).toBeInTheDocument();
    });
    
    vi.useRealTimers();
  });
});