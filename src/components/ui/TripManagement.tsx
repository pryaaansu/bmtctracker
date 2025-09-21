import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { Card } from './Card'
import { Button } from './Button'
import { useToast } from '../../hooks/useToast'

interface Trip {
  id: number
  vehicle_id: number
  route_id: number
  driver_id: number
  start_time?: string
  end_time?: string
  status: 'scheduled' | 'active' | 'completed' | 'cancelled'
  created_at: string
  vehicle_number?: string
  route_name?: string
  route_number?: string
}

interface TripManagementProps {
  currentTrip?: Trip
  onTripUpdate: () => void
}

export const TripManagement: React.FC<TripManagementProps> = ({
  currentTrip,
  onTripUpdate
}) => {
  const { t } = useTranslation()
  const { showToast } = useToast()
  const [loading, setLoading] = useState(false)

  const handleStartTrip = async () => {
    if (!currentTrip) return
    
    setLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      showToast('Trip started successfully', 'success')
      onTripUpdate()
    } catch (error) {
      showToast('Failed to start trip', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleEndTrip = async () => {
    if (!currentTrip) return
    
    setLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      showToast('Trip ended successfully', 'success')
      onTripUpdate()
    } catch (error) {
      showToast('Failed to end trip', 'error')
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'scheduled':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'completed':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
      case 'cancelled':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Current Trip
        </h2>
        {currentTrip && (
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(currentTrip.status)}`}>
            {currentTrip.status.charAt(0).toUpperCase() + currentTrip.status.slice(1)}
          </span>
        )}
      </div>

      {currentTrip ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          {/* Trip Details */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                  Route Information
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium">Route:</span> {currentTrip.route_name}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium">Number:</span> {currentTrip.route_number}
                </p>
              </div>
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                  Vehicle Information
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium">Vehicle:</span> {currentTrip.vehicle_number}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium">Trip ID:</span> #{currentTrip.id}
                </p>
              </div>
            </div>
          </div>

          {/* Trip Timeline */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 dark:text-white mb-3">
              Trip Timeline
            </h3>
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${
                  currentTrip.start_time ? 'bg-green-500' : 'bg-gray-300'
                }`}></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Trip Started
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {currentTrip.start_time ? formatTime(currentTrip.start_time) : 'Not started'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${
                  currentTrip.end_time ? 'bg-green-500' : 'bg-gray-300'
                }`}></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Trip Ended
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {currentTrip.end_time ? formatTime(currentTrip.end_time) : 'In progress'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            {currentTrip.status === 'scheduled' && (
              <Button
                onClick={handleStartTrip}
                disabled={loading}
                className="flex-1"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Starting...
                  </div>
                ) : (
                  'Start Trip'
                )}
              </Button>
            )}
            
            {currentTrip.status === 'active' && (
              <>
                <Button
                  onClick={handleEndTrip}
                  disabled={loading}
                  variant="outline"
                  className="flex-1"
                >
                  {loading ? (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                      Ending...
                    </div>
                  ) : (
                    'End Trip'
                  )}
                </Button>
                <Button
                  variant="secondary"
                  className="px-4"
                  onClick={() => {
                    // This would open a break/pause modal
                    showToast('Break functionality coming soon', 'info')
                  }}
                >
                  Take Break
                </Button>
              </>
            )}
          </div>

          {/* Trip Stats */}
          {currentTrip.status === 'active' && currentTrip.start_time && (
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <h3 className="font-medium text-blue-900 dark:text-blue-200 mb-2">
                Trip Progress
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-blue-700 dark:text-blue-300">Duration</p>
                  <p className="font-medium text-blue-900 dark:text-blue-100">
                    {Math.floor((Date.now() - new Date(currentTrip.start_time).getTime()) / (1000 * 60))} minutes
                  </p>
                </div>
                <div>
                  <p className="text-blue-700 dark:text-blue-300">Status</p>
                  <p className="font-medium text-blue-900 dark:text-blue-100">
                    In Progress
                  </p>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      ) : (
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-2">No active trip</p>
          <p className="text-sm text-gray-500 dark:text-gray-500">
            Your next scheduled trip will appear here
          </p>
        </div>
      )}
    </Card>
  )
}

export default TripManagement