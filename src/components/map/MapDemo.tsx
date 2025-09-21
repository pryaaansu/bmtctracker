import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { MapView } from './MapView'
import { BusData } from '../ui/BusDetailCard'

// Mock data for demonstration
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
      route_name: 'Majestic to Electronic City',
      route_number: '500A',
      start_time: new Date().toISOString(),
      driver_id: 1
    },
    occupancy: {
      level: 'medium',
      percentage: 65,
      passenger_count: 32
    }
  },
  {
    id: 2,
    vehicle_number: 'KA-01-CD-5678',
    capacity: 50,
    status: 'active',
    current_location: {
      latitude: 12.9750,
      longitude: 77.6000,
      speed: 15,
      bearing: 90,
      recorded_at: new Date().toISOString(),
      age_minutes: 1,
      is_recent: true
    },
    current_trip: {
      id: 2,
      route_id: 2,
      route_name: 'Majestic to Whitefield',
      route_number: '500B',
      start_time: new Date().toISOString(),
      driver_id: 2
    },
    occupancy: {
      level: 'high',
      percentage: 85,
      passenger_count: 42
    }
  },
  {
    id: 3,
    vehicle_number: 'KA-01-EF-9012',
    capacity: 50,
    status: 'active',
    current_location: {
      latitude: 12.9680,
      longitude: 77.5900,
      speed: 0,
      bearing: 0,
      recorded_at: new Date().toISOString(),
      age_minutes: 5,
      is_recent: true
    },
    current_trip: {
      id: 3,
      route_id: 3,
      route_name: 'Majestic to Banashankari',
      route_number: '500C',
      start_time: new Date().toISOString(),
      driver_id: 3
    },
    occupancy: {
      level: 'low',
      percentage: 30,
      passenger_count: 15
    }
  }
]

const mockRoutes = [
  {
    id: 1,
    name: 'Majestic to Electronic City',
    route_number: '500A',
    coordinates: [
      [12.9716, 77.5946],
      [12.9750, 77.6000],
      [12.9800, 77.6100],
      [12.9850, 77.6200],
      [12.9900, 77.6300]
    ],
    color: '#3B82F6',
    is_active: true
  },
  {
    id: 2,
    name: 'Majestic to Whitefield',
    route_number: '500B',
    coordinates: [
      [12.9716, 77.5946],
      [12.9750, 77.6000],
      [12.9800, 77.6100],
      [12.9850, 77.6200],
      [12.9900, 77.6300],
      [12.9950, 77.6400]
    ],
    color: '#10B981',
    is_active: true
  },
  {
    id: 3,
    name: 'Majestic to Banashankari',
    route_number: '500C',
    coordinates: [
      [12.9716, 77.5946],
      [12.9680, 77.5900],
      [12.9650, 77.5850],
      [12.9600, 77.5800],
      [12.9550, 77.5750]
    ],
    color: '#F59E0B',
    is_active: true
  }
]

interface MapDemoProps {
  className?: string
}

const MapDemo: React.FC<MapDemoProps> = ({ className = '' }) => {
  const [selectedBusId, setSelectedBusId] = useState<number | null>(null)
  const [selectedRouteId, setSelectedRouteId] = useState<number | null>(null)
  const [buses, setBuses] = useState<BusData[]>(mockBuses)
  const [routes] = useState(mockRoutes)

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setBuses(prevBuses => 
        prevBuses.map(bus => {
          if (bus.current_location && bus.status === 'active') {
            // Simulate movement
            const speed = bus.current_location.speed || 0
            if (speed > 0) {
              const latOffset = (Math.random() - 0.5) * 0.001
              const lngOffset = (Math.random() - 0.5) * 0.001
              
              return {
                ...bus,
                current_location: {
                  ...bus.current_location,
                  latitude: bus.current_location.latitude + latOffset,
                  longitude: bus.current_location.longitude + lngOffset,
                  speed: Math.max(0, speed + (Math.random() - 0.5) * 5),
                  age_minutes: Math.max(0, bus.current_location.age_minutes - 0.1)
                }
              }
            }
          }
          return bus
        })
      )
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  const handleBusSelect = (bus: BusData | null) => {
    setSelectedBusId(bus?.id || null)
    if (bus) {
      setSelectedRouteId(null)
    }
  }

  const handleRouteSelect = (route: any) => {
    setSelectedRouteId(route?.id || null)
    if (route) {
      setSelectedBusId(null)
    }
  }

  return (
    <div className={`w-full h-full ${className}`}>
      <MapView
        buses={buses}
        routes={routes}
        selectedBusId={selectedBusId}
        selectedRouteId={selectedRouteId}
        onBusSelect={handleBusSelect}
        onRouteSelect={handleRouteSelect}
        center={[12.9716, 77.5946]}
        zoom={13}
        enableClustering={true}
        enableAnimations={true}
        showUserLocation={true}
        showRoutePolylines={true}
        autoFitBounds={false}
      />
      
      {/* Demo controls */}
      <div className="absolute top-4 right-4 z-20 bg-white dark:bg-gray-800 shadow-lg rounded-lg p-4 space-y-2">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
          Demo Controls
        </h3>
        
        <div className="space-y-1">
          <button
            onClick={() => setSelectedBusId(1)}
            className="w-full text-left px-2 py-1 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
          >
            Select Bus KA-01-AB-1234
          </button>
          <button
            onClick={() => setSelectedBusId(2)}
            className="w-full text-left px-2 py-1 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
          >
            Select Bus KA-01-CD-5678
          </button>
          <button
            onClick={() => setSelectedBusId(3)}
            className="w-full text-left px-2 py-1 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
          >
            Select Bus KA-01-EF-9012
          </button>
        </div>
        
        <div className="border-t border-gray-200 dark:border-gray-700 pt-2">
          <div className="space-y-1">
            <button
              onClick={() => setSelectedRouteId(1)}
              className="w-full text-left px-2 py-1 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              Show Route 500A
            </button>
            <button
              onClick={() => setSelectedRouteId(2)}
              className="w-full text-left px-2 py-1 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              Show Route 500B
            </button>
            <button
              onClick={() => setSelectedRouteId(3)}
              className="w-full text-left px-2 py-1 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              Show Route 500C
            </button>
          </div>
        </div>
        
        <button
          onClick={() => {
            setSelectedBusId(null)
            setSelectedRouteId(null)
          }}
          className="w-full px-2 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
        >
          Clear Selection
        </button>
      </div>
    </div>
  )
}

export default MapDemo

