import React, { useEffect, useRef } from 'react'
import { Marker, Popup } from 'react-leaflet'
import { LatLng, Icon, DivIcon } from 'leaflet'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { BusData } from '../ui/BusDetailCard'

interface BusMarkerProps {
  bus: BusData
  onBusClick?: (bus: BusData) => void
  onBusHover?: (bus: BusData | null) => void
  isSelected?: boolean
  showPopup?: boolean
  enableAnimations?: boolean
}

// Create custom bus icon based on status and occupancy
const createBusIcon = (bus: BusData, isSelected: boolean = false): Icon | DivIcon => {
  const { status, occupancy, current_location } = bus
  
  // Determine colors based on status and occupancy
  let bgColor = '#6B7280' // Default gray
  let borderColor = '#374151'
  
  if (status === 'active') {
    if (occupancy.level === 'low') {
      bgColor = '#10B981' // Green
      borderColor = '#059669'
    } else if (occupancy.level === 'medium') {
      bgColor = '#F59E0B' // Yellow
      borderColor = '#D97706'
    } else {
      bgColor = '#EF4444' // Red
      borderColor = '#DC2626'
    }
  } else if (status === 'maintenance') {
    bgColor = '#F59E0B' // Orange
    borderColor = '#D97706'
  } else {
    bgColor = '#6B7280' // Gray
    borderColor = '#374151'
  }

  // Add selection highlight
  if (isSelected) {
    borderColor = '#3B82F6' // Blue
  }

  // Create speed indicator if bus is moving
  const speed = current_location?.speed || 0
  const isMoving = speed > 5 // Consider moving if speed > 5 km/h

  return new DivIcon({
    html: `
      <div class="bus-marker-container">
        <div class="bus-marker ${isSelected ? 'selected' : ''} ${isMoving ? 'moving' : ''}" 
             style="background-color: ${bgColor}; border-color: ${borderColor};">
          <div class="bus-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
              <path d="M4 16c0 .88.39 1.67 1 2.22V20c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h8v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1.78c.61-.55 1-1.34 1-2.22V6c0-3.5-3.58-4-8-4s-8 .5-8 4v10zm3.5 1c-.83 0-1.5-.67-1.5-1.5S6.67 14 7.5 14s1.5.67 1.5 1.5S8.33 17 7.5 17zm9 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm1.5-6H6V6h12v5z"/>
            </svg>
          </div>
          ${isMoving ? '<div class="speed-indicator"></div>' : ''}
        </div>
        <div class="bus-number">${bus.vehicle_number}</div>
      </div>
    `,
    className: 'custom-bus-marker',
    iconSize: [32, 40],
    iconAnchor: [16, 20],
    popupAnchor: [0, -20]
  })
}

// Create pulsing effect for moving buses
const createPulsingIcon = (bus: BusData, isSelected: boolean = false): DivIcon => {
  const baseIcon = createBusIcon(bus, isSelected)
  
  return new DivIcon({
    html: `
      <div class="bus-marker-container">
        <div class="bus-marker-pulse"></div>
        <div class="bus-marker ${isSelected ? 'selected' : ''}" 
             style="background-color: ${bus.status === 'active' ? '#10B981' : '#6B7280'};">
          <div class="bus-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
              <path d="M4 16c0 .88.39 1.67 1 2.22V20c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h8v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1.78c.61-.55 1-1.34 1-2.22V6c0-3.5-3.58-4-8-4s-8 .5-8 4v10zm3.5 1c-.83 0-1.5-.67-1.5-1.5S6.67 14 7.5 14s1.5.67 1.5 1.5S8.33 17 7.5 17zm9 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm1.5-6H6V6h12v5z"/>
            </svg>
          </div>
        </div>
        <div class="bus-number">${bus.vehicle_number}</div>
      </div>
    `,
    className: 'custom-bus-marker pulsing',
    iconSize: [32, 40],
    iconAnchor: [16, 20],
    popupAnchor: [0, -20]
  })
}

const BusMarker: React.FC<BusMarkerProps> = ({
  bus,
  onBusClick,
  onBusHover,
  isSelected = false,
  showPopup = true,
  enableAnimations = true
}) => {
  const { t } = useTranslation()
  const markerRef = useRef<any>(null)
  const [isHovered, setIsHovered] = React.useState(false)

  // Get bus position
  const position: [number, number] = bus.current_location 
    ? [bus.current_location.latitude, bus.current_location.longitude]
    : [0, 0]

  // Don't render if no location data
  if (!bus.current_location) {
    return null
  }

  // Determine if bus is moving
  const speed = bus.current_location.speed || 0
  const isMoving = speed > 5

  // Create appropriate icon
  const icon = enableAnimations && isMoving 
    ? createPulsingIcon(bus, isSelected)
    : createBusIcon(bus, isSelected)

  // Handle marker events
  const handleClick = () => {
    onBusClick?.(bus)
  }

  const handleMouseOver = () => {
    setIsHovered(true)
    onBusHover?.(bus)
  }

  const handleMouseOut = () => {
    setIsHovered(false)
    onBusHover?.(null)
  }

  // Get status text
  const getStatusText = () => {
    switch (bus.status) {
      case 'active':
        return t('bus.status.active')
      case 'maintenance':
        return t('bus.status.maintenance')
      case 'offline':
        return t('bus.status.offline')
      default:
        return t('bus.status.unknown')
    }
  }

  // Get occupancy text
  const getOccupancyText = () => {
    switch (bus.occupancy.level) {
      case 'low':
        return t('bus.occupancy.low')
      case 'medium':
        return t('bus.occupancy.medium')
      case 'high':
        return t('bus.occupancy.high')
      default:
        return t('bus.occupancy.unknown')
    }
  }

  return (
    <Marker
      ref={markerRef}
      position={position}
      icon={icon}
      eventHandlers={{
        click: handleClick,
        mouseover: handleMouseOver,
        mouseout: handleMouseOut
      }}
    >
      {showPopup && (
        <Popup
          closeButton={true}
          autoClose={false}
          closeOnClick={false}
          className="bus-popup"
        >
          <div className="bus-popup-content">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-bold text-bmtc-primary">
                {bus.vehicle_number}
              </h3>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                bus.status === 'active' 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                  : bus.status === 'maintenance'
                  ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400'
                  : 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
              }`}>
                {getStatusText()}
              </span>
            </div>

            {bus.current_trip && (
              <div className="mb-2">
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {bus.current_trip.route_number}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  {bus.current_trip.route_name}
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-600 dark:text-gray-400">{t('bus.occupancy')}:</span>
                <div className="font-medium">{getOccupancyText()}</div>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">{t('bus.capacity')}:</span>
                <div className="font-medium">{bus.occupancy.passenger_count}/{bus.capacity}</div>
              </div>
            </div>

            {bus.current_location && (
              <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                <div>{t('bus.lastUpdated')}: {Math.round(bus.current_location.age_minutes)} {t('bus.minutesAgo')}</div>
                {bus.current_location.speed > 0 && (
                  <div>{t('bus.speed')}: {Math.round(bus.current_location.speed)} km/h</div>
                )}
              </div>
            )}

            <div className="mt-3">
              <button
                onClick={handleClick}
                className="w-full px-3 py-2 bg-bmtc-primary text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                {t('map.viewDetails')}
              </button>
            </div>
          </div>
        </Popup>
      )}
    </Marker>
  )
}

export default BusMarker
