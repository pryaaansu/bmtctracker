import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { Card } from './Card'
import { Button } from './Button'
import { useToast } from '../../hooks/useToast'

interface OccupancyLevel {
  value: string
  label: string
  percentage: string
  color: string
  bgColor: string
  icon: string
}

const occupancyLevels: OccupancyLevel[] = [
  {
    value: 'empty',
    label: 'Empty',
    percentage: '0-10%',
    color: 'text-green-700 dark:text-green-300',
    bgColor: 'bg-green-100 dark:bg-green-900/30 border-green-200 dark:border-green-800',
    icon: '🟢'
  },
  {
    value: 'low',
    label: 'Low',
    percentage: '11-30%',
    color: 'text-blue-700 dark:text-blue-300',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800',
    icon: '🔵'
  },
  {
    value: 'medium',
    label: 'Medium',
    percentage: '31-60%',
    color: 'text-yellow-700 dark:text-yellow-300',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900/30 border-yellow-200 dark:border-yellow-800',
    icon: '🟡'
  },
  {
    value: 'high',
    label: 'High',
    percentage: '61-85%',
    color: 'text-orange-700 dark:text-orange-300',
    bgColor: 'bg-orange-100 dark:bg-orange-900/30 border-orange-200 dark:border-orange-800',
    icon: '🟠'
  },
  {
    value: 'full',
    label: 'Full',
    percentage: '86-100%',
    color: 'text-red-700 dark:text-red-300',
    bgColor: 'bg-red-100 dark:bg-red-900/30 border-red-200 dark:border-red-800',
    icon: '🔴'
  }
]

interface OccupancyReporterProps {
  vehicleNumber?: string
  onReport?: (level: string) => void
  className?: string
}

export const OccupancyReporter: React.FC<OccupancyReporterProps> = ({
  vehicleNumber,
  onReport,
  className = ''
}) => {
  const { t } = useTranslation()
  const { showToast } = useToast()
  const [selectedLevel, setSelectedLevel] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [lastReported, setLastReported] = useState<string | null>(null)

  const handleReport = async () => {
    if (!selectedLevel) {
      showToast('Please select an occupancy level', 'error')
      return
    }

    setLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800))
      
      const selectedLevelData = occupancyLevels.find(level => level.value === selectedLevel)
      setLastReported(selectedLevel)
      
      showToast(
        `Occupancy reported as ${selectedLevelData?.label} (${selectedLevelData?.percentage})`,
        'success'
      )
      
      if (onReport) {
        onReport(selectedLevel)
      }
      
      // Reset selection after successful report
      setTimeout(() => setSelectedLevel(''), 2000)
    } catch (error) {
      showToast('Failed to report occupancy', 'error')
    } finally {
      setLoading(false)
    }
  }

  const getQuickReportButtons = () => {
    return [
      { level: 'empty', label: 'Empty', emoji: '🟢' },
      { level: 'medium', label: 'Half', emoji: '🟡' },
      { level: 'full', label: 'Full', emoji: '🔴' }
    ]
  }

  return (
    <Card className={`p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Report Occupancy
        </h2>
        {vehicleNumber && (
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {vehicleNumber}
          </span>
        )}
      </div>

      {/* Quick Report Buttons */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Quick Report
        </h3>
        <div className="grid grid-cols-3 gap-3">
          {getQuickReportButtons().map((button) => (
            <Button
              key={button.level}
              onClick={() => {
                setSelectedLevel(button.level)
                handleReport()
              }}
              variant="outline"
              disabled={loading}
              className="flex flex-col items-center gap-2 h-auto py-3"
            >
              <span className="text-2xl">{button.emoji}</span>
              <span className="text-sm">{button.label}</span>
            </Button>
          ))}
        </div>
      </div>

      {/* Detailed Selection */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Detailed Selection
        </h3>
        <div className="space-y-2">
          {occupancyLevels.map((level) => (
            <motion.button
              key={level.value}
              onClick={() => setSelectedLevel(level.value)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`w-full p-4 rounded-lg border-2 transition-all ${
                selectedLevel === level.value
                  ? level.bgColor
                  : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{level.icon}</span>
                  <div className="text-left">
                    <p className={`font-medium ${
                      selectedLevel === level.value 
                        ? level.color 
                        : 'text-gray-900 dark:text-white'
                    }`}>
                      {level.label}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {level.percentage} capacity
                    </p>
                  </div>
                </div>
                {selectedLevel === level.value && (
                  <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Report Button */}
      <Button
        onClick={handleReport}
        disabled={!selectedLevel || loading}
        className="w-full"
      >
        {loading ? (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            Reporting...
          </div>
        ) : (
          'Report Occupancy'
        )}
      </Button>

      {/* Last Reported */}
      {lastReported && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg"
        >
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <p className="text-sm text-green-700 dark:text-green-300">
              Last reported: {occupancyLevels.find(l => l.value === lastReported)?.label} at{' '}
              {new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
            </p>
          </div>
        </motion.div>
      )}

      {/* Tips */}
      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <h4 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-1">
          💡 Reporting Tips
        </h4>
        <ul className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
          <li>• Report occupancy at major stops for better passenger information</li>
          <li>• Use quick report buttons for faster updates during busy periods</li>
          <li>• Regular reporting helps improve ETA accuracy</li>
        </ul>
      </div>
    </Card>
  )
}

export default OccupancyReporter