import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import Modal, { ModalBody, ModalFooter } from './Modal';
import Button from './Button';
import Input from './Input';
import { fadeUpVariants, staggerContainer, staggerItem } from '../../design-system/animations';
import { useToast } from '../../hooks/useToast';

export interface NotificationHistoryItem {
  id: string;
  message: string;
  channel: 'sms' | 'voice' | 'whatsapp' | 'push';
  status: 'delivered' | 'failed' | 'pending';
  created_at: string;
  sent_at?: string;
  delivered_at?: string;
  error_message?: string;
  stop?: {
    id: number;
    name: string;
    name_kannada?: string;
  };
  route?: {
    id: number;
    name: string;
    route_number: string;
  };
  subscription_id?: number;
  read?: boolean;
}

export interface NotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
  userId?: string;
  phoneNumber?: string;
}

type FilterType = 'all' | 'unread' | 'today' | 'thisWeek';
type StatusFilter = 'all' | 'delivered' | 'failed' | 'pending';

const NotificationCenter: React.FC<NotificationCenterProps> = ({
  isOpen,
  onClose,
  userId,
  phoneNumber,
}) => {
  const { t } = useTranslation();
  const { showToast } = useToast();
  
  const [notifications, setNotifications] = useState<NotificationHistoryItem[]>([]);
  const [filteredNotifications, setFilteredNotifications] = useState<NotificationHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [showPreferences, setShowPreferences] = useState(false);

  // Fetch notification history
  const fetchNotifications = async () => {
    if (!phoneNumber && !userId) return;
    
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (phoneNumber) params.append('phone', phoneNumber);
      if (userId) params.append('user_id', userId);
      params.append('limit', '50');
      
      const response = await fetch(`/api/v1/notifications/history?${params}`);
      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications || []);
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      showToast({
        type: 'error',
        message: t('notifications.fetchError'),
        duration: 4000,
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Filter notifications based on search and filters
  useEffect(() => {
    let filtered = notifications;

    // Apply search filter
    if (searchQuery.trim()) {
      filtered = filtered.filter(notification =>
        notification.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
        notification.stop?.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        notification.route?.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply time filter
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const thisWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

    switch (filterType) {
      case 'unread':
        filtered = filtered.filter(n => !n.read);
        break;
      case 'today':
        filtered = filtered.filter(n => new Date(n.created_at) >= today);
        break;
      case 'thisWeek':
        filtered = filtered.filter(n => new Date(n.created_at) >= thisWeek);
        break;
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(n => n.status === statusFilter);
    }

    // Sort by creation date (newest first)
    filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    setFilteredNotifications(filtered);
  }, [notifications, searchQuery, filterType, statusFilter]);

  // Fetch notifications when modal opens
  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen, phoneNumber, userId]);

  // Mark notification as read
  const markAsRead = async (notificationId: string) => {
    try {
      await fetch(`/api/v1/notifications/${notificationId}/read`, {
        method: 'POST',
      });
      
      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  // Mark all notifications as read
  const markAllAsRead = async () => {
    try {
      const params = new URLSearchParams();
      if (phoneNumber) params.append('phone', phoneNumber);
      if (userId) params.append('user_id', userId);
      
      await fetch(`/api/v1/notifications/mark-all-read?${params}`, {
        method: 'POST',
      });
      
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      showToast({
        type: 'success',
        message: t('notifications.allMarkedRead'),
        duration: 3000,
      });
    } catch (error) {
      console.error('Failed to mark all as read:', error);
      showToast({
        type: 'error',
        message: t('notifications.markReadError'),
        duration: 4000,
      });
    }
  };

  // Clear notification history
  const clearHistory = async () => {
    if (!confirm(t('notifications.confirmClearHistory'))) return;
    
    try {
      const params = new URLSearchParams();
      if (phoneNumber) params.append('phone', phoneNumber);
      if (userId) params.append('user_id', userId);
      
      await fetch(`/api/v1/notifications/clear-history?${params}`, {
        method: 'DELETE',
      });
      
      setNotifications([]);
      showToast({
        type: 'success',
        message: t('notifications.historyCleared'),
        duration: 3000,
      });
    } catch (error) {
      console.error('Failed to clear history:', error);
      showToast({
        type: 'error',
        message: t('notifications.clearHistoryError'),
        duration: 4000,
      });
    }
  };

  // Get status icon and color
  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'delivered':
        return {
          icon: '✓',
          color: 'text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/30',
          label: t('notifications.delivered')
        };
      case 'failed':
        return {
          icon: '✗',
          color: 'text-error-600 bg-error-100 dark:text-error-400 dark:bg-error-900/30',
          label: t('notifications.failed')
        };
      case 'pending':
        return {
          icon: '⏳',
          color: 'text-warning-600 bg-warning-100 dark:text-warning-400 dark:bg-warning-900/30',
          label: t('notifications.pending')
        };
      default:
        return {
          icon: '?',
          color: 'text-neutral-600 bg-neutral-100 dark:text-neutral-400 dark:bg-neutral-900/30',
          label: status
        };
    }
  };

  // Get channel icon
  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'sms': return '📱';
      case 'voice': return '📞';
      case 'whatsapp': return '💬';
      case 'push': return '🔔';
      default: return '📨';
    }
  };

  // Format relative time
  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return t('notifications.justNow');
    if (diffMins < 60) return t('notifications.minutesAgo', { count: diffMins });
    if (diffHours < 24) return t('notifications.hoursAgo', { count: diffHours });
    if (diffDays < 7) return t('notifications.daysAgo', { count: diffDays });
    return date.toLocaleDateString();
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`${t('notifications.center')} ${unreadCount > 0 ? `(${unreadCount})` : ''}`}
      size="lg"
    >
      <ModalBody>
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-4"
        >
          {/* Controls */}
          <motion.div variants={staggerItem} className="space-y-4">
            {/* Search */}
            <Input
              placeholder={t('notifications.searchPlaceholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              }
            />

            {/* Filters */}
            <div className="flex flex-wrap gap-2">
              {/* Time filters */}
              {(['all', 'unread', 'today', 'thisWeek'] as FilterType[]).map((filter) => (
                <Button
                  key={filter}
                  variant={filterType === filter ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setFilterType(filter)}
                >
                  {t(`notifications.${filter}`)}
                </Button>
              ))}
              
              {/* Status filters */}
              {(['all', 'delivered', 'failed', 'pending'] as StatusFilter[]).map((status) => (
                <Button
                  key={status}
                  variant={statusFilter === status ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => setStatusFilter(status)}
                >
                  {t(`notifications.${status}`)}
                </Button>
              ))}
            </div>

            {/* Action buttons */}
            <div className="flex justify-between items-center">
              <div className="flex gap-2">
                {unreadCount > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={markAllAsRead}
                  >
                    {t('notifications.markAllRead')}
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowPreferences(!showPreferences)}
                >
                  {t('notifications.preferences')}
                </Button>
              </div>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={clearHistory}
                disabled={notifications.length === 0}
              >
                {t('notifications.clearHistory')}
              </Button>
            </div>
          </motion.div>

          {/* Notification List */}
          <motion.div variants={staggerItem}>
            <AnimatePresence mode="wait">
              {isLoading ? (
                <motion.div
                  key="loading"
                  variants={fadeUpVariants}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                  className="text-center py-8"
                >
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-2">
                    {t('common.loading')}
                  </p>
                </motion.div>
              ) : filteredNotifications.length === 0 ? (
                <motion.div
                  key="empty"
                  variants={fadeUpVariants}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                  className="text-center py-8"
                >
                  <svg className="w-12 h-12 text-neutral-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM9 17H4l5 5v-5zM12 3v18" />
                  </svg>
                  <p className="text-neutral-600 dark:text-neutral-400">
                    {searchQuery || filterType !== 'all' || statusFilter !== 'all' 
                      ? t('notifications.noMatchingNotifications')
                      : t('notifications.noNotifications')
                    }
                  </p>
                </motion.div>
              ) : (
                <motion.div
                  key="notifications"
                  variants={staggerContainer}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                  className="space-y-3 max-h-96 overflow-y-auto"
                >
                  {filteredNotifications.map((notification, index) => {
                    const statusDisplay = getStatusDisplay(notification.status);
                    
                    return (
                      <motion.div
                        key={notification.id}
                        variants={staggerItem}
                        className={`
                          p-4 rounded-lg border transition-all duration-200 cursor-pointer
                          ${!notification.read 
                            ? 'bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800' 
                            : 'bg-neutral-50 dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700'
                          }
                          hover:shadow-md
                        `}
                        onClick={() => !notification.read && markAsRead(notification.id)}
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.99 }}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-lg">{getChannelIcon(notification.channel)}</span>
                              <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${statusDisplay.color}`}>
                                {statusDisplay.icon} {statusDisplay.label}
                              </span>
                              {!notification.read && (
                                <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
                              )}
                            </div>
                            
                            <p className="text-sm text-neutral-900 dark:text-neutral-100 mb-2">
                              {notification.message}
                            </p>
                            
                            {(notification.stop || notification.route) && (
                              <div className="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
                                {notification.stop && (
                                  <span>{notification.stop.name}</span>
                                )}
                                {notification.route && (
                                  <span className="ml-2">
                                    {t('stop.route')}: {notification.route.route_number}
                                  </span>
                                )}
                              </div>
                            )}
                            
                            {notification.error_message && (
                              <p className="text-xs text-error-600 dark:text-error-400 mt-1">
                                {notification.error_message}
                              </p>
                            )}
                          </div>
                          
                          <div className="text-right text-xs text-neutral-500 dark:text-neutral-400 ml-4">
                            <div>{formatRelativeTime(notification.created_at)}</div>
                            {notification.delivered_at && (
                              <div className="mt-1">
                                {t('notifications.deliveredAt')}: {new Date(notification.delivered_at).toLocaleTimeString()}
                              </div>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </motion.div>
      </ModalBody>

      <ModalFooter>
        <Button variant="ghost" onClick={onClose}>
          {t('common.close')}
        </Button>
        <Button onClick={fetchNotifications} disabled={isLoading}>
          {t('common.refresh')}
        </Button>
      </ModalFooter>
    </Modal>
  );
};

export default NotificationCenter;