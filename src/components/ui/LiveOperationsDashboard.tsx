import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'

interface BusLocation {
  vehicle_id: number
  vehicle_number: string
  status: 'active' | 'stale' | 'offline'
  location: {
    latitude: number | null
    longitude: number | null
    speed: number
    bearing: number
    last_update: string | null
  }
  route: {
    id: number | null
    name: string
  }
  occupancy: string
  alerts: any[]
}

interface LiveMetrics {
  fleet_status: {
    total_vehicles: number
    active_vehicles: number
    maintenance_vehicles: number
    utilization_rate: number
  }
  network_status: {
    total_routes: number
    total_stops: number
    active_routes: number
    coverage_percentage: number
  }
  performance_metrics: {
    on_time_percentage: number
    average_delay_minutes: number
    trips_completed_today: number
    passenger_satisfaction: number
  }
  alerts_and_incidents: {
    active_alerts: number
    incidents_today: number
    emergency_calls: number
    maintenance_due: number
  }
  real_time_stats: {
    passengers_in_transit: number
    average_occupancy: number
    fuel_efficiency: number
    carbon_saved_today: number
  }
}

interface SystemAlert {
  id: number
  type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  description: string
  vehicle_id?: string
  route_id?: number
  timestamp: string
  status: string
}

const LiveOperationsDashboard: React.FC = () => {
  const { t } = useTranslation()
  const [liveBuses, setLiveBuses] = useState<BusLocation[]>([])
  const [metrics, setMetrics] = useState<LiveMetrics | null>(null)
  const [alerts, setAlerts] = useState<SystemAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  // Mock data for demonstration
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Simulate API calls with mock data
        const mockBuses: BusLocation[] = [
          {
            vehicle_id: 1,
            vehicle_number: 'KA01AB1234',
            status: 'active',
            location: {
              latitude: 12.9716,
              longitude: 77.5946,
              speed: 25,
              bearing: 45,
              last_update: new Date().toISOString()
            },
            route: { id: 335, name: 'Route 335E' },
            occupancy: 'high',
            alerts: []
          },
          {
            vehicle_id: 2,
            vehicle_number: 'KA01AB5678',
            status: 'active',
            location: {
              latitude: 12.9352,
              longitude: 77.6245,
              speed: 15,
              bearing: 180,
              last_update: new Date().toISOString()
            },
            route: { id: 201, name: 'Route 201A' },
            occupancy: 'medium',
            alerts: []
          },
          {
            vehicle_id: 3,
            vehicle_number: 'KA01AB9012',
            status: 'stale',
            location: {
              latitude: 12.9141,
              longitude: 77.6101,
              speed: 0,
              bearing: 90,
              last_update: new Date(Date.now() - 10 * 60 * 1000).toISOString()
            },
            route: { id: 500, name: 'Route 500D' },
            occupancy: 'low',
            alerts: []
          }
        ]

        const mockMetrics: LiveMetrics = {
          fleet_status: {
            total_vehicles: 150,
            active_vehicles: 142,
            maintenance_vehicles: 8,
            utilization_rate: 94.7
          },
          network_status: {
            total_routes: 45,
            total_stops: 1250,
            active_routes: 43,
            coverage_percentage: 92.3
          },
          performance_metrics: {
            on_time_percentage: 85.5,
            average_delay_minutes: 3.2,
            trips_completed_today: 245,
            passenger_satisfaction: 4.2
          },
          alerts_and_incidents: {
            active_alerts: 2,
            incidents_today: 3,
            emergency_calls: 0,
            maintenance_due: 5
          },
          real_time_stats: {
            passengers_in_transit: 1250,
            average_occupancy: 68.5,
            fuel_efficiency: 12.3,
            carbon_saved_today: 145.7
          }
        }

        const mockAlerts: SystemAlert[] = [
          {
            id: 1,
            type: 'delay',
            severity: 'medium',
            title: 'Route 335E experiencing delays',
            description: 'Average delay of 8 minutes due to traffic congestion',
            vehicle_id: 'KA01AB1234',
            route_id: 335,
            timestamp: new Date().toISOString(),
            status: 'active'
          },
          {
            id: 2,
            type: 'maintenance',
            severity: 'low',
            title: 'Vehicle maintenance due',
            description: '5 vehicles are due for scheduled maintenance',
            timestamp: new Date().toISOString(),
            status: 'pending'
          }
        ]

        setLiveBuses(mockBuses)
        setMetrics(mockMetrics)
        setAlerts(mockAlerts)
        setLastUpdate(new Date())
        setLoading(false)
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
        setLoading(false)
      }
    }

    fetchData()

    // Set up real-time updates
    const interval = setInterval(fetchData, 30000) // Update every 30 seconds

    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900'
      case 'stale':
        return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900'
      case 'offline':
        return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900'
      default:
        return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900'
      case 'high':
        return 'text-orange-600 bg-orange-100 dark:text-orange-400 dark:bg-orange-900'
      case 'medium':
        return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900'
      case 'low':
        return 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900'
      default:
        return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Last Update */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Live Operations Dashboard
        </h2>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Last updated: {lastUpdate.toLocaleTimeString()}
        </div>
      </div>

      {/* Key Metrics Grid */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Fleet Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Active Buses
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {metrics.fleet_status.active_vehicles}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  of {metrics.fleet_status.total_vehicles} total
                </p>
              </div>
              <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a4 4 0 118 0v4m-4 8a2 2 0 100-4 2 2 0 000 4zm0 0v4a2 2 0 002 2h6a2 2 0 002-2v-4" />
                </svg>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex items-center">
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${metrics.fleet_status.utilization_rate}%` }}
                  ></div>
                </div>
                <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
                  {metrics.fleet_status.utilization_rate}%
                </span>
              </div>
            </div>
          </motion.div>

          {/* Performance Metrics */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="card p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  On-Time Performance
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {metrics.performance_metrics.on_time_percentage}%
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Avg delay: {metrics.performance_metrics.average_delay_minutes}min
                </p>
              </div>
              <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </motion.div>

          {/* Alerts */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="card p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Active Alerts
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {metrics.alerts_and_incidents.active_alerts}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {metrics.alerts_and_incidents.incidents_today} incidents today
                </p>
              </div>
              <div className="p-3 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
                <svg className="w-6 h-6 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
            </div>
          </motion.div>

          {/* Passengers */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Passengers in Transit
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {metrics.real_time_stats.passengers_in_transit.toLocaleString()}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {metrics.real_time_stats.average_occupancy}% avg occupancy
                </p>
              </div>
              <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
                <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Live Bus Status */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="card p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Live Bus Status
          </h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            <AnimatePresence>
              {liveBuses.map((bus) => (
                <motion.div
                  key={bus.vehicle_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(bus.status)}`}>
                      {bus.status}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {bus.vehicle_number}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {bus.route.name}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {bus.location.speed} km/h
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {bus.location.last_update ? 
                        new Date(bus.location.last_update).toLocaleTimeString() : 
                        'No data'
                      }
                    </p>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* System Alerts */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="card p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            System Alerts
          </h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            <AnimatePresence>
              {alerts.map((alert) => (
                <motion.div
                  key={alert.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                          {alert.severity}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {alert.title}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                        {alert.description}
                      </p>
                      {alert.vehicle_id && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          Vehicle: {alert.vehicle_id}
                        </p>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export { LiveOperationsDashboard }