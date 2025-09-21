import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import Modal, { ModalBody, ModalFooter } from './Modal';
import Button from './Button';
import Input from './Input';
import { fadeUpVariants, staggerContainer, staggerItem } from '../../design-system/animations';
import { useToast } from '../../hooks/useToast';

export interface Subscription {
  id: number;
  phone: string;
  stop_id: number;
  channel: 'sms' | 'voice' | 'whatsapp' | 'push';
  eta_threshold: number;
  is_active: boolean;
  created_at: string;
  stop?: {
    id: number;
    name: string;
    name_kannada?: string;
    route_name?: string;
  };
}

export interface SubscriptionManagerProps {
  isOpen: boolean;
  onClose: () => void;
  phoneNumber?: string;
  userId?: string;
}

const SubscriptionManager: React.FC<SubscriptionManagerProps> = ({
  isOpen,
  onClose,
  phoneNumber,
  userId,
}) => {
  const { t } = useTranslation();
  const { showToast } = useToast();
  
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showConfirmDialog, setShowConfirmDialog] = useState<number | null>(null);

  // Fetch user subscriptions
  const fetchSubscriptions = async () => {
    if (!phoneNumber && !userId) return;
    
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (phoneNumber) params.append('phone', phoneNumber);
      if (userId) params.append('user_id', userId);
      
      const response = await fetch(`/api/v1/subscriptions?${params}`);
      if (response.ok) {
        const data = await response.json();
        setSubscriptions(data.subscriptions || []);
      }
    } catch (error) {
      console.error('Failed to fetch subscriptions:', error);
      showToast({
        type: 'error',
        message: t('notifications.fetchSubscriptionsError'),
        duration: 4000,
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle subscription active status
  const toggleSubscription = async (subscriptionId: number, isActive: boolean) => {
    try {
      const response = await fetch(`/api/v1/subscriptions/${subscriptionId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_active: isActive }),
      });
      
      if (response.ok) {
        setSubscriptions(prev =>
          prev.map(sub => 
            sub.id === subscriptionId ? { ...sub, is_active: isActive } : sub
          )
        );
        
        showToast({
          type: 'success',
          message: isActive 
            ? t('notifications.subscriptionEnabled') 
            : t('notifications.subscriptionDisabled'),
          duration: 3000,
        });
      }
    } catch (error) {
      console.error('Failed to toggle subscription:', error);
      showToast({
        type: 'error',
        message: t('notifications.toggleError'),
        duration: 4000,
      });
    }
  };

  // Delete subscription
  const deleteSubscription = async (subscriptionId: number) => {
    try {
      const response = await fetch(`/api/v1/subscriptions/${subscriptionId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        setSubscriptions(prev => prev.filter(sub => sub.id !== subscriptionId));
        setShowConfirmDialog(null);
        
        showToast({
          type: 'success',
          message: t('notifications.subscriptionDeleted'),
          duration: 3000,
        });
      }
    } catch (error) {
      console.error('Failed to delete subscription:', error);
      showToast({
        type: 'error',
        message: t('notifications.deleteError'),
        duration: 4000,
      });
    }
  };

  // Update subscription preferences
  const updateSubscription = async (subscriptionId: number, updates: Partial<Subscription>) => {
    try {
      const response = await fetch(`/api/v1/subscriptions/${subscriptionId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });
      
      if (response.ok) {
        setSubscriptions(prev =>
          prev.map(sub => 
            sub.id === subscriptionId ? { ...sub, ...updates } : sub
          )
        );
        
        showToast({
          type: 'success',
          message: t('notifications.subscriptionUpdated'),
          duration: 3000,
        });
      }
    } catch (error) {
      console.error('Failed to update subscription:', error);
      showToast({
        type: 'error',
        message: t('notifications.updateError'),
        duration: 4000,
      });
    }
  };

  // Filter subscriptions based on search
  const filteredSubscriptions = subscriptions.filter(subscription =>
    !searchQuery.trim() || 
    subscription.stop?.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    subscription.stop?.route_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Fetch subscriptions when modal opens
  useEffect(() => {
    if (isOpen) {
      fetchSubscriptions();
    }
  }, [isOpen, phoneNumber, userId]);

  // Get channel icon and label
  const getChannelDisplay = (channel: string) => {
    switch (channel) {
      case 'sms': return { icon: '📱', label: t('notifications.sms') };
      case 'voice': return { icon: '📞', label: t('notifications.voice') };
      case 'whatsapp': return { icon: '💬', label: t('notifications.whatsapp') };
      case 'push': return { icon: '🔔', label: t('notifications.push') };
      default: return { icon: '📨', label: channel };
    }
  };

  const activeSubscriptions = subscriptions.filter(sub => sub.is_active).length;

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title={`${t('notifications.manageSubscriptions')} (${activeSubscriptions})`}
        size="lg"
      >
        <ModalBody>
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-4"
          >
            {/* Search */}
            <motion.div variants={staggerItem}>
              <Input
                placeholder={t('notifications.searchSubscriptions')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                leftIcon={
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                }
              />
            </motion.div>

            {/* Subscriptions List */}
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
                ) : filteredSubscriptions.length === 0 ? (
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
                      {searchQuery 
                        ? t('notifications.noMatchingSubscriptions')
                        : t('notifications.noSubscriptions')
                      }
                    </p>
                  </motion.div>
                ) : (
                  <motion.div
                    key="subscriptions"
                    variants={staggerContainer}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                    className="space-y-3 max-h-96 overflow-y-auto"
                  >
                    {filteredSubscriptions.map((subscription, index) => {
                      const channelDisplay = getChannelDisplay(subscription.channel);
                      
                      return (
                        <motion.div
                          key={subscription.id}
                          variants={staggerItem}
                          className={`
                            p-4 rounded-lg border transition-all duration-200
                            ${subscription.is_active 
                              ? 'bg-white dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700' 
                              : 'bg-neutral-100 dark:bg-neutral-900 border-neutral-300 dark:border-neutral-600 opacity-60'
                            }
                          `}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="text-lg">{channelDisplay.icon}</span>
                                <span className="font-medium text-neutral-900 dark:text-neutral-100">
                                  {subscription.stop?.name}
                                </span>
                                {subscription.stop?.name_kannada && (
                                  <span className="text-sm text-neutral-600 dark:text-neutral-400">
                                    ({subscription.stop.name_kannada})
                                  </span>
                                )}
                              </div>
                              
                              <div className="text-sm text-neutral-600 dark:text-neutral-400 space-y-1">
                                <div>
                                  {t('notifications.channel')}: {channelDisplay.label}
                                </div>
                                <div>
                                  {t('notifications.etaThreshold')}: {subscription.eta_threshold} {t('map.minutes')}
                                </div>
                                {subscription.stop?.route_name && (
                                  <div>
                                    {t('stop.route')}: {subscription.stop.route_name}
                                  </div>
                                )}
                                <div>
                                  {t('notifications.createdAt')}: {new Date(subscription.created_at).toLocaleDateString()}
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex flex-col gap-2 ml-4">
                              {/* Toggle Active */}
                              <Button
                                variant={subscription.is_active ? 'success' : 'ghost'}
                                size="sm"
                                onClick={() => toggleSubscription(subscription.id, !subscription.is_active)}
                              >
                                {subscription.is_active ? t('notifications.active') : t('notifications.inactive')}
                              </Button>
                              
                              {/* Delete */}
                              <Button
                                variant="danger"
                                size="sm"
                                onClick={() => setShowConfirmDialog(subscription.id)}
                              >
                                {t('common.delete')}
                              </Button>
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
          <Button onClick={fetchSubscriptions} disabled={isLoading}>
            {t('common.refresh')}
          </Button>
        </ModalFooter>
      </Modal>

      {/* Confirmation Dialog */}
      <Modal
        isOpen={showConfirmDialog !== null}
        onClose={() => setShowConfirmDialog(null)}
        title={t('notifications.confirmDelete')}
        size="sm"
      >
        <ModalBody>
          <p className="text-neutral-700 dark:text-neutral-300">
            {t('notifications.confirmDeleteMessage')}
          </p>
        </ModalBody>
        <ModalFooter>
          <Button
            variant="ghost"
            onClick={() => setShowConfirmDialog(null)}
          >
            {t('common.cancel')}
          </Button>
          <Button
            variant="danger"
            onClick={() => showConfirmDialog && deleteSubscription(showConfirmDialog)}
          >
            {t('common.delete')}
          </Button>
        </ModalFooter>
      </Modal>
    </>
  );
};

export default SubscriptionManager;