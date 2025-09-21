import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import Modal, { ModalBody, ModalFooter } from './Modal';
import Button from './Button';
import Input from './Input';
import { useToast } from '../../hooks/useToast';

export interface SubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  stopId?: number;
  stopName?: string;
  stopNameKannada?: string;
}

interface SubscriptionFormData {
  phone: string;
  channel: 'sms' | 'voice' | 'whatsapp' | 'push';
  etaThreshold: number;
}

const SubscriptionModal: React.FC<SubscriptionModalProps> = ({
  isOpen,
  onClose,
  stopId,
  stopName,
  stopNameKannada,
}) => {
  const { t } = useTranslation();
  const { showToast } = useToast();
  
  const [formData, setFormData] = useState<SubscriptionFormData>({
    phone: '',
    channel: 'sms',
    etaThreshold: 5,
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Partial<SubscriptionFormData>>({});
  const [showSuccess, setShowSuccess] = useState(false);

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData({
        phone: '',
        channel: 'sms',
        etaThreshold: 5,
      });
      setErrors({});
      setShowSuccess(false);
    }
  }, [isOpen]);

  const validatePhone = (phone: string): boolean => {
    // Indian phone number validation
    const phoneRegex = /^(\+91|91)?[6-9]\d{9}$/;
    return phoneRegex.test(phone.replace(/\s+/g, ''));
  };

  const formatPhoneNumber = (phone: string): string => {
    // Remove all non-digits
    const digits = phone.replace(/\D/g, '');
    
    // Add +91 prefix if not present
    if (digits.length === 10 && digits.startsWith('6789'.charAt(0))) {
      return `+91${digits}`;
    } else if (digits.length === 12 && digits.startsWith('91')) {
      return `+${digits}`;
    } else if (digits.length === 13 && digits.startsWith('91')) {
      return `+${digits}`;
    }
    
    return phone;
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setFormData(prev => ({ ...prev, phone: value }));
    
    // Clear phone error when user starts typing
    if (errors.phone) {
      setErrors(prev => ({ ...prev, phone: undefined }));
    }
  };

  const handleChannelChange = (channel: SubscriptionFormData['channel']) => {
    setFormData(prev => ({ ...prev, channel }));
  };

  const handleEtaThresholdChange = (threshold: number) => {
    setFormData(prev => ({ ...prev, etaThreshold: threshold }));
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<SubscriptionFormData> = {};
    
    if (!formData.phone.trim()) {
      newErrors.phone = t('notifications.phoneRequired');
    } else if (!validatePhone(formData.phone)) {
      newErrors.phone = t('notifications.phoneInvalid');
    }
    
    if (formData.etaThreshold < 1 || formData.etaThreshold > 30) {
      newErrors.etaThreshold = t('notifications.etaThresholdInvalid');
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm() || !stopId) return;
    
    setIsSubmitting(true);
    
    try {
      const formattedPhone = formatPhoneNumber(formData.phone);
      
      const response = await fetch('/api/v1/subscriptions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone: formattedPhone,
          stop_id: stopId,
          channel: formData.channel,
          eta_threshold: formData.etaThreshold,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to create subscription');
      }
      
      const result = await response.json();
      
      // Show success animation
      setShowSuccess(true);
      
      // Show success toast
      showToast({
        type: 'success',
        message: t('notifications.success'),
        duration: 4000,
      });
      
      // Close modal after animation
      setTimeout(() => {
        onClose();
      }, 2000);
      
    } catch (error) {
      console.error('Subscription error:', error);
      showToast({
        type: 'error',
        message: t('notifications.error'),
        duration: 4000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const channelOptions = [
    { value: 'sms', label: t('notifications.sms'), icon: '📱' },
    { value: 'voice', label: t('notifications.voice'), icon: '📞' },
    { value: 'whatsapp', label: t('notifications.whatsapp'), icon: '💬' },
    { value: 'push', label: t('notifications.push'), icon: '🔔' },
  ] as const;

  const etaOptions = [1, 2, 5, 10, 15, 20];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t('notifications.subscribe')}
      size="md"
    >
      <AnimatePresence mode="wait">
        {showSuccess ? (
          <ModalBody>
            <motion.div
              className="text-center py-8"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.5 }}
            >
              <motion.div
                className="w-16 h-16 mx-auto mb-4 bg-success-100 dark:bg-success-900/20 rounded-full flex items-center justify-center"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
              >
                <motion.svg
                  className="w-8 h-8 text-success-600 dark:text-success-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ delay: 0.5, duration: 0.5 }}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </motion.svg>
              </motion.div>
              
              <motion.h3
                className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                {t('notifications.success')}
              </motion.h3>
              
              <motion.p
                className="text-neutral-600 dark:text-neutral-400"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                {t('notifications.subscriptionCreated')}
              </motion.p>
            </motion.div>
          </ModalBody>
        ) : (
          <form onSubmit={handleSubmit}>
            <ModalBody>
              <motion.div
                className="space-y-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                {/* Stop Information */}
                {stopName && (
                  <motion.div
                    className="p-4 bg-primary-50 dark:bg-primary-900/20 rounded-lg"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 }}
                  >
                    <h4 className="font-medium text-primary-900 dark:text-primary-100 mb-1">
                      {stopName}
                    </h4>
                    {stopNameKannada && (
                      <p className="text-sm text-primary-700 dark:text-primary-300">
                        {stopNameKannada}
                      </p>
                    )}
                  </motion.div>
                )}

                {/* Phone Number Input */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <Input
                    label={t('notifications.phoneNumber')}
                    type="tel"
                    value={formData.phone}
                    onChange={handlePhoneChange}
                    error={errors.phone}
                    placeholder="+91 98765 43210"
                    leftIcon={
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                      </svg>
                    }
                  />
                </motion.div>

                {/* Channel Selection */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
                    {t('notifications.channel')}
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {channelOptions.map((option, index) => (
                      <motion.button
                        key={option.value}
                        type="button"
                        className={`
                          p-4 rounded-lg border-2 transition-all duration-200
                          ${formData.channel === option.value
                            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                            : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-300 dark:hover:border-neutral-600'
                          }
                        `}
                        onClick={() => handleChannelChange(option.value)}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.3 + index * 0.1 }}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <div className="text-2xl mb-2">{option.icon}</div>
                        <div className={`text-sm font-medium ${
                          formData.channel === option.value
                            ? 'text-primary-700 dark:text-primary-300'
                            : 'text-neutral-700 dark:text-neutral-300'
                        }`}>
                          {option.label}
                        </div>
                      </motion.button>
                    ))}
                  </div>
                </motion.div>

                {/* ETA Threshold */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 }}
                >
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
                    {t('notifications.etaThreshold')}
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {etaOptions.map((minutes, index) => (
                      <motion.button
                        key={minutes}
                        type="button"
                        className={`
                          px-4 py-2 rounded-lg border transition-all duration-200
                          ${formData.etaThreshold === minutes
                            ? 'border-primary-500 bg-primary-500 text-white'
                            : 'border-neutral-300 dark:border-neutral-600 text-neutral-700 dark:text-neutral-300 hover:border-primary-300'
                          }
                        `}
                        onClick={() => handleEtaThresholdChange(minutes)}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.4 + index * 0.05 }}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        {minutes} {t('map.minutes')}
                      </motion.button>
                    ))}
                  </div>
                  {errors.etaThreshold && (
                    <motion.p
                      className="mt-2 text-sm text-error-600 dark:text-error-400"
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      {errors.etaThreshold}
                    </motion.p>
                  )}
                </motion.div>
              </motion.div>
            </ModalBody>

            <ModalFooter>
              <Button
                variant="ghost"
                onClick={onClose}
                disabled={isSubmitting}
              >
                {t('common.cancel')}
              </Button>
              <Button
                type="submit"
                loading={isSubmitting}
                disabled={!formData.phone || !stopId}
              >
                {t('notifications.subscribe')}
              </Button>
            </ModalFooter>
          </form>
        )}
      </AnimatePresence>
    </Modal>
  );
};

export default SubscriptionModal;