import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import Card, { CardHeader, CardContent } from './Card'
import Button from './Button'
import { fadeUpVariants, scaleVariants } from '../../design-system/animations'

interface DemandPrediction {
  route_id: number
  prediction_date: string
  predicted_demand: number
  confidence_score: number
  historical_average: number
  trend_percentage: number
  factors: string[]
}

interface DelayPrediction {
  route_id: number
  prediction_date: string
  time_of_day: string
  predicted_delay_minutes: number
  confidence_interval_lower: number
  confidence_interval_upper: number
  confidence_score: number
  factors: string[]
}

interface Route {
  id: number
  name: string
  route_number: string
}

interface PredictiveAnalyticsProps {
  className?: string
}

const PredictiveAnalytics: React.FC<PredictiveAnalyticsProps> = ({ className = '' }) => {
  const { t } = useTranslation()
  const [routes, setRoutes] = useState<Route[]>([])
  const [selectedRoute, setSelectedRoute] = useState<number | null>(null)
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0])
  const [selectedTimeOfDay, setSelectedTimeOfDay] = useState<'morning' | 'afternoon' | 'evening'>('morning')
  const [demandPrediction, setDemandPrediction] = useState<DemandPrediction | null>(null)
  const [delayPrediction, setDelayPrediction] = useState<DelayPrediction | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchRoutes()
  }, [])

  const fetchRoutes = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/v1/routes?active_only=true&limit=50', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setRoutes(data.routes || [])
        if (data.routes && data.routes.length > 0) {
          setSelectedRoute(data.routes[0].id)
        }
      }
    } catch (err) {
      console.error('Error fetching routes:', err)
    }
  }

  const generateDemandPrediction = async () => {
    if (!selectedRoute) return

    try {
      setLoading(true)
      setError(null)

      const token = localStorage.getItem('token')
      const response = await fetch(
        `/api/v1/analytics/demand-prediction?route_id=${selectedRoute}&prediction_date=${selectedDate}&days_ahead=7`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      )

      if (!response.ok) {
        throw new Error('Failed to generate demand prediction')
      }

      const data = await response.json()
      setDemandPrediction(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const generateDelayPrediction = async () => {
    if (!selectedRoute) return

    try {
      setLoading(true)
      setError(null)

      const token = localStorage.getItem('token')
      const response = await fetch(
        `/api/v1/analytics/delay-prediction?route_id=${selectedRoute}&prediction_date=${selectedDate}&time_of_day=${selectedTimeOfDay}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      )

      if (!response.ok) {
        throw new Error('Failed to generate delay prediction')
      }

      const data = await response.json()
      setDelayPrediction(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400'
    if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getConfidenceLabel = (score: number) => {
    if (score >= 0.8) return t('analytics.prediction.high')
    if (score >= 0.6) return t('analytics.prediction.medium')
    return t('analytics.prediction.low')
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toFixed(0)
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Controls */}
      <Card>
        <CardHeader title={t('analytics.prediction.title')} />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('analytics.prediction.route')}
              </label>
              <select
                value={selectedRoute || ''}
                onChange={(e) => setSelectedRoute(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value="">{t('analytics.prediction.selectRoute')}</option>
                {routes.map((route) => (
                  <option key={route.id} value={route.id}>
                    {route.route_number} - {route.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('analytics.prediction.date')}
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('analytics.prediction.timeOfDay')}
              </label>
              <select
                value={selectedTimeOfDay}
                onChange={(e) => setSelectedTimeOfDay(e.target.value as 'morning' | 'afternoon' | 'evening')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value="morning">{t('analytics.prediction.morning')}</option>
                <option value="afternoon">{t('analytics.prediction.afternoon')}</option>
                <option value="evening">{t('analytics.prediction.evening')}</option>
              </select>
            </div>
          </div>

          <div className="flex space-x-4">
            <Button
              onClick={generateDemandPrediction}
              disabled={!selectedRoute || loading}
              variant="primary"
            >
              {loading ? t('common.loading') : t('analytics.prediction.predictDemand')}
            </Button>
            <Button
              onClick={generateDelayPrediction}
              disabled={!selectedRoute || loading}
              variant="outline"
            >
              {loading ? t('common.loading') : t('analytics.prediction.predictDelay')}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
        >
          <div className="flex items-center">
            <div className="text-red-500 text-xl mr-3">⚠️</div>
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        </motion.div>
      )}

      {/* Demand Prediction Results */}
      {demandPrediction && (
        <motion.div
          variants={fadeUpVariants}
          initial="hidden"
          animate="visible"
        >
          <Card>
            <CardHeader title={t('analytics.prediction.demandResults')} />
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                    {formatNumber(demandPrediction.predicted_demand)}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {t('analytics.prediction.predictedDemand')}
                  </div>
                </div>

                <div className="text-center">
                  <div className={`text-3xl font-bold ${getConfidenceColor(demandPrediction.confidence_score)} mb-2`}>
                    {(demandPrediction.confidence_score * 100).toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {getConfidenceLabel(demandPrediction.confidence_score)}
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600 dark:text-green-400 mb-2">
                    {formatNumber(demandPrediction.historical_average)}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {t('analytics.prediction.historicalAverage')}
                  </div>
                </div>

                <div className="text-center">
                  <div className={`text-3xl font-bold ${demandPrediction.trend_percentage >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'} mb-2`}>
                    {demandPrediction.trend_percentage >= 0 ? '+' : ''}{demandPrediction.trend_percentage.toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {t('analytics.prediction.trend')}
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('analytics.prediction.factors')}
                </h4>
                <div className="flex flex-wrap gap-2">
                  {demandPrediction.factors.map((factor, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-full text-sm"
                    >
                      {factor}
                    </span>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Delay Prediction Results */}
      {delayPrediction && (
        <motion.div
          variants={fadeUpVariants}
          initial="hidden"
          animate="visible"
        >
          <Card>
            <CardHeader title={t('analytics.prediction.delayResults')} />
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-600 dark:text-red-400 mb-2">
                    {delayPrediction.predicted_delay_minutes.toFixed(1)} min
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {t('analytics.prediction.predictedDelay')}
                  </div>
                </div>

                <div className="text-center">
                  <div className={`text-3xl font-bold ${getConfidenceColor(delayPrediction.confidence_score)} mb-2`}>
                    {(delayPrediction.confidence_score * 100).toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {getConfidenceLabel(delayPrediction.confidence_score)}
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-600 dark:text-orange-400 mb-2">
                    {delayPrediction.confidence_interval_lower.toFixed(1)} - {delayPrediction.confidence_interval_upper.toFixed(1)} min
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {t('analytics.prediction.confidenceInterval')}
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                    {delayPrediction.time_of_day}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {t('analytics.prediction.timeOfDay')}
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('analytics.prediction.factors')}
                </h4>
                <div className="flex flex-wrap gap-2">
                  {delayPrediction.factors.map((factor, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200 rounded-full text-sm"
                    >
                      {factor}
                    </span>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}

export default PredictiveAnalytics

