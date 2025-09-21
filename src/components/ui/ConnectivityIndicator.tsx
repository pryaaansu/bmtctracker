import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useConnectivity } from '../../hooks/useConnectivity';
import { useI18n } from '../../hooks/useI18n';

interface ConnectivityIndicatorProps {
  className?: string;
  showDetails?: boolean;
}

export function ConnectivityIndicator({ 
  className = '', 
  showDetails = false 
}: ConnectivityIndicatorProps) {
  const connectivity = useConnectivity();
  const { t } = useI18n();

  const getConnectionIcon = () => {
    if (connectivity.isOffline) return '📡';
    
    switch (connectivity.effectiveType) {
      case 'slow-2g':
      case '2g':
        return '📶';
      case '3g':
        return '📶';
      case '4g':
        return '📶';
      default:
        return '📶';
    }
  };

  const getConnectionColor = () => {
    if (connectivity.isOffline) return 'text-red-500';
    
    switch (connectivity.effectiveType) {
      case 'slow-2g':
      case '2g':
        return 'text-orange-500';
      case '3g':
        return 'text-yellow-500';
      case '4g':
        return 'text-green-500';
      default:
        return 'text-blue-500';
    }
  };

  const getConnectionText = () => {
    if (connectivity.isOffline) return t('connectivity.offline');
    
    switch (connectivity.effectiveType) {
      case 'slow-2g':
        return t('connectivity.slow');
      case '2g':
        return t('connectivity.2g');
      case '3g':
        return t('connectivity.3g');
      case '4g':
        return t('connectivity.4g');
      default:
        return t('connectivity.online');
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={`flex items-center space-x-2 ${className}`}
      >
        <motion.span
          animate={{ 
            scale: connectivity.isOffline ? [1, 1.2, 1] : 1,
            rotate: connectivity.isOffline ? [0, 10, -10, 0] : 0
          }}
          transition={{ 
            duration: connectivity.isOffline ? 0.5 : 0,
            repeat: connectivity.isOffline ? Infinity : 0,
            repeatDelay: 2
          }}
          className={`text-lg ${getConnectionColor()}`}
        >
          {getConnectionIcon()}
        </motion.span>
        
        <div className="flex flex-col">
          <span className={`text-sm font-medium ${getConnectionColor()}`}>
            {getConnectionText()}
          </span>
          
          {showDetails && connectivity.isOnline && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="text-xs text-gray-500 dark:text-gray-400"
            >
              {connectivity.downlink && (
                <span>{connectivity.downlink.toFixed(1)} Mbps</span>
              )}
              {connectivity.rtt && (
                <span className="ml-2">{connectivity.rtt}ms</span>
              )}
            </motion.div>
          )}
        </div>
        
        {connectivity.isOffline && (
          <motion.div
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            className="px-2 py-1 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 text-xs rounded-full"
          >
            {t('connectivity.offlineMode')}
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}

// Offline banner component
export function OfflineBanner() {
  const connectivity = useConnectivity();
  const { t } = useI18n();

  return (
    <AnimatePresence>
      {connectivity.isOffline && (
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -50 }}
          className="fixed top-0 left-0 right-0 z-50 bg-orange-500 text-white px-4 py-2 text-center text-sm font-medium"
        >
          <div className="flex items-center justify-center space-x-2">
            <motion.span
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              ⚡
            </motion.span>
            <span>{t('connectivity.offlineBanner')}</span>
            <motion.span
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              📱
            </motion.span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Connection quality indicator
export function ConnectionQuality() {
  const connectivity = useConnectivity();
  const { t } = useI18n();

  if (connectivity.isOffline) return null;

  const getQualityBars = () => {
    switch (connectivity.effectiveType) {
      case 'slow-2g':
        return 1;
      case '2g':
        return 2;
      case '3g':
        return 3;
      case '4g':
        return 4;
      default:
        return 4;
    }
  };

  const qualityBars = getQualityBars();

  return (
    <div className="flex items-center space-x-1" title={getConnectionText()}>
      {[1, 2, 3, 4].map((bar) => (
        <motion.div
          key={bar}
          initial={{ scaleY: 0 }}
          animate={{ scaleY: bar <= qualityBars ? 1 : 0.3 }}
          transition={{ delay: bar * 0.1 }}
          className={`w-1 bg-current rounded-full ${
            bar <= qualityBars ? getConnectionColor() : 'text-gray-300'
          }`}
          style={{ height: `${bar * 3 + 2}px` }}
        />
      ))}
    </div>
  );
}