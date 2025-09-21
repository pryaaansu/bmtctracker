import React, { useState, useEffect, useCallback, useRef } from 'react'
import { MapContainer, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import { LatLng, LatLngBounds } from 'leaflet'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'

import MapContainer as CustomMapContainer from './MapContainer'
import BusMarker from './BusMarker'
import RoutePolyline from './RoutePolyline'
import MarkerClusterGroup from './MarkerClusterGroup'
import UserLocationMarker from './UserLocationMarker'
import { BusData } from '../ui/BusDetailCard'
import BusDetailCard from '../ui/BusDetailCard'

interface Route {
  id: number
  name: string
  route_number: string
  coordinates: [number, number][]
  color?: string
  is_active: boolean
}

interface MapViewProps {
  buses?: BusData[]
  routes?: Route[]
  selectedBusId?: number | null
  selectedRouteId?: number | null
  onBusSelect?: (bus: BusData | null) => void
  onRouteSelect?: (route: Route | null) => void
  onLocationFound?: (location: LatLng) => void
  onLocationError?: (error: any) => void
  center?: [number, number]
  zoom?: number
  className?: string
  enableClustering?: boolean
  enableAnimations?: boolean
  showUserLocation?: boolean
  showRoutePolylines?: boolean
  autoFitBounds?: boolean
}

// Component to handle map events and interactions
const MapEventHandler: React.FC<{
  onBusSelect?: (bus: BusData | null) => void
  onRouteSelect?: (route: Route | null) => void
  onMapClick?: (latlng: LatLng) => void
  selectedBusId?: number | null
  selectedRouteId?: number | null
}> = ({ 
  onBusSelect, 
  onRouteSelect, 
  onMapClick, 
  selectedBusId, 
  selectedRouteId 
}) => {
  const map = useMap()

  useMapEvents({
    click: (e) => {
      // Deselect when clicking on empty map area
      if (onMapClick) {
        onMapClick(e.latlng)
      }
      
      // Clear selections if clicking on empty area
      if (e.originalEvent.target === map.getContainer()) {
        onBusSelect?.(null)
        onRouteSelect?.(null)
      }
    },
    zoomend: () => {
      console.log('Map zoom level:', map.getZoom())
    },
    moveend: () => {
      console.log('Map center:', map.getCenter())
    }
  })

  return null
}

// Component to handle bounds fitting
const BoundsHandler: React.FC<{
  buses: BusData[]
  routes: Route[]
  selectedBusId?: number | null
  selectedRouteId?: number | null
  autoFitBounds?: boolean
}> = ({ buses, routes, selectedBusId, selectedRouteId, autoFitBounds }) => {
  const map = useMap()

  useEffect(() => {
    if (!autoFitBounds) return

    const bounds = new LatLngBounds()
    let hasBounds = false

    // Add selected bus to bounds
    if (selectedBusId) {
      const selectedBus = buses.find(bus => bus.id === selectedBusId)
      if (selectedBus?.current_location) {
        bounds.extend([selectedBus.current_location.latitude, selectedBus.current_location.longitude])
        hasBounds = true
      }
    }

    // Add selected route to bounds
    if (selectedRouteId) {
      const selectedRoute = routes.find(route => route.id === selectedRouteId)
      if (selectedRoute?.coordinates.length > 0) {
        selectedRoute.coordinates.forEach(coord => {
          bounds.extend([coord[0], coord[1]])
        })
        hasBounds = true
      }
    }

    // If no specific selection, fit all buses
    if (!hasBounds && buses.length > 0) {
      buses.forEach(bus => {
        if (bus.current_location) {
          bounds.extend([bus.current_location.latitude, bus.current_location.longitude])
          hasBounds = true
        }
      })
    }

    // If still no bounds, fit all routes
    if (!hasBounds && routes.length > 0) {
      routes.forEach(route => {
        route.coordinates.forEach(coord => {
          bounds.extend([coord[0], coord[1]])
        })
        hasBounds = true
      })
    }

    if (hasBounds) {
      map.fitBounds(bounds, { padding: [20, 20] })
    }
  }, [map, buses, routes, selectedBusId, selectedRouteId, autoFitBounds])

  return null
}

const MapView: React.FC<MapViewProps> = ({
  buses = [],
  routes = [],
  selectedBusId,
  selectedRouteId,
  onBusSelect,
  onRouteSelect,
  onLocationFound,
  onLocationError,
  center = [12.9716, 77.5946], // Default to Bengaluru
  zoom = 13,
  className = '',
  enableClustering = true,
  enableAnimations = true,
  showUserLocation = true,
  showRoutePolylines = true,
  autoFitBounds = true
}) => {
  const { t } = useTranslation()
  const [userLocation, setUserLocation] = useState<LatLng | null>(null)
  const [hoveredBus, setHoveredBus] = useState<BusData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const mapRef = useRef<any>(null)

  // Handle user location
  const handleLocationFound = useCallback((location: LatLng) => {
    setUserLocation(location)
    onLocationFound?.(location)
  }, [onLocationFound])

  const handleLocationError = useCallback((error: any) => {
    console.warn('Location access denied or unavailable:', error)
    onLocationError?.(error)
  }, [onLocationError])

  // Handle bus selection
  const handleBusSelect = useCallback((bus: BusData | null) => {
    onBusSelect?.(bus)
  }, [onBusSelect])

  // Handle route selection
  const handleRouteSelect = useCallback((route: Route | null) => {
    onRouteSelect?.(route)
  }, [onRouteSelect])

  // Handle bus hover
  const handleBusHover = useCallback((bus: BusData | null) => {
    setHoveredBus(bus)
  }, [])

  // Get selected bus data
  const selectedBus = selectedBusId 
    ? buses.find(bus => bus.id === selectedBusId) 
    : null

  // Get selected route data
  const selectedRoute = selectedRouteId 
    ? routes.find(route => route.id === selectedRouteId) 
    : null

  // Filter active buses with location data
  const activeBuses = buses.filter(bus => 
    bus.current_location && 
    bus.status === 'active' &&
    bus.current_location.is_recent
  )

  // Filter active routes
  const activeRoutes = routes.filter(route => route.is_active)

  return (
    <div className={`relative w-full h-full ${className}`}>
      {/* Loading overlay */}
      <AnimatePresence>
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-gray-100 dark:bg-gray-800 flex items-center justify-center z-50"
          >
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">{t('map.loading')}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Map Container */}
      <CustomMapContainer
        center={center}
        zoom={zoom}
        className="w-full h-full"
        onLocationFound={handleLocationFound}
        onLocationError={handleLocationError}
        onMapReady={() => setIsLoading(false)}
      >
        {/* Map Event Handler */}
        <MapEventHandler
          onBusSelect={handleBusSelect}
          onRouteSelect={handleRouteSelect}
          onMapClick={() => {
            handleBusSelect(null)
            handleRouteSelect(null)
          }}
          selectedBusId={selectedBusId}
          selectedRouteId={selectedRouteId}
        />

        {/* Bounds Handler */}
        <BoundsHandler
          buses={buses}
          routes={routes}
          selectedBusId={selectedBusId}
          selectedRouteId={selectedRouteId}
          autoFitBounds={autoFitBounds}
        />

        {/* Route Polylines */}
        {showRoutePolylines && activeRoutes.map(route => (
          <RoutePolyline
            key={route.id}
            coordinates={route.coordinates}
            color={route.color || '#3B82F6'}
            animate={enableAnimations}
            highlight={selectedRouteId === route.id}
            routeId={route.id}
            onAnimationComplete={() => {
              console.log(`Route ${route.route_number} animation complete`)
            }}
          />
        ))}

        {/* Bus Markers */}
        {enableClustering ? (
          <MarkerClusterGroup
            maxClusterRadius={80}
            spiderfyOnMaxZoom={true}
            showCoverageOnHover={false}
            zoomToBoundsOnClick={true}
          >
            {activeBuses.map(bus => (
              <BusMarker
                key={bus.id}
                bus={bus}
                onBusClick={handleBusSelect}
                onBusHover={handleBusHover}
                isSelected={selectedBusId === bus.id}
                enableAnimations={enableAnimations}
              />
            ))}
          </MarkerClusterGroup>
        ) : (
          activeBuses.map(bus => (
            <BusMarker
              key={bus.id}
              bus={bus}
              onBusClick={handleBusSelect}
              onBusHover={handleBusHover}
              isSelected={selectedBusId === bus.id}
              enableAnimations={enableAnimations}
            />
          ))
        )}

        {/* User Location Marker */}
        {showUserLocation && userLocation && (
          <UserLocationMarker position={userLocation} />
        )}
      </CustomMapContainer>

      {/* Bus Detail Card */}
      <AnimatePresence>
        {selectedBus && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="absolute top-4 right-4 z-10 max-w-sm"
          >
            <BusDetailCard
              bus={selectedBus}
              onClose={() => handleBusSelect(null)}
              onBusUpdate={(updatedBus) => {
                // Update bus in parent component if needed
                console.log('Bus updated:', updatedBus)
              }}
              enableRealTimeUpdates={true}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hover Info */}
      <AnimatePresence>
        {hoveredBus && !selectedBus && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute bottom-4 left-4 z-10 bg-white dark:bg-gray-800 shadow-lg rounded-lg p-3 max-w-xs"
          >
            <div className="text-sm">
              <div className="font-semibold text-gray-900 dark:text-gray-100">
                {hoveredBus.vehicle_number}
              </div>
              {hoveredBus.current_trip && (
                <div className="text-gray-600 dark:text-gray-400">
                  {hoveredBus.current_trip.route_number} - {hoveredBus.current_trip.route_name}
                </div>
              )}
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {t('bus.occupancy')}: {hoveredBus.occupancy.percentage}%
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Map Legend */}
      <div className="absolute bottom-4 right-4 z-10 bg-white dark:bg-gray-800 shadow-lg rounded-lg p-3 text-xs">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>{t('map.legend.lowOccupancy')}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span>{t('map.legend.mediumOccupancy')}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span>{t('map.legend.highOccupancy')}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
            <span>{t('map.legend.offline')}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MapView

