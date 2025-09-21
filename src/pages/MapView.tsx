import React, { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { LatLng } from 'leaflet'
import { MapView as EnhancedMapView } from '../components/map'
import { SearchBar, FilterPanel, NearbyStops, SOSButton } from '../components/ui'
import { BusData } from '../components/ui/BusDetailCard'
import { useBusRealTime } from '../hooks/useBusRealTime'

interface Route {
  id: number
  name: string
  route_number: string
  coordinates: [number, number][]
  color?: string
  is_active: boolean
}

const MapView: React.FC = () => {
  const { t } = useTranslation()
  const [userLocation, setUserLocation] = useState<LatLng | null>(null)
  const [locationError, setLocationError] = useState<string | null>(null)
  const [_selectedResult, setSelectedResult] = useState<any>(null)
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [filters, setFilters] = useState<any>({
    routes: [],
    serviceTypes: [],
    maxDistance: 5,
    showActiveOnly: true
  })
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  
  // Map state
  const [buses, setBuses] = useState<BusData[]>([])
  const [routes, setRoutes] = useState<Route[]>([])
  const [selectedBusId, setSelectedBusId] = useState<number | null>(null)
  const [selectedRouteId, setSelectedRouteId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Real-time bus updates
  const { isConnected, subscribeToBus, unsubscribeFromBus } = useBusRealTime({
    onLocationUpdate: (update) => {
      setBuses(prevBuses => 
        prevBuses.map(bus => 
          bus.id === update.vehicle_id 
            ? {
                ...bus,
                current_location: {
                  ...update.location,
                  is_recent: true
                },
                occupancy: update.occupancy || bus.occupancy
              }
            : bus
        )
      )
    }
  })

  // Fetch buses data
  const fetchBuses = useCallback(async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/v1/buses?active_only=true&with_location=true&limit=100', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setBuses(data.buses || [])
        
        // Subscribe to all active buses for real-time updates
        data.buses?.forEach((bus: BusData) => {
          if (bus.current_location?.is_recent) {
            subscribeToBus(bus.id)
          }
        })
      } else {
        console.error('Failed to fetch buses:', response.statusText)
      }
    } catch (error) {
      console.error('Error fetching buses:', error)
    } finally {
      setIsLoading(false)
    }
  }, [subscribeToBus])

  // Fetch routes data
  const fetchRoutes = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/routes?active_only=true&limit=50', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        const routesWithCoordinates = (data.routes || []).map((route: any) => ({
          ...route,
          coordinates: route.geojson ? JSON.parse(route.geojson).coordinates.map((coord: [number, number]) => [coord[1], coord[0]]) : []
        }))
        setRoutes(routesWithCoordinates)
      } else {
        console.error('Failed to fetch routes:', response.statusText)
      }
    } catch (error) {
      console.error('Error fetching routes:', error)
    }
  }, [])

  // Load data on component mount
  useEffect(() => {
    fetchBuses()
    fetchRoutes()
  }, [fetchBuses, fetchRoutes])

  // Handle bus selection
  const handleBusSelect = useCallback((bus: BusData | null) => {
    setSelectedBusId(bus?.id || null)
    if (bus) {
      setSelectedRouteId(null) // Clear route selection when bus is selected
    }
  }, [])

  // Handle route selection
  const handleRouteSelect = useCallback((route: Route | null) => {
    setSelectedRouteId(route?.id || null)
    if (route) {
      setSelectedBusId(null) // Clear bus selection when route is selected
    }
  }, [])

  // Handle location found
  const handleLocationFound = useCallback((location: LatLng) => {
    setUserLocation(location)
    setLocationError(null)
  }, [])

  // Handle location error
  const handleLocationError = useCallback((error: any) => {
    setLocationError(error.message || 'Unable to get your location')
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="h-screen pt-16"
    >
      <div className="h-full flex">
        {/* Sidebar */}
        <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex space-x-2">
              <div className="flex-1">
                <SearchBar
                  placeholder={t('map.searchPlaceholder')}
                  userLocation={userLocation ? { lat: userLocation.lat, lng: userLocation.lng } : null}
                  onSelect={(suggestion) => {
                    setSelectedResult(suggestion)
                    console.log('Selected:', suggestion)
                    // TODO: Handle selection (zoom to location, show details, etc.)
                  }}
                  onSearch={(query) => {
                    console.log('Search:', query)
                    // TODO: Handle manual search
                  }}
                />
              </div>
              <button
                onClick={() => setIsFilterOpen(true)}
                className="px-3 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                title={t('common.filter')}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.707A1 1 0 013 7V4z" />
                </svg>
              </button>
            </div>
          </div>
          
          <div className="flex-1 p-4">
            <NearbyStops
              userLocation={userLocation ? { lat: userLocation.lat, lng: userLocation.lng } : null}
              maxDistance={filters.maxDistance}
              onStopSelect={(stop) => {
                console.log('Stop selected:', stop)
                // TODO: Handle stop selection (zoom to stop, show details, etc.)
              }}
              refreshTrigger={refreshTrigger}
            />
          </div>
        </div>

        {/* Enhanced Map Container */}
        <div className="flex-1 relative">
          <EnhancedMapView
            buses={buses}
            routes={routes}
            selectedBusId={selectedBusId}
            selectedRouteId={selectedRouteId}
            onBusSelect={handleBusSelect}
            onRouteSelect={handleRouteSelect}
            onLocationFound={handleLocationFound}
            onLocationError={handleLocationError}
            center={userLocation ? [userLocation.lat, userLocation.lng] : [12.9716, 77.5946]}
            zoom={13}
            className="h-full"
            enableClustering={true}
            enableAnimations={true}
            showUserLocation={true}
            showRoutePolylines={true}
            autoFitBounds={true}
          />
          
          {/* Status indicators */}
          <div className="absolute top-4 left-4 z-10 space-y-2">
            {/* Connection status */}
            <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-3 flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {isConnected ? t('map.live') : t('map.offline')}
              </span>
            </div>

            {/* Bus count */}
            <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-3">
              <div className="text-sm text-gray-700 dark:text-gray-300">
                {t('map.activeBuses')}: {buses.filter(bus => bus.current_location?.is_recent).length}
              </div>
            </div>
          </div>

          {/* Location error notification */}
          {locationError && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="absolute top-4 right-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3 z-10 max-w-sm"
            >
              <div className="flex items-center">
                <svg className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  {t('map.locationError')}: {locationError}
                </p>
              </div>
            </motion.div>
          )}

          {/* Loading overlay */}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-gray-100 dark:bg-gray-800 flex items-center justify-center z-50"
            >
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
                <p className="text-gray-600 dark:text-gray-400">{t('map.loadingBuses')}</p>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* Filter Panel */}
      <FilterPanel
        isOpen={isFilterOpen}
        onClose={() => setIsFilterOpen(false)}
        onFiltersChange={(newFilters) => {
          setFilters(newFilters)
          setRefreshTrigger(prev => prev + 1) // Trigger refresh of nearby stops
          console.log('Filters changed:', newFilters)
          // TODO: Apply filters to map data
        }}
        userLocation={userLocation ? { lat: userLocation.lat, lng: userLocation.lng } : null}
      />

      {/* SOS Button */}
      <SOSButton />
    </motion.div>
  )
}

export default MapView