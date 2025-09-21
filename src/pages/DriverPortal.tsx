import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Modal } from '../components/ui/Modal'
import { Input } from '../components/ui/Input'
import { TripManagement } from '../components/ui/TripManagement'
import { OccupancyReporter } from '../components/ui/OccupancyReporter'
import { ShiftSchedule } from '../components/ui/ShiftSchedule'
import { IssueReporter } from '../components/ui/IssueReporter'
import { LocationTracker } from '../components/ui/LocationTracker'
import { DriverCommunication } from '../components/ui/DriverCommunication'
import { useToast } from '../hooks/useToast'

// Types for driver portal
interface DriverProfile {
  id: number
  name: string
  phone: string
  license_number: string
  status: 'active' | 'inactive' | 'on_break'
  assigned_vehicle_id?: number
  assigned_vehicle_number?: string
  current_route_id?: number
  current_route_name?: string
}

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

interface ShiftSchedule {
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

interface Issue {
  id: number
  category: string
  priority: string
  title: string
  description: string
  status: string
  created_at: string
}

interface DashboardData {
  driver: DriverProfile
  current_trip?: Trip
  upcoming_shifts: ShiftSchedule[]
  recent_issues: Issue[]
  today_stats: {
    trips_completed: number
    issues_reported: number
    hours_scheduled: number
    status: string
  }
}

interface LoginData {
  phone: string
  password: string
}

const DriverPortal: React.FC = () => {
  const { t } = useTranslation()
  const { showToast } = useToast()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(true)
  const [showOccupancyModal, setShowOccupancyModal] = useState(false)
  const [showIssueModal, setShowIssueModal] = useState(false)
  const [loginData, setLoginData] = useState<LoginData>({ phone: '', password: '' })
  const [occupancyLevel, setOccupancyLevel] = useState<string>('medium')
  const [issueData, setIssueData] = useState({
    category: 'mechanical',
    priority: 'medium',
    title: '',
    description: ''
  })

  // Mock authentication for demo
  const handleLogin = async () => {
    setLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Mock successful login
      if (loginData.phone && loginData.password) {
        setIsAuthenticated(true)
        setShowLoginModal(false)
        await loadDashboard()
        showToast('Login successful', 'success')
      } else {
        showToast('Please enter phone and password', 'error')
      }
    } catch (error) {
      showToast('Login failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Mock dashboard data loading
  const loadDashboard = async () => {
    setLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800))
      
      // Mock dashboard data
      const mockData: DashboardData = {
        driver: {
          id: 1,
          name: 'Rajesh Kumar',
          phone: '+91-9876543210',
          license_number: 'KA05-2023-001234',
          status: 'active',
          assigned_vehicle_id: 1,
          assigned_vehicle_number: 'KA-05-HB-1234',
          current_route_id: 1,
          current_route_name: 'Majestic to Electronic City'
        },
        current_trip: {
          id: 1,
          vehicle_id: 1,
          route_id: 1,
          driver_id: 1,
          start_time: new Date().toISOString(),
          status: 'active',
          created_at: new Date().toISOString(),
          vehicle_number: 'KA-05-HB-1234',
          route_name: 'Majestic to Electronic City',
          route_number: '335E'
        },
        upcoming_shifts: [
          {
            id: 1,
            driver_id: 1,
            start_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
            end_time: new Date(Date.now() + 32 * 60 * 60 * 1000).toISOString(),
            route_id: 1,
            vehicle_id: 1,
            status: 'scheduled',
            route_name: 'Majestic to Electronic City',
            route_number: '335E',
            vehicle_number: 'KA-05-HB-1234'
          }
        ],
        recent_issues: [
          {
            id: 1,
            category: 'mechanical',
            priority: 'medium',
            title: 'AC not working properly',
            description: 'Air conditioning system needs maintenance',
            status: 'open',
            created_at: new Date().toISOString()
          }
        ],
        today_stats: {
          trips_completed: 3,
          issues_reported: 1,
          hours_scheduled: 8.5,
          status: 'active'
        }
      }
      
      setDashboardData(mockData)
    } catch (error) {
      showToast('Failed to load dashboard', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleStartTrip = async () => {
    if (!dashboardData?.current_trip) return
    
    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 500))
      showToast('Trip started successfully', 'success')
      await loadDashboard()
    } catch (error) {
      showToast('Failed to start trip', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleEndTrip = async () => {
    if (!dashboardData?.current_trip) return
    
    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 500))
      showToast('Trip ended successfully', 'success')
      await loadDashboard()
    } catch (error) {
      showToast('Failed to end trip', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleReportOccupancy = async () => {
    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 500))
      setShowOccupancyModal(false)
      showToast('Occupancy reported successfully', 'success')
    } catch (error) {
      showToast('Failed to report occupancy', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleReportIssue = async () => {
    if (!issueData.title || !issueData.description) {
      showToast('Please fill in all fields', 'error')
      return
    }
    
    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 500))
      setShowIssueModal(false)
      setIssueData({ category: 'mechanical', priority: 'medium', title: '', description: '' })
      showToast('Issue reported successfully', 'success')
      await loadDashboard()
    } catch (error) {
      showToast('Failed to report issue', 'error')
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short'
    })
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Modal
          isOpen={showLoginModal}
          onClose={() => {}}
          title="Driver Login"
        >
          <div className="space-y-4">
            <Input
              label="Phone Number"
              type="tel"
              value={loginData.phone}
              onChange={(e) => setLoginData({ ...loginData, phone: e.target.value })}
              placeholder="+91-9876543210"
            />
            <Input
              label="Password"
              type="password"
              value={loginData.password}
              onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
              placeholder="Enter your password"
            />
            <Button
              onClick={handleLogin}
              disabled={loading}
              className="w-full"
            >
              {loading ? 'Logging in...' : 'Login'}
            </Button>
            <p className="text-sm text-gray-500 text-center">
              Demo credentials: Any phone number with password "driver123"
            </p>
          </div>
        </Modal>
      </div>
    )
  }

  if (loading && !dashboardData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen pt-16 p-4 bg-gray-50 dark:bg-gray-900"
    >
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
              Driver Portal
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Welcome back, {dashboardData?.driver.name}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <OccupancyReporter 
              vehicleNumber={dashboardData?.driver.assigned_vehicle_number}
              onReport={(level) => console.log('Occupancy reported:', level)}
              className="w-auto"
            />
            <IssueReporter 
              onReport={(issue) => console.log('Issue reported:', issue)}
              className="w-auto"
            />
            <DriverCommunication
              driverId={dashboardData?.driver.id || 1}
              driverName={dashboardData?.driver.name || 'Driver'}
              onMessageSent={(message) => console.log('Message sent:', message)}
              className="w-auto"
            />
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {dashboardData?.today_stats.trips_completed || 0}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Trips Today</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {dashboardData?.today_stats.hours_scheduled || 0}h
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Hours Scheduled</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
              {dashboardData?.today_stats.issues_reported || 0}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Issues Reported</div>
          </Card>
          <Card className="p-4 text-center">
            <div className={`text-2xl font-bold ${
              dashboardData?.driver.status === 'active' 
                ? 'text-green-600 dark:text-green-400' 
                : 'text-gray-600 dark:text-gray-400'
            }`}>
              {dashboardData?.driver.status === 'active' ? '●' : '○'}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Status</div>
          </Card>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Current Trip */}
          <TripManagement
            currentTrip={dashboardData?.current_trip}
            onTripUpdate={loadDashboard}
          />

          {/* Location Tracking */}
          <LocationTracker
            isActive={dashboardData?.current_trip?.status === 'active'}
            interval={30}
            onLocationUpdate={(location) => console.log('Location update:', location)}
            onError={(error) => showToast(error, 'error')}
          />
        </div>

        <div className="grid lg:grid-cols-1 gap-6">
          {/* Shift Schedule */}
          <ShiftSchedule
            shifts={dashboardData?.upcoming_shifts || []}
          />
        </div>

        {/* Recent Issues */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Recent Issues
          </h2>
          <div className="space-y-3">
            {dashboardData?.recent_issues.length ? (
              dashboardData.recent_issues.map((issue) => (
                <div key={issue.id} className="flex justify-between items-start p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        issue.priority === 'critical' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                        issue.priority === 'high' ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200' :
                        'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                      }`}>
                        {issue.priority}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                        {issue.category}
                      </span>
                    </div>
                    <p className="font-medium text-gray-900 dark:text-white">{issue.title}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{issue.description}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {formatDate(issue.created_at)} at {formatTime(issue.created_at)}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    issue.status === 'open' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                    issue.status === 'resolved' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                    'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                  }`}>
                    {issue.status}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-gray-600 dark:text-gray-400">No recent issues</p>
            )}
          </div>
        </Card>

        {/* Occupancy Modal */}
        <Modal
          isOpen={showOccupancyModal}
          onClose={() => setShowOccupancyModal(false)}
          title="Report Occupancy"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Occupancy Level
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { value: 'empty', label: 'Empty (0-10%)', color: 'bg-green-100 text-green-800' },
                  { value: 'low', label: 'Low (11-30%)', color: 'bg-blue-100 text-blue-800' },
                  { value: 'medium', label: 'Medium (31-60%)', color: 'bg-yellow-100 text-yellow-800' },
                  { value: 'high', label: 'High (61-85%)', color: 'bg-orange-100 text-orange-800' },
                  { value: 'full', label: 'Full (86-100%)', color: 'bg-red-100 text-red-800' }
                ].map((level) => (
                  <button
                    key={level.value}
                    onClick={() => setOccupancyLevel(level.value)}
                    className={`p-3 rounded-lg text-sm font-medium transition-colors ${
                      occupancyLevel === level.value
                        ? level.color
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
                    }`}
                  >
                    {level.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleReportOccupancy} disabled={loading} className="flex-1">
                {loading ? 'Reporting...' : 'Report'}
              </Button>
              <Button onClick={() => setShowOccupancyModal(false)} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </Modal>

        {/* Issue Modal */}
        <Modal
          isOpen={showIssueModal}
          onClose={() => setShowIssueModal(false)}
          title="Report Issue"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Category
                </label>
                <select
                  value={issueData.category}
                  onChange={(e) => setIssueData({ ...issueData, category: e.target.value })}
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option value="mechanical">Mechanical</option>
                  <option value="traffic">Traffic</option>
                  <option value="passenger">Passenger</option>
                  <option value="route">Route</option>
                  <option value="emergency">Emergency</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Priority
                </label>
                <select
                  value={issueData.priority}
                  onChange={(e) => setIssueData({ ...issueData, priority: e.target.value })}
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>
            <Input
              label="Title"
              value={issueData.title}
              onChange={(e) => setIssueData({ ...issueData, title: e.target.value })}
              placeholder="Brief description of the issue"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Description
              </label>
              <textarea
                value={issueData.description}
                onChange={(e) => setIssueData({ ...issueData, description: e.target.value })}
                placeholder="Detailed description of the issue"
                rows={4}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none"
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleReportIssue} disabled={loading} className="flex-1">
                {loading ? 'Reporting...' : 'Report Issue'}
              </Button>
              <Button onClick={() => setShowIssueModal(false)} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </motion.div>
  )
}

export default DriverPortal