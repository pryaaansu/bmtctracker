import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import Card, { CardHeader, CardContent } from '../components/ui/Card'
import Button from '../components/ui/Button'
import { fadeUpVariants, scaleVariants } from '../design-system/animations'

interface PerformanceMetrics {
  total_trips: number
  on_time_percentage: number
  average_delay_minutes: number
  reliability_score: number
  total_passengers: int
  average_occupancy: number
  total_co2_saved_kg: number
}

interface RidershipData {
  total_passengers: number
  average_daily_passengers: number
  peak_hour_occupancy: number
  growth_trend: number
  daily_patterns: Record<string, number>
  hourly_occupancy: Record<string, number>
}

interface CarbonFootprint {
  total_co2_saved_kg: number
  total_distance_km: number
  total_passengers: number
  equivalent_cars_off_road: number
  co2_saved_per_passenger_kg: number
  co2_saved_per_km_kg: number
}

interface DashboardSummary {
  performance: PerformanceMetrics
  ridership: RidershipData
  environmental: CarbonFootprint
  trends: {
    delay_trend_percentage: number
    recent_trips_count: number
    data_period_days: number
  }
  last_updated: string
}

const AnalyticsDashboard: React.FC = () => {
  const { t } = useTranslation()
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedPeriod, setSelectedPeriod] = useState<'7d' | '30d' | '90d'>('30d')
  const [selectedRoute, setSelectedRoute] = useState<number | null>(null)

  useEffect(() => {
    fetchDashboardData()
  }, [selectedPeriod, selectedRoute])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const token = localStorage.getItem('token')
      const response = await fetch('/api/v1/analytics/dashboard-summary', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data')
      }

      const data = await response.json()
      setDashboardData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const getPeriodDays = () => {
    switch (selectedPeriod) {
      case '7d': return 7
      case '30d': return 30
      case '90d': return 90
      default: return 30
    }
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toFixed(0)
  }

  const getTrendColor = (trend: number) => {
    if (trend > 0) return 'text-green-600 dark:text-green-400'
    if (trend < 0) return 'text-red-600 dark:text-red-400'
    return 'text-gray-600 dark:text-gray-400'
  }

  const getTrendIcon = (trend: number) => {
    if (trend > 0) return '↗'
    if (trend < 0) return '↘'
    return '→'
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-64 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
              ))}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-64 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-12"
          >
            <div className="text-red-500 text-6xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              {t('analytics.error.title')}
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">{error}</p>
            <Button onClick={fetchDashboardData} variant="primary">
              {t('common.retry')}
            </Button>
          </motion.div>
        </div>
      </div>
    )
  }

  if (!dashboardData) {
    return null
  }

  const { performance, ridership, environmental, trends } = dashboardData

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6"
    >
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          variants={fadeUpVariants}
          initial="hidden"
          animate="visible"
          className="mb-8"
        >
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {t('analytics.title')}
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                {t('analytics.subtitle')}
              </p>
            </div>
            
            <div className="mt-4 sm:mt-0 flex space-x-4">
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value as '7d' | '30d' | '90d')}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value="7d">{t('analytics.period.7d')}</option>
                <option value="30d">{t('analytics.period.30d')}</option>
                <option value="90d">{t('analytics.period.90d')}</option>
              </select>
              
              <Button
                onClick={fetchDashboardData}
                variant="outline"
                size="sm"
              >
                {t('common.refresh')}
              </Button>
            </div>
          </div>
        </motion.div>

        {/* Key Metrics Cards */}
        <motion.div
          variants={fadeUpVariants}
          initial="hidden"
          animate="visible"
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-sm font-medium">{t('analytics.metrics.totalTrips')}</p>
                  <p className="text-3xl font-bold">{formatNumber(performance.total_trips)}</p>
                </div>
                <div className="text-blue-200 text-3xl">🚌</div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100 text-sm font-medium">{t('analytics.metrics.onTimePercentage')}</p>
                  <p className="text-3xl font-bold">{performance.on_time_percentage.toFixed(1)}%</p>
                </div>
                <div className="text-green-200 text-3xl">⏰</div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm font-medium">{t('analytics.metrics.totalPassengers')}</p>
                  <p className="text-3xl font-bold">{formatNumber(performance.total_passengers)}</p>
                </div>
                <div className="text-purple-200 text-3xl">👥</div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-orange-100 text-sm font-medium">{t('analytics.metrics.co2Saved')}</p>
                  <p className="text-3xl font-bold">{formatNumber(environmental.total_co2_saved_kg)} kg</p>
                </div>
                <div className="text-orange-200 text-3xl">🌱</div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Performance Metrics */}
        <motion.div
          variants={fadeUpVariants}
          initial="hidden"
          animate="visible"
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8"
        >
          <Card>
            <CardHeader title={t('analytics.performance.title')} />
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">{t('analytics.performance.reliabilityScore')}</span>
                  <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {performance.reliability_score.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">{t('analytics.performance.averageDelay')}</span>
                  <span className="text-2xl font-bold text-red-600 dark:text-red-400">
                    {performance.average_delay_minutes.toFixed(1)} min
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">{t('analytics.performance.averageOccupancy')}</span>
                  <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {performance.average_occupancy.toFixed(1)}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader title={t('analytics.ridership.title')} />
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">{t('analytics.ridership.dailyAverage')}</span>
                  <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {formatNumber(ridership.average_daily_passengers)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">{t('analytics.ridership.peakOccupancy')}</span>
                  <span className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                    {ridership.peak_hour_occupancy.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">{t('analytics.ridership.growthTrend')}</span>
                  <span className={`text-2xl font-bold ${getTrendColor(ridership.growth_trend)}`}>
                    {getTrendIcon(ridership.growth_trend)} {Math.abs(ridership.growth_trend).toFixed(1)}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Environmental Impact */}
        <motion.div
          variants={fadeUpVariants}
          initial="hidden"
          animate="visible"
          transition={{ delay: 0.3 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8"
        >
          <Card>
            <CardHeader title={t('analytics.environmental.title')} />
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">{t('analytics.environmental.carsOffRoad')}</span>
                  <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {environmental.equivalent_cars_off_road.toFixed(0)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">{t('analytics.environmental.co2PerPassenger')}</span>
                  <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {environmental.co2_saved_per_passenger_kg.toFixed(2)} kg
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">{t('analytics.environmental.totalDistance')}</span>
                  <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {formatNumber(environmental.total_distance_km)} km
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader title={t('analytics.trends.title')} />
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">{t('analytics.trends.delayTrend')}</span>
                  <span className={`text-2xl font-bold ${getTrendColor(trends.delay_trend_percentage)}`}>
                    {getTrendIcon(trends.delay_trend_percentage)} {Math.abs(trends.delay_trend_percentage).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">{t('analytics.trends.recentTrips')}</span>
                  <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {trends.recent_trips_count}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">{t('analytics.trends.dataPeriod')}</span>
                  <span className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                    {trends.data_period_days} days
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Last Updated */}
        <motion.div
          variants={fadeUpVariants}
          initial="hidden"
          animate="visible"
          transition={{ delay: 0.4 }}
          className="text-center text-sm text-gray-500 dark:text-gray-400"
        >
          {t('analytics.lastUpdated')}: {new Date(dashboardData.last_updated).toLocaleString()}
        </motion.div>
      </div>
    </motion.div>
  )
}

export default AnalyticsDashboard

