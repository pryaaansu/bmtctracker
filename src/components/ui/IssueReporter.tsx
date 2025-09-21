import React, { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { Card } from './Card'
import { Button } from './Button'
import { Input } from './Input'
import { Modal } from './Modal'
import { useToast } from '../../hooks/useToast'

interface IssueCategory {
  value: string
  label: string
  icon: string
  color: string
  examples: string[]
}

interface IssuePriority {
  value: string
  label: string
  color: string
  description: string
}

const issueCategories: IssueCategory[] = [
  {
    value: 'mechanical',
    label: 'Mechanical',
    icon: '🔧',
    color: 'text-blue-700 dark:text-blue-300',
    examples: ['Engine problems', 'Brake issues', 'AC not working', 'Door malfunction']
  },
  {
    value: 'traffic',
    label: 'Traffic',
    icon: '🚦',
    color: 'text-orange-700 dark:text-orange-300',
    examples: ['Road blockage', 'Heavy traffic', 'Accident ahead', 'Route deviation']
  },
  {
    value: 'passenger',
    label: 'Passenger',
    icon: '👥',
    color: 'text-green-700 dark:text-green-300',
    examples: ['Unruly passenger', 'Medical emergency', 'Lost item', 'Complaint']
  },
  {
    value: 'route',
    label: 'Route',
    icon: '🗺️',
    color: 'text-purple-700 dark:text-purple-300',
    examples: ['Road closure', 'Construction work', 'New route needed', 'Stop issues']
  },
  {
    value: 'emergency',
    label: 'Emergency',
    icon: '🚨',
    color: 'text-red-700 dark:text-red-300',
    examples: ['Accident', 'Fire', 'Medical emergency', 'Security threat']
  },
  {
    value: 'other',
    label: 'Other',
    icon: '📝',
    color: 'text-gray-700 dark:text-gray-300',
    examples: ['General inquiry', 'Suggestion', 'Administrative', 'Miscellaneous']
  }
]

const issuePriorities: IssuePriority[] = [
  {
    value: 'low',
    label: 'Low',
    color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    description: 'Minor issues that can wait'
  },
  {
    value: 'medium',
    label: 'Medium',
    color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    description: 'Issues that need attention soon'
  },
  {
    value: 'high',
    label: 'High',
    color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    description: 'Important issues requiring quick action'
  },
  {
    value: 'critical',
    label: 'Critical',
    color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    description: 'Urgent issues requiring immediate attention'
  }
]

interface IssueReporterProps {
  onReport?: (issueData: any) => void
  className?: string
}

export const IssueReporter: React.FC<IssueReporterProps> = ({
  onReport,
  className = ''
}) => {
  const { t } = useTranslation()
  const { showToast } = useToast()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [currentLocation, setCurrentLocation] = useState<{lat: number, lng: number} | null>(null)
  const [locationLoading, setLocationLoading] = useState(false)
  
  const [issueData, setIssueData] = useState({
    category: 'mechanical',
    priority: 'medium',
    title: '',
    description: '',
    photos: [] as File[],
    location_lat: null as number | null,
    location_lng: null as number | null,
    vehicle_id: null as number | null,
    route_id: null as number | null
  })

  const getCurrentLocation = async () => {
    setLocationLoading(true)
    try {
      if (!navigator.geolocation) {
        throw new Error('Geolocation is not supported by this browser')
      }

      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000
        })
      })

      const location = {
        lat: position.coords.latitude,
        lng: position.coords.longitude
      }

      setCurrentLocation(location)
      setIssueData(prev => ({
        ...prev,
        location_lat: location.lat,
        location_lng: location.lng
      }))

      showToast('Location captured successfully', 'success')
    } catch (error) {
      console.error('Error getting location:', error)
      showToast('Failed to get location. Please try again.', 'error')
    } finally {
      setLocationLoading(false)
    }
  }

  const handlePhotoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    
    if (files.length === 0) return

    // Validate file types and sizes
    const validFiles = files.filter(file => {
      const isValidType = file.type.startsWith('image/')
      const isValidSize = file.size <= 5 * 1024 * 1024 // 5MB limit
      
      if (!isValidType) {
        showToast(`${file.name} is not a valid image file`, 'error')
        return false
      }
      
      if (!isValidSize) {
        showToast(`${file.name} is too large (max 5MB)`, 'error')
        return false
      }
      
      return true
    })

    if (issueData.photos.length + validFiles.length > 3) {
      showToast('Maximum 3 photos allowed', 'error')
      return
    }

    setIssueData(prev => ({
      ...prev,
      photos: [...prev.photos, ...validFiles]
    }))

    showToast(`${validFiles.length} photo(s) added`, 'success')
  }

  const removePhoto = (index: number) => {
    setIssueData(prev => ({
      ...prev,
      photos: prev.photos.filter((_, i) => i !== index)
    }))
  }

  const handleSubmit = async () => {
    if (!issueData.title.trim() || !issueData.description.trim()) {
      showToast('Please fill in title and description', 'error')
      return
    }

    setLoading(true)
    try {
      // Simulate API call with photo upload
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const reportData = {
        ...issueData,
        timestamp: new Date().toISOString(),
        photos: issueData.photos.map(photo => ({
          name: photo.name,
          size: photo.size,
          type: photo.type
        }))
      }

      if (onReport) {
        onReport(reportData)
      }

      showToast('Issue reported successfully', 'success')
      
      // Reset form
      setIssueData({
        category: 'mechanical',
        priority: 'medium',
        title: '',
        description: '',
        photos: [],
        location_lat: null,
        location_lng: null,
        vehicle_id: null,
        route_id: null
      })
      setCurrentLocation(null)
      setIsOpen(false)
      
    } catch (error) {
      showToast('Failed to report issue', 'error')
    } finally {
      setLoading(false)
    }
  }

  const selectedCategory = issueCategories.find(cat => cat.value === issueData.category)
  const selectedPriority = issuePriorities.find(pri => pri.value === issueData.priority)

  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        className={`flex items-center gap-2 ${className}`}
        variant="outline"
      >
        <span className="text-lg">📝</span>
        Report Issue
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Report Issue"
        size="lg"
      >
        <div className="space-y-6 max-h-[70vh] overflow-y-auto">
          {/* Category Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Issue Category
            </label>
            <div className="grid grid-cols-2 gap-3">
              {issueCategories.map((category) => (
                <motion.button
                  key={category.value}
                  onClick={() => setIssueData(prev => ({ ...prev, category: category.value }))}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`p-3 rounded-lg border-2 transition-all text-left ${
                    issueData.category === category.value
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xl">{category.icon}</span>
                    <span className={`font-medium ${category.color}`}>
                      {category.label}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {category.examples[0]}
                  </p>
                </motion.button>
              ))}
            </div>
          </div>

          {/* Priority Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Priority Level
            </label>
            <div className="grid grid-cols-2 gap-3">
              {issuePriorities.map((priority) => (
                <motion.button
                  key={priority.value}
                  onClick={() => setIssueData(prev => ({ ...prev, priority: priority.value }))}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`p-3 rounded-lg border-2 transition-all text-left ${
                    issueData.priority === priority.value
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {priority.label}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${priority.color}`}>
                      {priority.label}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {priority.description}
                  </p>
                </motion.button>
              ))}
            </div>
          </div>

          {/* Title and Description */}
          <div className="space-y-4">
            <Input
              label="Issue Title"
              value={issueData.title}
              onChange={(e) => setIssueData(prev => ({ ...prev, title: e.target.value }))}
              placeholder="Brief description of the issue"
              maxLength={200}
            />
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Detailed Description
              </label>
              <textarea
                value={issueData.description}
                onChange={(e) => setIssueData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Provide detailed information about the issue"
                rows={4}
                maxLength={1000}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {issueData.description.length}/1000 characters
              </p>
            </div>
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Location
            </label>
            <div className="flex items-center gap-3">
              <Button
                onClick={getCurrentLocation}
                disabled={locationLoading}
                variant="outline"
                size="sm"
              >
                {locationLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                    Getting Location...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <span>📍</span>
                    Capture Location
                  </div>
                )}
              </Button>
              
              {currentLocation && (
                <div className="flex-1 p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <p className="text-sm text-green-700 dark:text-green-300">
                    📍 Location captured: {currentLocation.lat.toFixed(6)}, {currentLocation.lng.toFixed(6)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Photo Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Photos (Optional)
            </label>
            
            <div className="space-y-3">
              {/* Upload Button */}
              <Button
                onClick={() => fileInputRef.current?.click()}
                variant="outline"
                size="sm"
                disabled={issueData.photos.length >= 3}
              >
                <div className="flex items-center gap-2">
                  <span>📷</span>
                  Add Photos ({issueData.photos.length}/3)
                </div>
              </Button>
              
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={handlePhotoUpload}
                className="hidden"
              />

              {/* Photo Preview */}
              <AnimatePresence>
                {issueData.photos.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="grid grid-cols-3 gap-3"
                  >
                    {issueData.photos.map((photo, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="relative group"
                      >
                        <div className="aspect-square bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden">
                          <img
                            src={URL.createObjectURL(photo)}
                            alt={`Issue photo ${index + 1}`}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <button
                          onClick={() => removePhoto(index)}
                          className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          ×
                        </button>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                          {photo.name}
                        </p>
                      </motion.div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Summary */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 dark:text-white mb-2">Issue Summary</h4>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <span>{selectedCategory?.icon}</span>
                <span className="text-gray-600 dark:text-gray-400">Category:</span>
                <span className={selectedCategory?.color}>{selectedCategory?.label}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${selectedPriority?.color}`}>
                  {selectedPriority?.label}
                </span>
                <span className="text-gray-600 dark:text-gray-400">Priority</span>
              </div>
              {currentLocation && (
                <div className="flex items-center gap-2">
                  <span>📍</span>
                  <span className="text-gray-600 dark:text-gray-400">Location captured</span>
                </div>
              )}
              {issueData.photos.length > 0 && (
                <div className="flex items-center gap-2">
                  <span>📷</span>
                  <span className="text-gray-600 dark:text-gray-400">
                    {issueData.photos.length} photo(s) attached
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Button
              onClick={handleSubmit}
              disabled={loading || !issueData.title.trim() || !issueData.description.trim()}
              className="flex-1"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Reporting Issue...
                </div>
              ) : (
                'Report Issue'
              )}
            </Button>
            <Button
              onClick={() => setIsOpen(false)}
              variant="outline"
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </>
  )
}

export default IssueReporter