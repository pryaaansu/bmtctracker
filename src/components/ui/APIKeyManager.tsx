import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import Card, { CardHeader, CardContent } from './Card'
import Button from './Button'
import { fadeUpVariants, scaleVariants } from '../../design-system/animations'

interface APIKey {
  id: number
  key_name: string
  key_prefix: string
  is_active: boolean
  permissions: string[] | null
  rate_limits: {
    requests_per_minute: number
    requests_per_hour: number
    requests_per_day: number
  }
  total_requests: number
  last_used: string | null
  expires_at: string | null
  description: string | null
  created_at: string
  created_by: number | null
}

interface APIKeyStats {
  total_requests: number
  successful_requests: number
  error_requests: number
  success_rate: number
  average_response_time_ms: number
  most_used_endpoints: Array<{ endpoint: string; count: number }>
  period_days: number
}

interface APIKeyManagerProps {
  className?: string
}

const APIKeyManager: React.FC<APIKeyManagerProps> = ({ className = '' }) => {
  const { t } = useTranslation()
  const [apiKeys, setApiKeys] = useState<APIKey[]>([])
  const [selectedKey, setSelectedKey] = useState<APIKey | null>(null)
  const [keyStats, setKeyStats] = useState<APIKeyStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showKeyDetails, setShowKeyDetails] = useState(false)

  // Form state for creating new API key
  const [newKeyForm, setNewKeyForm] = useState({
    key_name: '',
    permissions: [] as string[],
    requests_per_minute: 60,
    requests_per_hour: 1000,
    requests_per_day: 10000,
    expires_in_days: null as number | null,
    description: ''
  })

  useEffect(() => {
    fetchAPIKeys()
  }, [])

  const fetchAPIKeys = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const token = localStorage.getItem('token')
      const response = await fetch('/api/v1/api-keys', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch API keys')
      }

      const data = await response.json()
      setApiKeys(data.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const fetchKeyStats = async (keyId: number) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/v1/api-keys/${keyId}/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch key statistics')
      }

      const data = await response.json()
      setKeyStats(data.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch statistics')
    }
  }

  const createAPIKey = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const token = localStorage.getItem('token')
      const response = await fetch('/api/v1/api-keys', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newKeyForm),
      })

      if (!response.ok) {
        throw new Error('Failed to create API key')
      }

      const data = await response.json()
      
      // Show the new API key (this is the only time the full key is returned)
      setShowKeyDetails(true)
      setSelectedKey(data.data)
      
      // Reset form
      setNewKeyForm({
        key_name: '',
        permissions: [],
        requests_per_minute: 60,
        requests_per_hour: 1000,
        requests_per_day: 10000,
        expires_in_days: null,
        description: ''
      })
      setShowCreateForm(false)
      
      // Refresh the list
      await fetchAPIKeys()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create API key')
    } finally {
      setLoading(false)
    }
  }

  const revokeAPIKey = async (keyId: number) => {
    if (!window.confirm('Are you sure you want to revoke this API key?')) {
      return
    }

    try {
      setLoading(true)
      setError(null)
      
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/v1/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to revoke API key')
      }

      // Refresh the list
      await fetchAPIKeys()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke API key')
    } finally {
      setLoading(false)
    }
  }

  const toggleKeyStatus = async (keyId: number, isActive: boolean) => {
    try {
      setLoading(true)
      setError(null)
      
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/v1/api-keys/${keyId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_active: !isActive }),
      })

      if (!response.ok) {
        throw new Error('Failed to update API key')
      }

      // Refresh the list
      await fetchAPIKeys()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update API key')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleString()
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toString()
  }

  if (loading && apiKeys.length === 0) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-64 mb-4"></div>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      variants={fadeUpVariants}
      initial="hidden"
      animate="visible"
      className={`space-y-6 ${className}`}
    >
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {t('apiKeys.title')}
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            {t('apiKeys.subtitle')}
          </p>
        </div>
        <Button
          onClick={() => setShowCreateForm(true)}
          variant="primary"
        >
          {t('apiKeys.createNew')}
        </Button>
      </div>

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

      {/* API Keys List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {apiKeys.map((key) => (
          <Card key={key.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {key.key_name}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {key.key_prefix}...
                  </p>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => toggleKeyStatus(key.id, key.is_active)}
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      key.is_active
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                        : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                    }`}
                  >
                    {key.is_active ? t('apiKeys.active') : t('apiKeys.inactive')}
                  </button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">{t('apiKeys.totalRequests')}</span>
                    <p className="font-medium">{formatNumber(key.total_requests)}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">{t('apiKeys.lastUsed')}</span>
                    <p className="font-medium">{formatDate(key.last_used)}</p>
                  </div>
                </div>
                
                <div className="text-sm">
                  <span className="text-gray-500 dark:text-gray-400">{t('apiKeys.rateLimits')}</span>
                  <div className="mt-1 space-y-1">
                    <p>{key.rate_limits.requests_per_minute}/min</p>
                    <p>{key.rate_limits.requests_per_hour}/hour</p>
                    <p>{key.rate_limits.requests_per_day}/day</p>
                  </div>
                </div>

                {key.description && (
                  <div className="text-sm">
                    <span className="text-gray-500 dark:text-gray-400">{t('apiKeys.description')}</span>
                    <p className="mt-1">{key.description}</p>
                  </div>
                )}

                <div className="flex space-x-2 pt-2">
                  <Button
                    onClick={() => {
                      setSelectedKey(key)
                      fetchKeyStats(key.id)
                      setShowKeyDetails(true)
                    }}
                    variant="outline"
                    size="sm"
                  >
                    {t('apiKeys.viewDetails')}
                  </Button>
                  <Button
                    onClick={() => revokeAPIKey(key.id)}
                    variant="outline"
                    size="sm"
                    className="text-red-600 hover:text-red-700"
                  >
                    {t('apiKeys.revoke')}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Create API Key Form */}
      {showCreateForm && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        >
          <Card className="w-full max-w-md mx-4">
            <CardHeader>
              <h3 className="text-lg font-semibold">{t('apiKeys.createNew')}</h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('apiKeys.keyName')}
                  </label>
                  <input
                    type="text"
                    value={newKeyForm.key_name}
                    onChange={(e) => setNewKeyForm({ ...newKeyForm, key_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                    placeholder={t('apiKeys.keyNamePlaceholder')}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('apiKeys.description')}
                  </label>
                  <textarea
                    value={newKeyForm.description}
                    onChange={(e) => setNewKeyForm({ ...newKeyForm, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                    rows={3}
                    placeholder={t('apiKeys.descriptionPlaceholder')}
                  />
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {t('apiKeys.perMinute')}
                    </label>
                    <input
                      type="number"
                      value={newKeyForm.requests_per_minute}
                      onChange={(e) => setNewKeyForm({ ...newKeyForm, requests_per_minute: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {t('apiKeys.perHour')}
                    </label>
                    <input
                      type="number"
                      value={newKeyForm.requests_per_hour}
                      onChange={(e) => setNewKeyForm({ ...newKeyForm, requests_per_hour: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {t('apiKeys.perDay')}
                    </label>
                    <input
                      type="number"
                      value={newKeyForm.requests_per_day}
                      onChange={(e) => setNewKeyForm({ ...newKeyForm, requests_per_day: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                    />
                  </div>
                </div>

                <div className="flex space-x-3 pt-4">
                  <Button
                    onClick={createAPIKey}
                    variant="primary"
                    disabled={loading || !newKeyForm.key_name}
                  >
                    {loading ? t('common.creating') : t('apiKeys.create')}
                  </Button>
                  <Button
                    onClick={() => setShowCreateForm(false)}
                    variant="outline"
                  >
                    {t('common.cancel')}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Key Details Modal */}
      {showKeyDetails && selectedKey && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        >
          <Card className="w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex justify-between items-start">
                <h3 className="text-lg font-semibold">{selectedKey.key_name}</h3>
                <button
                  onClick={() => setShowKeyDetails(false)}
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  ✕
                </button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Key Information */}
                <div>
                  <h4 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-3">
                    {t('apiKeys.keyInformation')}
                  </h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">{t('apiKeys.keyPrefix')}</span>
                      <p className="font-mono">{selectedKey.key_prefix}...</p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">{t('apiKeys.status')}</span>
                      <p className={selectedKey.is_active ? 'text-green-600' : 'text-red-600'}>
                        {selectedKey.is_active ? t('apiKeys.active') : t('apiKeys.inactive')}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">{t('apiKeys.createdAt')}</span>
                      <p>{formatDate(selectedKey.created_at)}</p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">{t('apiKeys.expiresAt')}</span>
                      <p>{formatDate(selectedKey.expires_at)}</p>
                    </div>
                  </div>
                </div>

                {/* Statistics */}
                {keyStats && (
                  <div>
                    <h4 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-3">
                      {t('apiKeys.statistics')}
                    </h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">{t('apiKeys.totalRequests')}</span>
                        <p className="font-medium">{formatNumber(keyStats.total_requests)}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">{t('apiKeys.successRate')}</span>
                        <p className="font-medium">{keyStats.success_rate.toFixed(1)}%</p>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">{t('apiKeys.avgResponseTime')}</span>
                        <p className="font-medium">{keyStats.average_response_time_ms.toFixed(0)}ms</p>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">{t('apiKeys.errorRequests')}</span>
                        <p className="font-medium">{formatNumber(keyStats.error_requests)}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Rate Limits */}
                <div>
                  <h4 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-3">
                    {t('apiKeys.rateLimits')}
                  </h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">{selectedKey.rate_limits.requests_per_minute}</p>
                      <p className="text-gray-500 dark:text-gray-400">{t('apiKeys.perMinute')}</p>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <p className="text-2xl font-bold text-green-600">{selectedKey.rate_limits.requests_per_hour}</p>
                      <p className="text-gray-500 dark:text-gray-400">{t('apiKeys.perHour')}</p>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <p className="text-2xl font-bold text-purple-600">{selectedKey.rate_limits.requests_per_day}</p>
                      <p className="text-gray-500 dark:text-gray-400">{t('apiKeys.perDay')}</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  )
}

export default APIKeyManager

