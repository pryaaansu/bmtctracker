import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'

interface Route {
  id: number
  name: string
  route_number: string
  is_active: boolean
}

interface FilterOptions {
  routes: number[]
  serviceTypes: string[]
  maxDistance?: number
  showActiveOnly: boolean
}

interface FilterPanelProps {
  isOpen: boolean
  onClose: () => void
  onFiltersChange: (filters: FilterOptions) => void
  userLocation?: { lat: number; lng: number } | null
  className?: string
}

const FilterPanel: React.FC<FilterPanelProps> = ({
  isOpen,
  onClose,
  onFiltersChange,
  userLocation,
  className = ''
}) => {
  const { t } = useTranslation()
  const [routes, setRoutes] = useState<Route[]>([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState<FilterOptions>({
    routes: [],
    serviceTypes: [],
    maxDistance: userLocation ? 5 : undefined,
    showActiveOnly: true
  })

  // Service types for BMTC
  const serviceTypes = [
    { id: 'ordinary', name: 'Ordinary', name_kannada: 'ಸಾಮಾನ್ಯ' },
    { id: 'volvo', name: 'Volvo AC', name_kannada: 'ವೋಲ್ವೋ ಎಸಿ' },
    { id: 'vajra', name: 'Vajra', name_kannada: 'ವಜ್ರ' },
    { id: 'atal_sarige', name: 'Atal Sarige', name_kannada: 'ಅಟಲ್ ಸಾರಿಗೆ' },
    { id: 'express', name: 'Express', name_kannada: 'ಎಕ್ಸ್‌ಪ್ರೆಸ್' }
  ]

  // Distance options
  const distanceOptions = [
    { value: 1, label: '1 km' },
    { value: 2, label: '2 km' },
    { value: 5, label: '5 km' },
    { value: 10, label: '10 km' },
    { value: 20, label: '20 km' }
  ]

  // Load routes on component mount
  useEffect(() => {
    if (isOpen) {
      loadRoutes()
    }
  }, [isOpen])

  const loadRoutes = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/v1/routes?limit=100&active_only=true')
      if (!response.ok) throw new Error('Failed to load routes')
      
      const data = await response.json()
      setRoutes(data.routes || [])
    } catch (error) {
      console.error('Failed to load routes:', error)
    } finally {
      setLoading(false)
    }
  }

  // Handle filter changes
  const updateFilters = (newFilters: Partial<FilterOptions>) => {
    const updated = { ...filters, ...newFilters }
    setFilters(updated)
    onFiltersChange(updated)
  }

  // Handle route selection
  const toggleRoute = (routeId: number) => {
    const newRoutes = filters.routes.includes(routeId)
      ? filters.routes.filter(id => id !== routeId)
      : [...filters.routes, routeId]
    
    updateFilters({ routes: newRoutes })
  }

  // Handle service type selection
  const toggleServiceType = (serviceType: string) => {
    const newServiceTypes = filters.serviceTypes.includes(serviceType)
      ? filters.serviceTypes.filter(type => type !== serviceType)
      : [...filters.serviceTypes, serviceType]
    
    updateFilters({ serviceTypes: newServiceTypes })
  }

  // Clear all filters
  const clearFilters = () => {
    const clearedFilters: FilterOptions = {
      routes: [],
      serviceTypes: [],
      maxDistance: userLocation ? 5 : undefined,
      showActiveOnly: true
    }
    setFilters(clearedFilters)
    onFiltersChange(clearedFilters)
  }

  // Get active filter count
  const getActiveFilterCount = () => {
    return filters.routes.length + filters.serviceTypes.length + 
           (filters.maxDistance && filters.maxDistance < 20 ? 1 : 0) +
           (!filters.showActiveOnly ? 1 : 0)
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
          />
          
          {/* Filter Panel */}
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className={`fixed left-0 top-0 h-full w-80 bg-white dark:bg-gray-800 shadow-xl z-50 overflow-y-auto ${className}`}
          >
            {/* Header */}
            <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 z-10">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {t('common.filter')}
                </h2>
                <div className="flex items-center space-x-2">
                  {getActiveFilterCount() > 0 && (
                    <span className="px-2 py-1 text-xs font-medium bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200 rounded-full">
                      {getActiveFilterCount()}
                    </span>
                  )}
                  <button
                    onClick={onClose}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              
              {getActiveFilterCount() > 0 && (
                <button
                  onClick={clearFilters}
                  className="mt-2 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200"
                >
                  Clear all filters
                </button>
              )}
            </div>

            <div className="p-4 space-y-6">
              {/* Distance Filter */}
              {userLocation && (
                <div>
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                    Maximum Distance
                  </h3>
                  <div className="space-y-2">
                    {distanceOptions.map((option) => (
                      <label key={option.value} className="flex items-center">
                        <input
                          type="radio"
                          name="distance"
                          value={option.value}
                          checked={filters.maxDistance === option.value}
                          onChange={() => updateFilters({ maxDistance: option.value })}
                          className="w-4 h-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                        />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                          {option.label}
                        </span>
                      </label>
                    ))}
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="distance"
                        checked={!filters.maxDistance || filters.maxDistance >= 50}
                        onChange={() => updateFilters({ maxDistance: undefined })}
                        className="w-4 h-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                      />
                      <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                        No limit
                      </span>
                    </label>
                  </div>
                </div>
              )}

              {/* Service Type Filter */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                  Service Type
                </h3>
                <div className="space-y-2">
                  {serviceTypes.map((service) => (
                    <label key={service.id} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.serviceTypes.includes(service.id)}
                        onChange={() => toggleServiceType(service.id)}
                        className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                      />
                      <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                        {service.name}
                        {service.name_kannada && (
                          <span className="text-gray-500 dark:text-gray-400 ml-1">
                            ({service.name_kannada})
                          </span>
                        )}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Route Filter */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                  Routes
                </h3>
                
                {loading ? (
                  <div className="space-y-2">
                    {[...Array(5)].map((_, i) => (
                      <div key={i} className="animate-pulse">
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {routes.map((route) => (
                      <label key={route.id} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={filters.routes.includes(route.id)}
                          onChange={() => toggleRoute(route.id)}
                          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                        />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                          <span className="font-medium">{route.route_number}</span>
                          <span className="text-gray-500 dark:text-gray-400 ml-1">
                            - {route.name}
                          </span>
                        </span>
                      </label>
                    ))}
                    
                    {routes.length === 0 && !loading && (
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        No routes available
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Active Only Toggle */}
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.showActiveOnly}
                    onChange={(e) => updateFilters({ showActiveOnly: e.target.checked })}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    Show active routes only
                  </span>
                </label>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default FilterPanel