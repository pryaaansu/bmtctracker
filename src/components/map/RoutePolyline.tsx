import React, { useEffect, useRef, useState } from 'react'
import { Polyline, useMap } from 'react-leaflet'
import { LatLng, LatLngBounds } from 'leaflet'
import { motion, AnimatePresence } from 'framer-motion'

interface RoutePolylineProps {
  coordinates: [number, number][]
  color?: string
  weight?: number
  opacity?: number
  dashArray?: string
  animate?: boolean
  animationDuration?: number
  onAnimationComplete?: () => void
  className?: string
  interactive?: boolean
  highlight?: boolean
  routeId?: number | string
}

const RoutePolyline: React.FC<RoutePolylineProps> = ({
  coordinates,
  color = '#3B82F6',
  weight = 4,
  opacity = 0.7,
  dashArray,
  animate = false,
  animationDuration = 2000,
  onAnimationComplete,
  className = '',
  interactive = true,
  highlight = false,
  routeId
}) => {
  const map = useMap()
  const polylineRef = useRef<any>(null)
  const [isAnimating, setIsAnimating] = useState(false)
  const [animationProgress, setAnimationProgress] = useState(0)

  // Convert coordinates to LatLng objects
  const latLngs = coordinates.map(coord => new LatLng(coord[0], coord[1]))

  // Animate polyline drawing
  useEffect(() => {
    if (!animate || !polylineRef.current) return

    setIsAnimating(true)
    setAnimationProgress(0)

    const startTime = Date.now()
    const duration = animationDuration

    const animatePolyline = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)
      
      setAnimationProgress(progress)

      if (progress < 1) {
        requestAnimationFrame(animatePolyline)
      } else {
        setIsAnimating(false)
        onAnimationComplete?.()
      }
    }

    requestAnimationFrame(animatePolyline)
  }, [animate, animationDuration, onAnimationComplete])

  // Calculate animated coordinates based on progress
  const getAnimatedCoordinates = () => {
    if (!animate || animationProgress >= 1) {
      return coordinates
    }

    const animatedLength = Math.floor(coordinates.length * animationProgress)
    return coordinates.slice(0, animatedLength + 1)
  }

  // Handle polyline click
  const handleClick = () => {
    if (!interactive) return
    
    // Fit map to polyline bounds
    if (latLngs.length > 0) {
      const bounds = new LatLngBounds(latLngs)
      map.fitBounds(bounds, { padding: [20, 20] })
    }
  }

  // Get polyline style
  const getPolylineStyle = () => {
    const baseStyle = {
      color: highlight ? '#1D4ED8' : color,
      weight: highlight ? weight + 2 : weight,
      opacity: highlight ? Math.min(opacity + 0.2, 1) : opacity,
      dashArray: dashArray
    }

    if (animate && isAnimating) {
      return {
        ...baseStyle,
        opacity: baseStyle.opacity * 0.6
      }
    }

    return baseStyle
  }

  const animatedCoordinates = getAnimatedCoordinates()

  return (
    <>
      {/* Main polyline */}
      <Polyline
        ref={polylineRef}
        positions={animatedCoordinates}
        pathOptions={getPolylineStyle()}
        eventHandlers={{
          click: handleClick
        }}
        className={className}
      />

      {/* Animation trail effect */}
      {animate && isAnimating && (
        <Polyline
          positions={animatedCoordinates}
          pathOptions={{
            color: color,
            weight: weight + 1,
            opacity: 0.3,
            dashArray: '10, 5'
          }}
          className="route-animation-trail"
        />
      )}

      {/* Highlight effect */}
      {highlight && (
        <Polyline
          positions={coordinates}
          pathOptions={{
            color: '#60A5FA',
            weight: weight + 4,
            opacity: 0.2,
            dashArray: '0'
          }}
          className="route-highlight"
        />
      )}
    </>
  )
}

export default RoutePolyline

