import React from 'react'
import { CircleMarker, Popup } from 'react-leaflet'
import { LatLng } from 'leaflet'
import { useTranslation } from 'react-i18next'

interface UserLocationMarkerProps {
  position: LatLng
  accuracy?: number
}

const UserLocationMarker: React.FC<UserLocationMarkerProps> = ({ 
  position, 
  accuracy = 0 
}) => {
  const { t } = useTranslation()

  return (
    <>
      {/* Accuracy circle */}
      {accuracy > 0 && (
        <CircleMarker
          center={position}
          radius={Math.min(accuracy / 2, 50)} // Cap the radius for very inaccurate readings
          pathOptions={{
            color: '#3B82F6',
            fillColor: '#3B82F6',
            fillOpacity: 0.1,
            weight: 1,
            opacity: 0.3
          }}
        />
      )}
      
      {/* User location marker */}
      <CircleMarker
        center={position}
        radius={8}
        pathOptions={{
          color: '#FFFFFF',
          fillColor: '#3B82F6',
          fillOpacity: 1,
          weight: 3,
          opacity: 1
        }}
      >
        <Popup>
          <div className="text-center">
            <h3 className="font-semibold text-gray-900 mb-1">
              {t('map.yourLocation')}
            </h3>
            {accuracy > 0 && (
              <p className="text-sm text-gray-600">
                {t('map.accuracy')}: ±{Math.round(accuracy)}m
              </p>
            )}
          </div>
        </Popup>
      </CircleMarker>
    </>
  )
}

export default UserLocationMarker