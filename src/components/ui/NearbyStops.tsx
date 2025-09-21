import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'

interface Stop {
  id: number
  name: string
  name_kannada?: string
  latitude: number
  longitude: number
  distance_km: number
  route?: {
    id: number
    name: string
    route_number: string
    is_active: boolean
  }
}

interface NearbyStopsProps {
  userLocation: { lat: number; lng: number } | null
  maxDistance?: number
  limit?: number
  onStopSelect?: (stop: Stop) => void
  className?: string
  refreshTrigger?: number
}

const NearbyStops: React.FC<NearbyStopsProps> = ({
  userLocation,
  maxDistance = 2,
  limit = 10,
  onStopSelect,
  className = '',
  refreshTrigger = 0
}) => {
  const { t } = useTranslation()
  const [stops, setStops] = useState<Stop[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load nearby stops when user location changes
  useEffect(() => {
    if (userLocation) {
      loadNearbyStops()
    } else {
      setStops([])
    }
  }, [userLocation, maxDistance, limit, refreshTrigger])

  const loadNearbyStops = async () => {
    if (!userLocation) return

    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        lat: userLocation.lat.toString(),
        lng: userLocation.lng.toString(),
        radius: maxDistance.toString(),
        limit: limit.toString(),
        skip: '0'
      })

      const response = await fetch(`/api/v1/stops?${params}`)
      if (!response.ok) throw new Error('Failed to load nearby stops')

      const data = await response.json()
      
      // The API returns stops with distances when lat/lng are provided
      const stopsWithDistance = data.stops.map((stop: any, index: number) => ({
        ...stop,
        distance_km: data.distances ? data.distances[index] : 0
      }))

      setStops(stopsWithDistance)
    } catch (error) {
      console.error('Failed to load nearby stops:', error)
      setError('Failed to load nearby stops')
    } finally {
      setLoading(false)
    }
  }

  // Format distance for display
  const formatDistance = (distanceKm: number) => {
    if (distanceKm < 1) {
      return `${Math.round(distanceKm * 1000)}m`
    }
    return `${distanceKm.toFixed(1)}km`
  }

  // Get bus count for a stop (mock data for now)
  const getBusCount = (_stopId: number) => {
    // This would normally come from real-time bus data
    return Math.floor(Math.random() * 5) + 1
  }

  // Get next bus ETA (mock data for now)
  const getNextBusETA = (_stopId: number) => {
    // This would normally come from real-time ETA calculations
    const minutes = Math.floor(Math.random() * 15) + 1
    return `${minutes} min`
  }

  if (!userLocation) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p className="text-gray-500 dark:text-gray-400">
          Enable location to see nearby stops
        </p>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <svg className="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <p className="text-red-600 dark:text-red-400 mb-2">{error}</p>
        <button
          onClick={loadNearbyStops}
          className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200"
        >
          Try again
        </button>
      </div>
    )
  }

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t('map.nearbyStops')}
        </h3>
        <button
          onClick={loadNearbyStops}
          disabled={loading}
          className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
        >
          <motion.svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            animate={loading ? { rotate: 360 } : {}}
            transition={loading ? { duration: 1, repeat: Infinity, ease: "linear" } : {}}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </motion.svg>
        </button>
      </div>

      {loading && stops.length === 0 ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card p-3 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                </div>
                <div className="text-right">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 mb-1"></div>
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-12"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <AnimatePresence mode="popLayout">
          <div className="space-y-3">
            {stops.map((stop, index) => (
              <motion.div
                key={stop.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.1 }}
                className="card p-3 cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => onStopSelect?.(stop)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900 dark:text-white truncate">
                        {stop.name}
                      </h4>
                      {stop.name_kannada && (
                        <span className="text-sm text-gray-500 dark:text-gray-400 truncate">
                          ({stop.name_kannada})
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2 mt-1">
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {formatDistance(stop.distance_km)} away
                      </p>
                      {stop.route && (
                        <>
                          <span className="text-gray-300 dark:text-gray-600">•</span>
                          <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                            {stop.route.route_number}
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-right flex-shrink-0 ml-3">
                    <p className="text-sm font-medium text-primary-600 dark:text-primary-400">
                      {getBusCount(stop.id)} buses
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Next: {getNextBusETA(stop.id)}
                    </p>
                  </div>
                </div>
                
                {/* Route indicator */}
                {stop.route && (
                  <div className="mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {stop.route.name}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        stop.route.is_active 
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                      }`}>
                        {stop.route.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
            
            {stops.length === 0 && !loading && (
              <div className="text-center py-8">
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <p className="text-gray-500 dark:text-gray-400">
                  No stops found within {maxDistance}km
                </p>
              </div>
            )}
          </div>
        </AnimatePresence>
      )}
    </div>
  )
}

export default NearbyStops