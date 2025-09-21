import React from 'react'
import MarkerClusterGroup from 'react-leaflet-cluster'
import L from 'leaflet'

interface ClusterGroupProps {
  children: React.ReactNode
  maxClusterRadius?: number
  spiderfyOnMaxZoom?: boolean
  showCoverageOnHover?: boolean
  zoomToBoundsOnClick?: boolean
}

const CustomMarkerClusterGroup: React.FC<ClusterGroupProps> = ({
  children,
  maxClusterRadius = 80,
  spiderfyOnMaxZoom = true,
  showCoverageOnHover = false,
  zoomToBoundsOnClick = true
}) => {
  // Custom cluster icon creation
  const createClusterCustomIcon = (cluster: any) => {
    const count = cluster.getChildCount()
    let size = 'small'
    let className = 'cluster-small'
    
    if (count >= 100) {
      size = 'large'
      className = 'cluster-large'
    } else if (count >= 10) {
      size = 'medium'
      className = 'cluster-medium'
    }

    return L.divIcon({
      html: `<div class="${className}"><span>${count}</span></div>`,
      className: 'custom-cluster-icon',
      iconSize: L.point(40, 40, true)
    })
  }

  return (
    <MarkerClusterGroup
      chunkedLoading
      maxClusterRadius={maxClusterRadius}
      spiderfyOnMaxZoom={spiderfyOnMaxZoom}
      showCoverageOnHover={showCoverageOnHover}
      zoomToBoundsOnClick={zoomToBoundsOnClick}
      iconCreateFunction={createClusterCustomIcon}
      spiderfyDistanceMultiplier={2}
      removeOutsideVisibleBounds={true}
      animate={true}
      animateAddingMarkers={true}
    >
      {children}
    </MarkerClusterGroup>
  )
}

export default CustomMarkerClusterGroup