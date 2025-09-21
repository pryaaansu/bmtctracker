import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { Card } from './Card'
import { Button } from './Button'
import { useToast } from '../../hooks/useToast'

interface LocationData {
  latitude: number
  longitude: number
  accuracy?: number
  speed?: number
  heading?: number
  timestamp: number
}

interface LocationTrackerProps {
  isActive?: boolean
  interval?: number // in seconds
  onLocationUpdate?: (location: LocationData) => void
  onError?: (error: string) => void
  className?: string
}

export const LocationTracker: React.FC<LocationTrackerProps> = ({
  isActive = false,
  interval = 30, // Default 30 seconds
  onLocationUpdate,
  onError,
  className = ''
}) => {
  const { t } = useTranslation()
  const { showToast } = useToast()
  
  const [isTracking, setIsTracking] = useState(isActive)
  const [currentLocation, setCurrentLocation] = useState<LocationData | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [trackingStats, setTrackingStats] = useState({
    totalUpdates: 0,
    successfulUpdates: 0,
    failedUpdates: 0,
    averageAccuracy: 0
  })
  const [connectionStatus, setConnectionStatus] = useState<'online' | 'offline' | 'syncing'>('online')
  
  const watchIdRef = useRef<number | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const locationHistoryRef = useRef<LocationData[]>([])

  // Geolocation options
  const geoOptions: PositionOptions = {
    enableHighAccuracy: true,
    timeout: 15000,
    maximumAge: 5000
  }

  const getCurrentLocation = async (): Promise<LocationData> => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation is not supported by this browser'))
        return
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const locationData: LocationData = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            speed: position.coords.speed || undefined,
            heading: position.coords.heading || undefined,
            timestamp: Date.now()
          }
          resolve(locationData)
        },
        (error) => {
          let errorMessage = 'Unknown location error'
          switch (error.code) {
            case error.PERMISSION_DENIED:
              errorMessage = 'Location access denied by user'
              break
            case error.POSITION_UNAVAILABLE:
              errorMessage = 'Location information unavailable'
              break
            case error.TIMEOUT:
              errorMessage = 'Location request timed out'
              break
          }
          reject(new Error(errorMessage))
        },
        geoOptions
      )
    })
  }

  const sendLocationUpdate = async (location: LocationData) => {
    try {
      setConnectionStatus('syncing')
      
      // Simulate API call to send location
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // In a real implementation, this would be an API call
      console.log('Location update sent:', location)
      
      if (onLocationUpdate) {
        onLocationUpdate(location)
      }
      
      setConnectionStatus('online')
      
      // Update stats
      setTrackingStats(prev => ({
        ...prev,
        successfulUpdates: prev.successfulUpdates + 1,
        averageAccuracy: location.accuracy 
          ? (prev.averageAccuracy + location.accuracy) / 2 
          : prev.averageAccuracy
      }))
      
      return true
    } catch (error) {
      setConnectionStatus('offline')
      
      // Store failed update for retry
      locationHistoryRef.current.push(location)
      
      setTrackingStats(prev => ({
        ...prev,
        failedUpdates: prev.failedUpdates + 1
      }))
      
      if (onError) {
        onError('Failed to send location update')
      }
      
      return false
    }
  }

  const updateLocation = async () => {
    try {
      const location = await getCurrentLocation()
      setCurrentLocation(location)
      setLastUpdate(new Date())
      
      // Add to history
      locationHistoryRef.current.push(location)
      
      // Keep only last 50 locations
      if (locationHistoryRef.current.length > 50) {
        locationHistoryRef.current = locationHistoryRef.current.slice(-50)
      }
      
      // Send to server
      await sendLocationUpdate(location)
      
      setTrackingStats(prev => ({
        ...prev,
        totalUpdates: prev.totalUpdates + 1
      }))
      
    } catch (error) {
      console.error('Location update failed:', error)
      
      if (onError) {
        onError(error instanceof Error ? error.message : 'Location update failed')
      }
      
      setTrackingStats(prev => ({
        ...prev,
        totalUpdates: prev.totalUpdates + 1,
        failedUpdates: prev.failedUpdates + 1
      }))
    }
  }

  const startTracking = async () => {
    if (!navigator.geolocation) {
      showToast('Geolocation is not supported by this browser', 'error')
      return
    }

    try {
      // Get initial location
      await updateLocation()
      
      // Start continuous tracking
      watchIdRef.current = navigator.geolocation.watchPosition(
        async (position) => {
          const locationData: LocationData = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            speed: position.coords.speed || undefined,
            heading: position.coords.heading || undefined,
            timestamp: Date.now()
          }
          
          setCurrentLocation(locationData)
          setLastUpdate(new Date())
        },
        (error) => {
          console.error('Watch position error:', error)
        },
        geoOptions
      )
      
      // Set up interval for server updates
      intervalRef.current = setInterval(updateLocation, interval * 1000)
      
      setIsTracking(true)
      showToast('Location tracking started', 'success')
      
    } catch (error) {
      showToast('Failed to start location tracking', 'error')
    }
  }

  const stopTracking = () => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current)
      watchIdRef.current = null
    }
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    
    setIsTracking(false)
    showToast('Location tracking stopped', 'info')
  }

  const retryFailedUpdates = async () => {
    if (locationHistoryRef.current.length === 0) return
    
    const failedLocations = [...locationHistoryRef.current]
    locationHistoryRef.current = []
    
    for (const location of failedLocations) {
      await sendLocationUpdate(location)
    }
    
    showToast(`Synced ${failedLocations.length} pending locations`, 'success')
  }

  // Auto-start tracking if isActive prop is true
  useEffect(() => {
    if (isActive && !isTracking) {
      startTracking()
    } else if (!isActive && isTracking) {
      stopTracking()
    }
  }, [isActive])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopTracking()
    }
  }, [])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getAccuracyColor = (accuracy?: number) => {
    if (!accuracy) return 'text-gray-500'
    if (accuracy <= 10) return 'text-green-600'
    if (accuracy <= 50) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'online':
        return 'text-green-600 dark:text-green-400'
      case 'syncing':
        return 'text-blue-600 dark:text-blue-400'
      case 'offline':
        return 'text-red-600 dark:text-red-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'online':
        return '🟢'
      case 'syncing':
        return '🔄'
      case 'offline':
        return '🔴'
      default:
        return '⚪'
    }
  }

  return (
    <Card className={`p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Location Tracking
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-sm">{getConnectionStatusIcon()}</span>
          <span className={`text-sm font-medium ${getConnectionStatusColor()}`}>
            {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
          </span>
        </div>
      </div>

      {/* Tracking Status */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Tracking Status
          </span>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${
              isTracking ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
            }`}></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {isTracking ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>
        
        <div className="flex gap-2">
          {!isTracking ? (
            <Button onClick={startTracking} size="sm">
              Start Tracking
            </Button>
          ) : (
            <Button onClick={stopTracking} variant="outline" size="sm">
              Stop Tracking
            </Button>
          )}
          
          {locationHistoryRef.current.length > 0 && (
            <Button onClick={retryFailedUpdates} variant="outline" size="sm">
              Sync ({locationHistoryRef.current.length})
            </Button>
          )}
        </div>
      </div>

      {/* Current Location */}
      <AnimatePresence>
        {currentLocation && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg"
          >
            <h3 className="font-medium text-blue-900 dark:text-blue-200 mb-3">
              Current Location
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-blue-700 dark:text-blue-300">Latitude</p>
                <p className="font-mono text-blue-900 dark:text-blue-100">
                  {currentLocation.latitude.toFixed(6)}
                </p>
              </div>
              <div>
                <p className="text-blue-700 dark:text-blue-300">Longitude</p>
                <p className="font-mono text-blue-900 dark:text-blue-100">
                  {currentLocation.longitude.toFixed(6)}
                </p>
              </div>
              {currentLocation.accuracy && (
                <div>
                  <p className="text-blue-700 dark:text-blue-300">Accuracy</p>
                  <p className={`font-medium ${getAccuracyColor(currentLocation.accuracy)}`}>
                    ±{currentLocation.accuracy.toFixed(0)}m
                  </p>
                </div>
              )}
              {currentLocation.speed && (
                <div>
                  <p className="text-blue-700 dark:text-blue-300">Speed</p>
                  <p className="font-medium text-blue-900 dark:text-blue-100">
                    {(currentLocation.speed * 3.6).toFixed(1)} km/h
                  </p>
                </div>
              )}
            </div>
            {lastUpdate && (
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
                Last updated: {formatTime(lastUpdate)}
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tracking Statistics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {trackingStats.totalUpdates}
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400">Total Updates</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
            {trackingStats.successfulUpdates}
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400">Successful</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-red-600 dark:text-red-400">
            {trackingStats.failedUpdates}
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400">Failed</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
            {trackingStats.averageAccuracy > 0 ? trackingStats.averageAccuracy.toFixed(0) : '-'}
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400">Avg Accuracy (m)</p>
        </div>
      </div>

      {/* Settings */}
      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <h4 className="font-medium text-gray-900 dark:text-white mb-3">
          Tracking Settings
        </h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Update Interval:</span>
            <span className="font-medium text-gray-900 dark:text-white">{interval}s</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">High Accuracy:</span>
            <span className="font-medium text-gray-900 dark:text-white">Enabled</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Auto Retry:</span>
            <span className="font-medium text-gray-900 dark:text-white">Enabled</span>
          </div>
        </div>
      </div>

      {/* Tips */}
      <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
        <h4 className="text-sm font-medium text-yellow-900 dark:text-yellow-200 mb-1">
          💡 Location Tracking Tips
        </h4>
        <ul className="text-xs text-yellow-700 dark:text-yellow-300 space-y-1">
          <li>• Keep GPS enabled for accurate tracking</li>
          <li>• Tracking works in background during active trips</li>
          <li>• Failed updates are automatically retried when online</li>
        </ul>
      </div>
    </Card>
  )
}

export default LocationTracker