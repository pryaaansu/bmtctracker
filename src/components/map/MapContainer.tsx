import React, { useEffect, useRef, useState } from 'react'
import { MapContainer as LeafletMapContainer, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import { Map as LeafletMap, LatLng } from 'leaflet'
import { motion } from 'framer-motion'
import 'leaflet/dist/leaflet.css'

// Fix for default markers in Leaflet with Webpack
import L from 'leaflet'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
})

interface MapContainerProps {
  center?: [number, number]
  zoom?: number
  className?: string
  onLocationFound?: (location: LatLng) => void
  onLocationError?: (error: any) => void
  children?: React.ReactNode
}

// Component to handle geolocation
const LocationHandler: React.FC<{
  onLocationFound?: (location: LatLng) => void
  onLocationError?: (error: any) => void
}> = ({ onLocationFound, onLocationError }) => {
  const map = useMap()

  useEffect(() => {
    if (!onLocationFound && !onLocationError) return

    const handleLocationFound = (e: any) => {
      onLocationFound?.(e.latlng)
    }

    const handleLocationError = (e: any) => {
      onLocationError?.(e)
    }

    map.on('locationfound', handleLocationFound)
    map.on('locationerror', handleLocationError)

    return () => {
      map.off('locationfound', handleLocationFound)
      map.off('locationerror', handleLocationError)
    }
  }, [map, onLocationFound, onLocationError])

  return null
}

// Component to handle responsive map sizing
const ResponsiveMapHandler: React.FC = () => {
  const map = useMap()

  useEffect(() => {
    const handleResize = () => {
      setTimeout(() => {
        map.invalidateSize()
      }, 100)
    }

    window.addEventListener('resize', handleResize)
    
    // Initial size invalidation
    setTimeout(() => {
      map.invalidateSize()
    }, 100)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [map])

  return null
}

// Component to handle map events
const MapEventHandler: React.FC<{
  onMapReady?: (map: LeafletMap) => void
}> = ({ onMapReady }) => {
  const map = useMap()

  useEffect(() => {
    onMapReady?.(map)
  }, [map, onMapReady])

  useMapEvents({
    click: (e) => {
      console.log('Map clicked at:', e.latlng)
    },
    zoomend: () => {
      console.log('Zoom level:', map.getZoom())
    },
    moveend: () => {
      console.log('Map center:', map.getCenter())
    }
  })

  return null
}

const MapContainer: React.FC<MapContainerProps> = ({
  center = [12.9716, 77.5946], // Default to Bengaluru coordinates
  zoom = 13,
  className = '',
  onLocationFound,
  onLocationError,
  children
}) => {
  const [isLoading, setIsLoading] = useState(true)
  const [userLocation, setUserLocation] = useState<LatLng | null>(null)
  const mapRef = useRef<LeafletMap | null>(null)

  const handleMapReady = (map: LeafletMap) => {
    mapRef.current = map
    setIsLoading(false)
    
    // Request user location
    if (navigator.geolocation) {
      map.locate({ setView: false, maxZoom: 16 })
    }
  }

  const handleLocationFound = (location: LatLng) => {
    setUserLocation(location)
    onLocationFound?.(location)
  }

  const handleLocationError = (error: any) => {
    console.warn('Location access denied or unavailable:', error)
    onLocationError?.(error)
  }

  return (
    <div className={`relative ${className}`}>
      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-gray-100 dark:bg-gray-800 flex items-center justify-center z-50"
        >
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading map...</p>
          </div>
        </motion.div>
      )}
      
      <LeafletMapContainer
        center={center}
        zoom={zoom}
        className={`w-full h-full ${className}`}
        zoomControl={false}
        attributionControl={true}
        scrollWheelZoom={true}
        doubleClickZoom={true}
        dragging={true}
        touchZoom={true}
        boxZoom={true}
        keyboard={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
          minZoom={3}
        />
        
        <LocationHandler
          onLocationFound={handleLocationFound}
          onLocationError={handleLocationError}
        />
        
        <ResponsiveMapHandler />
        
        <MapEventHandler onMapReady={handleMapReady} />
        
        {children}
      </LeafletMapContainer>

      {/* Custom zoom controls */}
      <div className="absolute top-4 right-4 z-10 flex flex-col space-y-2">
        <button
          onClick={() => mapRef.current?.zoomIn()}
          className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          aria-label="Zoom in"
        >
          <svg className="w-5 h-5 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        </button>
        <button
          onClick={() => mapRef.current?.zoomOut()}
          className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          aria-label="Zoom out"
        >
          <svg className="w-5 h-5 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 12H6" />
          </svg>
        </button>
      </div>

      {/* User location button */}
      {userLocation && (
        <button
          onClick={() => {
            if (mapRef.current && userLocation) {
              mapRef.current.setView(userLocation, 16)
            }
          }}
          className="absolute bottom-4 right-4 z-10 bg-white dark:bg-gray-800 shadow-lg rounded-lg p-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          aria-label="Go to my location"
        >
          <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      )}
    </div>
  )
}

export default MapContainer