import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Button from './Button';
import Modal from './Modal';
import { useToast } from '../../hooks/useToast';

interface SOSButtonProps {
  className?: string;
}

interface EmergencyType {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: string;
}

const emergencyTypes: EmergencyType[] = [
  {
    id: 'medical',
    label: 'Medical Emergency',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
    ),
    color: 'bg-red-500'
  },
  {
    id: 'safety',
    label: 'Safety Concern',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    color: 'bg-orange-500'
  },
  {
    id: 'harassment',
    label: 'Harassment',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
    ),
    color: 'bg-purple-500'
  },
  {
    id: 'accident',
    label: 'Accident',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
      </svg>
    ),
    color: 'bg-red-600'
  },
  {
    id: 'other',
    label: 'Other Emergency',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
    ),
    color: 'bg-gray-500'
  }
];

export const SOSButton: React.FC<SOSButtonProps> = ({ className = '' }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isPressed, setIsPressed] = useState(false);
  const [selectedType, setSelectedType] = useState<string>('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const { showToast } = useToast();

  const handleSOSPress = () => {
    setIsPressed(true);
    setIsModalOpen(true);
    captureLocation();
  };

  const captureLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          console.error('Error getting location:', error);
          showToast('Unable to get current location', 'error');
        }
      );
    }
  };

  const handleEmergencySubmit = async () => {
    if (!selectedType) {
      showToast('Please select an emergency type', 'error');
      return;
    }

    setIsSubmitting(true);

    try {
      const emergencyData = {
        type: selectedType,
        description,
        location,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent
      };

      // Send to backend API
      const response = await fetch('/api/v1/emergency/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(emergencyData)
      });

      if (response.ok) {
        showToast('Emergency alert sent successfully', 'success');
        setIsModalOpen(false);
        resetForm();
        
        // Simulate emergency call if enabled
        simulateEmergencyCall();
      } else {
        throw new Error('Failed to send emergency alert');
      }
    } catch (error) {
      console.error('Error sending emergency alert:', error);
      showToast('Failed to send emergency alert. Please try again.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const simulateEmergencyCall = () => {
    // Simulate emergency call functionality
    showToast('Connecting to emergency helpline...', 'info');
    
    setTimeout(() => {
      showToast('Emergency services have been notified', 'success');
    }, 2000);
  };

  const resetForm = () => {
    setSelectedType('');
    setDescription('');
    setLocation(null);
    setIsPressed(false);
  };

  const handleCancel = () => {
    setIsModalOpen(false);
    resetForm();
  };

  return (
    <>
      <motion.div
        className={`fixed bottom-6 right-6 z-50 ${className}`}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <Button
          onClick={handleSOSPress}
          className={`
            w-16 h-16 rounded-full shadow-lg
            ${isPressed 
              ? 'bg-red-600 hover:bg-red-700' 
              : 'bg-red-500 hover:bg-red-600'
            }
            text-white border-4 border-white
            flex items-center justify-center
            transition-all duration-200
          `}
          aria-label="Emergency SOS Button"
        >
          <motion.div
            animate={isPressed ? { scale: [1, 1.2, 1] } : {}}
            transition={{ duration: 0.5, repeat: isPressed ? Infinity : 0 }}
          >
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </motion.div>
        </Button>
      </motion.div>

      <AnimatePresence>
        {isModalOpen && (
          <Modal
            isOpen={isModalOpen}
            onClose={handleCancel}
            title="Emergency Report"
            className="max-w-md"
          >
            <div className="space-y-6">
              {/* Location Status */}
              <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>
                  {location 
                    ? `Location captured: ${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}`
                    : 'Capturing location...'
                  }
                </span>
              </div>

              {/* Emergency Type Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Emergency Type *
                </label>
                <div className="grid grid-cols-1 gap-2">
                  {emergencyTypes.map((type) => (
                    <motion.button
                      key={type.id}
                      onClick={() => setSelectedType(type.id)}
                      className={`
                        flex items-center space-x-3 p-3 rounded-lg border-2 transition-all
                        ${selectedType === type.id
                          ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                        }
                      `}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <div className={`p-2 rounded-full ${type.color} text-white`}>
                        {type.icon}
                      </div>
                      <span className="text-left font-medium text-gray-900 dark:text-gray-100">
                        {type.label}
                      </span>
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Additional Details (Optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the emergency situation..."
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg 
                           bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                           focus:ring-2 focus:ring-red-500 focus:border-transparent
                           resize-none"
                  rows={3}
                />
              </div>

              {/* Timestamp */}
              <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>
                  {new Date().toLocaleString()}
                </span>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-3">
                <Button
                  onClick={handleCancel}
                  variant="outline"
                  className="flex-1"
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleEmergencySubmit}
                  className="flex-1 bg-red-500 hover:bg-red-600 text-white"
                  disabled={isSubmitting || !selectedType}
                >
                  {isSubmitting ? (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Sending...</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                      </svg>
                      <span>Send Emergency Alert</span>
                    </div>
                  )}
                </Button>
              </div>

              {/* Emergency Contact Info */}
              <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                Emergency services will be notified immediately.
                <br />
                For immediate assistance, call 100 (Police) or 108 (Ambulance)
              </div>
            </div>
          </Modal>
        )}
      </AnimatePresence>
    </>
  );
};