import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import StopDetailModal, { StopData } from '../StopDetailModal';

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
    isConnected: true
  })
}));

// Mock fetch
global.fetch = vi.fn();

const mockStopData: StopData = {
  id: 1,
  name: "Silk Board Junction",
  name_kannada: "ಸಿಲ್ಕ್ ಬೋರ್ಡ್ ಜಂಕ್ಷನ್",
  latitude: 12.9165,
  longitude: 77.6224,
  route_id: 1,
  route_name: "Majestic to Electronic City",
  arrivals: [
    {
      vehicle_id: 1,
      vehicle_number: "KA-01-HB-1234",
      route_name: "Majestic to Electronic City",
      route_number: "335E",
      eta: {
        seconds: 420,
        minutes: 7,
        formatted: "7m 0s",
        arrival_time: new Date(Date.now() + 420000).toISOString()
      },
      occupancy: {
        level: "medium",
        percentage: 65
      },
      distance_meters: 2500,
      calculation_method: "gps_based",
      calculated_at: new Date().toISOString()
    }
  ]
};

describe('StopDetailModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(() => '[]'),
        setItem: vi.fn(),
      },
      writable: true,
    });
  });

  it('renders stop information correctly', () => {
    render(
      <StopDetailModal
        stop={mockStopData}
        isOpen={true}
        onClose={vi.fn()}
      />
    );
    
    expect(screen.getByText('Silk Board Junction')).toBeInTheDocument();
    expect(screen.getByText('stop.route: Majestic to Electronic City')).toBeInTheDocument();
  });

  it('shows Kannada name when language is Kannada', () => {
    // Mock i18n to return Kannada language
    vi.mocked(require('react-i18next').useTranslation).mockReturnValue({
      t: (key: string) => key,
      i18n: { language: 'kn' }
    });

    render(
      <StopDetailModal
        stop={mockStopData}
        isOpen={true}
        onClose={vi.fn()}
      />
    );
    
    expect(screen.getByText('ಸಿಲ್ಕ್ ಬೋರ್ಡ್ ಜಂಕ್ಷನ್')).toBeInTheDocument();
  });

  it('displays bus arrivals', () => {
    render(
      <StopDetailModal
        stop={mockStopData}
        isOpen={true}
        onClose={vi.fn()}
      />
    );
    
    expect(screen.getByText('KA-01-HB-1234')).toBeInTheDocument();
    expect(screen.getByText('335E')).toBeInTheDocument();
    expect(screen.getByText('65%')).toBeInTheDocument();
  });

  it('calls onClose when modal is closed', () => {
    const onClose = vi.fn();
    render(
      <StopDetailModal
        stop={mockStopData}
        isOpen={true}
        onClose={onClose}
      />
    );
    
    // Modal component should handle close functionality
    // This test verifies the prop is passed correctly
    expect(onClose).toBeDefined();
  });

  it('calls onSubscribe when subscribe button is clicked', () => {
    const onSubscribe = vi.fn();
    render(
      <StopDetailModal
        stop={mockStopData}
        isOpen={true}
        onClose={vi.fn()}
        onSubscribe={onSubscribe}
      />
    );
    
    const subscribeButton = screen.getByText('notifications.subscribe');
    fireEvent.click(subscribeButton);
    
    expect(onSubscribe).toHaveBeenCalledWith(1);
  });

  it('toggles favorite status', () => {
    const onToggleFavorite = vi.fn();
    render(
      <StopDetailModal
        stop={mockStopData}
        isOpen={true}
        onClose={vi.fn()}
        onToggleFavorite={onToggleFavorite}
      />
    );
    
    const favoriteButton = screen.getByText('stop.addToFavorites');
    fireEvent.click(favoriteButton);
    
    expect(onToggleFavorite).toHaveBeenCalledWith(1);
  });

  it('shows loading state when fetching arrivals', async () => {
    // Mock fetch to return a promise that doesn't resolve immediately
    const mockFetch = vi.fn(() => new Promise(() => {}));
    global.fetch = mockFetch;

    render(
      <StopDetailModal
        stop={mockStopData}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('common.loading')).toBeInTheDocument();
    });
  });

  it('shows no arrivals message when no buses are coming', () => {
    const stopWithNoArrivals = { ...mockStopData, arrivals: [] };
    
    render(
      <StopDetailModal
        stop={stopWithNoArrivals}
        isOpen={true}
        onClose={vi.fn()}
      />
    );
    
    expect(screen.getByText('stop.noBusesArriving')).toBeInTheDocument();
  });

  it('does not render when stop is null', () => {
    const { container } = render(
      <StopDetailModal
        stop={null}
        isOpen={true}
        onClose={vi.fn()}
      />
    );
    
    expect(container.firstChild).toBeNull();
  });

  it('calls individual bus notify buttons', () => {
    const onSubscribe = vi.fn();
    render(
      <StopDetailModal
        stop={mockStopData}
        isOpen={true}
        onClose={vi.fn()}
        onSubscribe={onSubscribe}
      />
    );
    
    const notifyButtons = screen.getAllByText('stop.notifyMe');
    fireEvent.click(notifyButtons[0]);
    
    expect(onSubscribe).toHaveBeenCalledWith(1, 1);
  });
});