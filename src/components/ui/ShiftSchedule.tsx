import React from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { Card } from './Card'

interface Shift {
  id: number
  driver_id: number
  start_time: string
  end_time: string
  route_id: number
  vehicle_id: number
  status: string
  route_name?: string
  route_number?: string
  vehicle_number?: string
}

interface ShiftScheduleProps {
  shifts: Shift[]
  className?: string
}

export const ShiftSchedule: React.FC<ShiftScheduleProps> = ({
  shifts,
  className = ''
}) => {
  const { t } = useTranslation()

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    if (date.toDateString() === today.toDateString()) {
      return 'Today'
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow'
    } else {
      return date.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short'
      })
    }
  }

  const getShiftDuration = (startTime: string, endTime: string) => {
    const start = new Date(startTime)
    const end = new Date(endTime)
    const durationMs = end.getTime() - start.getTime()
    const hours = Math.floor(durationMs / (1000 * 60 * 60))
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60))
    
    if (minutes === 0) {
      return `${hours}h`
    }
    return `${hours}h ${minutes}m`
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'scheduled':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'completed':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
      case 'cancelled':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
    }
  }

  const getTimelinePosition = (startTime: string) => {
    const start = new Date(startTime)
    const hour = start.getHours()
    
    // Position based on 24-hour timeline (0-100%)
    return (hour / 24) * 100
  }

  const isUpcoming = (startTime: string) => {
    return new Date(startTime) > new Date()
  }

  const groupShiftsByDate = (shifts: Shift[]) => {
    const grouped: { [key: string]: Shift[] } = {}
    
    shifts.forEach(shift => {
      const dateKey = new Date(shift.start_time).toDateString()
      if (!grouped[dateKey]) {
        grouped[dateKey] = []
      }
      grouped[dateKey].push(shift)
    })
    
    return grouped
  }

  const groupedShifts = groupShiftsByDate(shifts)

  return (
    <Card className={`p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Shift Schedule
        </h2>
        <span className="text-sm text-gray-600 dark:text-gray-400">
          Next 7 days
        </span>
      </div>

      {shifts.length === 0 ? (
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-2">No upcoming shifts</p>
          <p className="text-sm text-gray-500 dark:text-gray-500">
            Your schedule will appear here when available
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedShifts).map(([dateKey, dayShifts]) => (
            <motion.div
              key={dateKey}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-3"
            >
              {/* Date Header */}
              <div className="flex items-center gap-3">
                <h3 className="font-medium text-gray-900 dark:text-white">
                  {formatDate(dayShifts[0].start_time)}
                </h3>
                <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {dayShifts.length} shift{dayShifts.length !== 1 ? 's' : ''}
                </span>
              </div>

              {/* Timeline Visualization */}
              <div className="relative bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-4">
                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-2">
                  <span>6 AM</span>
                  <span>12 PM</span>
                  <span>6 PM</span>
                  <span>12 AM</span>
                </div>
                <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full">
                  {dayShifts.map((shift, index) => {
                    const startHour = new Date(shift.start_time).getHours()
                    const endHour = new Date(shift.end_time).getHours()
                    const left = (startHour / 24) * 100
                    const width = ((endHour - startHour) / 24) * 100
                    
                    return (
                      <div
                        key={shift.id}
                        className={`absolute h-2 rounded-full ${
                          shift.status === 'active' ? 'bg-green-500' :
                          shift.status === 'scheduled' ? 'bg-blue-500' :
                          'bg-gray-400'
                        }`}
                        style={{
                          left: `${left}%`,
                          width: `${width}%`,
                          top: `${index * 8}px`
                        }}
                      />
                    )
                  })}
                </div>
              </div>

              {/* Shift Cards */}
              <div className="space-y-3">
                {dayShifts.map((shift) => (
                  <motion.div
                    key={shift.id}
                    whileHover={{ scale: 1.01 }}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      isUpcoming(shift.start_time)
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
                        : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h4 className="font-medium text-gray-900 dark:text-white">
                            {shift.route_name}
                          </h4>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(shift.status)}`}>
                            {shift.status}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Time</p>
                            <p className="font-medium text-gray-900 dark:text-white">
                              {formatTime(shift.start_time)} - {formatTime(shift.end_time)}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {getShiftDuration(shift.start_time, shift.end_time)}
                            </p>
                          </div>
                          
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Route</p>
                            <p className="font-medium text-gray-900 dark:text-white">
                              {shift.route_number}
                            </p>
                          </div>
                          
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Vehicle</p>
                            <p className="font-medium text-gray-900 dark:text-white">
                              {shift.vehicle_number}
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      {isUpcoming(shift.start_time) && (
                        <div className="ml-4">
                          <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Summary Stats */}
      {shifts.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {shifts.length}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Shifts</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {shifts.reduce((total, shift) => {
                  const duration = new Date(shift.end_time).getTime() - new Date(shift.start_time).getTime()
                  return total + (duration / (1000 * 60 * 60))
                }, 0).toFixed(1)}h
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Hours</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                {new Set(shifts.map(s => s.route_id)).size}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Routes</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {shifts.filter(s => isUpcoming(s.start_time)).length}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Upcoming</p>
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}

export default ShiftSchedule