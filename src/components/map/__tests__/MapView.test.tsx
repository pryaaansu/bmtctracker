import React from 'react'
import { render, screen } from '@testing-library/react'
import { MapView } from '../MapView'
import { BusData } from '../../ui/BusDetailCard'

// Mock Leaflet components
jest.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => <div data-testid="map-container">{children}</div>,
  TileLayer: () => <div data-testid="tile-layer" />,
  useMap: () => ({
    fitBounds: jest.fn(),
    setView: jest.fn(),
    getZoom: () => 13,
    getCenter: () => ({ lat: 12.9716, lng: 77.5946 })
  }),
  useMapEvents: () => null
}))

// Mock the custom map container
jest.mock('../MapContainer', () => ({
  __esModule: true,
  default: ({ children }: any) => <div data-testid="custom-map-container">{children}</div>
}))

// Mock bus marker
jest.mock('../BusMarker', () => ({
  __esModule: true,
  default: ({ bus }: { bus: BusData }) => <div data-testid={`bus-marker-${bus.id}`}>{bus.vehicle_number}</div>
}))

// Mock route polyline
jest.mock('../RoutePolyline', () => ({
  __esModule: true,
  default: ({ routeId }: { routeId: number }) => <div data-testid={`route-polyline-${routeId}`} />
}))

// Mock marker cluster group
jest.mock('../MarkerClusterGroup', () => ({
  __esModule: true,
  default: ({ children }: any) => <div data-testid="marker-cluster-group">{children}</div>
}))

// Mock user location marker
jest.mock('../UserLocationMarker', () => ({
  __esModule: true,
  default: () => <div data-testid="user-location-marker" />
}))

// Mock bus detail card
jest.mock('../../ui/BusDetailCard', () => ({
  __esModule: true,
  default: ({ bus }: { bus: BusData }) => <div data-testid={`bus-detail-card-${bus.id}`}>{bus.vehicle_number}</div>
}))

const mockBuses: BusData[] = [
  {
    id: 1,
    vehicle_number: 'KA-01-AB-1234',
    capacity: 50,
    status: 'active',
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
      route_name: 'Test Route',
      route_number: '500A',
      start_time: new Date().toISOString(),
      driver_id: 1
    },
    occupancy: {
      level: 'medium',
      percentage: 65,
      passenger_count: 32
    }
  }
]

const mockRoutes = [
  {
    id: 1,
    name: 'Test Route',
    route_number: '500A',
    coordinates: [[12.9716, 77.5946], [12.9750, 77.6000]],
    color: '#3B82F6',
    is_active: true
  }
]

describe('MapView', () => {
  it('renders map container', () => {
    render(
      <MapView
        buses={mockBuses}
        routes={mockRoutes}
        center={[12.9716, 77.5946]}
        zoom={13}
      />
    )
    
    expect(screen.getByTestId('custom-map-container')).toBeInTheDocument()
  })

  it('renders bus markers when buses are provided', () => {
    render(
      <MapView
        buses={mockBuses}
        routes={mockRoutes}
        center={[12.9716, 77.5946]}
        zoom={13}
      />
    )
    
    expect(screen.getByTestId('bus-marker-1')).toBeInTheDocument()
    expect(screen.getByText('KA-01-AB-1234')).toBeInTheDocument()
  })

  it('renders route polylines when routes are provided', () => {
    render(
      <MapView
        buses={mockBuses}
        routes={mockRoutes}
        center={[12.9716, 77.5946]}
        zoom={13}
      />
    )
    
    expect(screen.getByTestId('route-polyline-1')).toBeInTheDocument()
  })

  it('shows bus detail card when bus is selected', () => {
    render(
      <MapView
        buses={mockBuses}
        routes={mockRoutes}
        selectedBusId={1}
        center={[12.9716, 77.5946]}
        zoom={13}
      />
    )
    
    expect(screen.getByTestId('bus-detail-card-1')).toBeInTheDocument()
  })

  it('enables clustering when enableClustering is true', () => {
    render(
      <MapView
        buses={mockBuses}
        routes={mockRoutes}
        enableClustering={true}
        center={[12.9716, 77.5946]}
        zoom={13}
      />
    )
    
    expect(screen.getByTestId('marker-cluster-group')).toBeInTheDocument()
  })

  it('shows user location marker when showUserLocation is true', () => {
    render(
      <MapView
        buses={mockBuses}
        routes={mockRoutes}
        showUserLocation={true}
        center={[12.9716, 77.5946]}
        zoom={13}
      />
    )
    
    expect(screen.getByTestId('user-location-marker')).toBeInTheDocument()
  })
})

