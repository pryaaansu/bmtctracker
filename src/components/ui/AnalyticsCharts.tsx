import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import Card, { CardHeader, CardContent } from './Card'
import { fadeUpVariants } from '../../design-system/animations'

interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string
    borderColor?: string
    borderWidth?: number
  }[]
}

interface AnalyticsChartsProps {
  performanceData?: any
  ridershipData?: any
  environmentalData?: any
  className?: string
}

const AnalyticsCharts: React.FC<AnalyticsChartsProps> = ({
  performanceData,
  ridershipData,
  environmentalData,
  className = ''
}) => {
  const { t } = useTranslation()
  const [selectedChart, setSelectedChart] = useState<'performance' | 'ridership' | 'environmental'>('performance')

  // Mock data for demonstration (in real app, this would come from props)
  const mockPerformanceData = {
    dailyOnTime: [
      { day: 'Mon', percentage: 85 },
      { day: 'Tue', percentage: 78 },
      { day: 'Wed', percentage: 92 },
      { day: 'Thu', percentage: 88 },
      { day: 'Fri', percentage: 75 },
      { day: 'Sat', percentage: 95 },
      { day: 'Sun', percentage: 90 }
    ],
    hourlyDelays: [
      { hour: '6AM', delay: 5 },
      { hour: '8AM', delay: 12 },
      { hour: '10AM', delay: 3 },
      { hour: '12PM', delay: 8 },
      { hour: '2PM', delay: 4 },
      { hour: '4PM', delay: 15 },
      { hour: '6PM', delay: 18 },
      { hour: '8PM', delay: 7 }
    ]
  }

  const mockRidershipData = {
    dailyPassengers: [
      { day: 'Mon', passengers: 1250 },
      { day: 'Tue', passengers: 1180 },
      { day: 'Wed', passengers: 1320 },
      { day: 'Thu', passengers: 1280 },
      { day: 'Fri', passengers: 1100 },
      { day: 'Sat', passengers: 850 },
      { day: 'Sun', passengers: 720 }
    ],
    hourlyOccupancy: [
      { hour: '6AM', occupancy: 45 },
      { hour: '8AM', occupancy: 85 },
      { hour: '10AM', occupancy: 60 },
      { hour: '12PM', occupancy: 70 },
      { hour: '2PM', occupancy: 55 },
      { hour: '4PM', occupancy: 90 },
      { hour: '6PM', occupancy: 95 },
      { hour: '8PM', occupancy: 40 }
    ]
  }

  const mockEnvironmentalData = {
    co2Savings: [
      { month: 'Jan', co2: 1250 },
      { month: 'Feb', co2: 1180 },
      { month: 'Mar', co2: 1320 },
      { month: 'Apr', co2: 1280 },
      { month: 'May', co2: 1100 },
      { month: 'Jun', co2: 1050 }
    ],
    carsOffRoad: [
      { month: 'Jan', cars: 45 },
      { month: 'Feb', cars: 42 },
      { month: 'Mar', cars: 48 },
      { month: 'Apr', cars: 46 },
      { month: 'May', cars: 40 },
      { month: 'Jun', cars: 38 }
    ]
  }

  const SimpleBarChart: React.FC<{ data: any[], title: string, color: string, yAxisLabel: string }> = ({
    data,
    title,
    color,
    yAxisLabel
  }) => {
    const maxValue = Math.max(...data.map(d => d.percentage || d.delay || d.passengers || d.occupancy || d.co2 || d.cars))
    
    return (
      <div className="space-y-4">
        <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h4>
        <div className="space-y-2">
          {data.map((item, index) => {
            const value = item.percentage || item.delay || item.passengers || item.occupancy || item.co2 || item.cars
            const percentage = (value / maxValue) * 100
            
            return (
              <div key={index} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">{item.day || item.hour || item.month}</span>
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {typeof value === 'number' ? value.toFixed(0) : value}
                    {item.percentage !== undefined ? '%' : ''}
                    {item.delay !== undefined ? ' min' : ''}
                    {item.passengers !== undefined ? ' pax' : ''}
                    {item.occupancy !== undefined ? '%' : ''}
                    {item.co2 !== undefined ? ' kg' : ''}
                    {item.cars !== undefined ? ' cars' : ''}
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <motion.div
                    className={`h-3 rounded-full ${color}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 1, delay: index * 0.1 }}
                  />
                </div>
              </div>
            )
          })}
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
          {yAxisLabel}
        </div>
      </div>
    )
  }

  const LineChart: React.FC<{ data: any[], title: string, color: string, yAxisLabel: string }> = ({
    data,
    title,
    color,
    yAxisLabel
  }) => {
    const maxValue = Math.max(...data.map(d => d.percentage || d.delay || d.passengers || d.occupancy || d.co2 || d.cars))
    const minValue = Math.min(...data.map(d => d.percentage || d.delay || d.passengers || d.occupancy || d.co2 || d.cars))
    const range = maxValue - minValue
    
    return (
      <div className="space-y-4">
        <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h4>
        <div className="relative h-48 bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <svg className="w-full h-full" viewBox="0 0 400 200">
            {data.map((item, index) => {
              const value = item.percentage || item.delay || item.passengers || item.occupancy || item.co2 || item.cars
              const x = (index / (data.length - 1)) * 360 + 20
              const y = 180 - ((value - minValue) / range) * 160
              
              return (
                <g key={index}>
                  <circle
                    cx={x}
                    cy={y}
                    r="4"
                    fill={color.replace('bg-', '#').replace('-500', '')}
                    className="opacity-80"
                  />
                  {index > 0 && (
                    <line
                      x1={((index - 1) / (data.length - 1)) * 360 + 20}
                      y1={180 - ((data[index - 1].percentage || data[index - 1].delay || data[index - 1].passengers || data[index - 1].occupancy || data[index - 1].co2 || data[index - 1].cars - minValue) / range) * 160}
                      x2={x}
                      y2={y}
                      stroke={color.replace('bg-', '#').replace('-500', '')}
                      strokeWidth="2"
                      className="opacity-60"
                    />
                  )}
                </g>
              )
            })}
          </svg>
          <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-gray-500 dark:text-gray-400 px-4 pb-2">
            {data.map((item, index) => (
              <span key={index}>{item.day || item.hour || item.month}</span>
            ))}
          </div>
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
          {yAxisLabel}
        </div>
      </div>
    )
  }

  const renderPerformanceCharts = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardContent className="p-6">
          <SimpleBarChart
            data={mockPerformanceData.dailyOnTime}
            title={t('analytics.charts.dailyOnTime')}
            color="bg-green-500"
            yAxisLabel={t('analytics.charts.onTimePercentage')}
          />
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-6">
          <LineChart
            data={mockPerformanceData.hourlyDelays}
            title={t('analytics.charts.hourlyDelays')}
            color="bg-red-500"
            yAxisLabel={t('analytics.charts.delayMinutes')}
          />
        </CardContent>
      </Card>
    </div>
  )

  const renderRidershipCharts = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardContent className="p-6">
          <LineChart
            data={mockRidershipData.dailyPassengers}
            title={t('analytics.charts.dailyPassengers')}
            color="bg-blue-500"
            yAxisLabel={t('analytics.charts.passengerCount')}
          />
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-6">
          <SimpleBarChart
            data={mockRidershipData.hourlyOccupancy}
            title={t('analytics.charts.hourlyOccupancy')}
            color="bg-purple-500"
            yAxisLabel={t('analytics.charts.occupancyPercentage')}
          />
        </CardContent>
      </Card>
    </div>
  )

  const renderEnvironmentalCharts = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardContent className="p-6">
          <LineChart
            data={mockEnvironmentalData.co2Savings}
            title={t('analytics.charts.co2Savings')}
            color="bg-green-500"
            yAxisLabel={t('analytics.charts.co2Kg')}
          />
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-6">
          <SimpleBarChart
            data={mockEnvironmentalData.carsOffRoad}
            title={t('analytics.charts.carsOffRoad')}
            color="bg-orange-500"
            yAxisLabel={t('analytics.charts.carCount')}
          />
        </CardContent>
      </Card>
    </div>
  )

  return (
    <motion.div
      variants={fadeUpVariants}
      initial="hidden"
      animate="visible"
      className={`space-y-6 ${className}`}
    >
      {/* Chart Type Selector */}
      <Card>
        <CardContent className="p-6">
          <div className="flex space-x-4">
            <button
              onClick={() => setSelectedChart('performance')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedChart === 'performance'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {t('analytics.charts.performance')}
            </button>
            <button
              onClick={() => setSelectedChart('ridership')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedChart === 'ridership'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {t('analytics.charts.ridership')}
            </button>
            <button
              onClick={() => setSelectedChart('environmental')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedChart === 'environmental'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {t('analytics.charts.environmental')}
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Charts */}
      {selectedChart === 'performance' && renderPerformanceCharts()}
      {selectedChart === 'ridership' && renderRidershipCharts()}
      {selectedChart === 'environmental' && renderEnvironmentalCharts()}
    </motion.div>
  )
}

export default AnalyticsCharts

