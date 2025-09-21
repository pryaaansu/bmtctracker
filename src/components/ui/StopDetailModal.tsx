import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import Modal, { ModalBody } from './Modal';
import Button from './Button';
import Card, { CardHeader, CardContent } from './Card';
import SubscriptionModal from './SubscriptionModal';
import { fadeUpVariants, staggerContainer, staggerItem, pulseVariants } from '../../design-system/animations';
import { useBusRealTime } from '../../hooks/useBusRealTime';

// Types for stop data
export interface StopLocation {
  latitude: number;
  longitude: number;
}

export interface StopRoute {
  id: number;
  name: string;
  route_number: string;
  is_active: boolean;
}

export interface BusArrival {
  vehicle_id: number;
  vehicle_number: string;
  route_name: string;
  route_number: string;
  eta: {
    seconds: number;
    minutes: number;
    formatted: string;
    arrival_time: string;
  };
  occupancy: {
    level: 'low' | 'medium' | 'high';
    percentage: number;
  };
  distance_meters: number;
  calculation_method: string;
  calculated_at: string;
  confidence?: {
    score: number;
    factors: string[];
  };
}

export interface StopData {
  id: number;
  name: string;
  name_kannada?: string;
  latitude: number;
  longitude: number;
  route_id: number;
  route_name?: string;
  route?: StopRoute;
  arrivals?: BusArrival[];
  total_arrivals?: number;
  calculated_at?: string;
}

export interface StopDetailModalProps {
  stop: StopData | null;
  isOpen: boolean;
  onClose: () => void;
  onSubscribe?: (stopId: number, busId?: number) => void;
  onToggleFavorite?: (stopId: number) => void;
  className?: string;
  enableRealTimeUpdates?: boolean;
}

const StopDetailModal: React.FC<StopDetailModalProps> = ({
  stop,
  isOpen,
  onClose,
  onSubscribe,
  onToggleFavorite,
  className = '',
  enableRealTimeUpdates = true
}) => {
  const { t, i18n } = useTranslation();
  const [arrivals, setArrivals] = useState<BusArrival[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFavorite, setIsFavorite] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [etaCountdowns, setEtaCountdowns] = useState<{ [key: number]: number }>({});
  const [showSubscriptionModal, setShowSubscriptionModal] = useState(false);

  // Check if stop is in favorites (using localStorage)
  useEffect(() => {
    if (stop) {
      const favorites = JSON.parse(localStorage.getItem('favoriteStops') || '[]');
      setIsFavorite(favorites.includes(stop.id));
    }
  }, [stop]);

  // Initialize ETA countdowns
  useEffect(() => {
    if (arrivals.length > 0) {
      const countdowns: { [key: number]: number } = {};
      arrivals.forEach(arrival => {
        countdowns[arrival.vehicle_id] = arrival.eta.seconds;
      });
      setEtaCountdowns(countdowns);
    }
  }, [arrivals]);

  // ETA countdown timers
  useEffect(() => {
    const timers: NodeJS.Timeout[] = [];
    
    Object.keys(etaCountdowns).forEach(vehicleIdStr => {
      const vehicleId = parseInt(vehicleIdStr);
      if (etaCountdowns[vehicleId] > 0) {
        const timer = setInterval(() => {
          setEtaCountdowns(prev => ({
            ...prev,
            [vehicleId]: Math.max(0, prev[vehicleId] - 1)
          }));
        }, 1000);
        timers.push(timer);
      }
    });

    return () => {
      timers.forEach(timer => clearInterval(timer));
    };
  }, [etaCountdowns]);

  // Real-time updates for bus locations and ETAs
  const handleLocationUpdate = (update: any) => {
    // Update ETA for the specific bus if it's in our arrivals list
    setArrivals(prev => prev.map(arrival => {
      if (arrival.vehicle_id === update.vehicle_id && update.eta_updates) {
        const etaUpdate = update.eta_updates.find((eta: any) => eta.stop_id === stop?.id);
        if (etaUpdate) {
          return {
            ...arrival,
            eta: {
              ...arrival.eta,
              seconds: etaUpdate.eta_seconds,
              minutes: etaUpdate.eta_minutes
            }
          };
        }
      }
      return arrival;
    }));
  };

  const { subscribeToBus, unsubscribeFromBus } = useBusRealTime({
    onLocationUpdate: handleLocationUpdate,
    autoConnect: enableRealTimeUpdates && isOpen
  });

  // Subscribe to all buses when arrivals change
  useEffect(() => {
    if (enableRealTimeUpdates && arrivals.length > 0) {
      arrivals.forEach(arrival => {
        subscribeToBus(arrival.vehicle_id);
      });
    }

    return () => {
      if (enableRealTimeUpdates && arrivals.length > 0) {
        arrivals.forEach(arrival => {
          unsubscribeFromBus(arrival.vehicle_id);
        });
      }
    };
  }, [arrivals, enableRealTimeUpdates, subscribeToBus, unsubscribeFromBus]);

  // Fetch stop arrivals
  const fetchArrivals = async () => {
    if (!stop) return;

    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/stops/${stop.id}/arrivals?max_arrivals=10&max_eta_minutes=60`);
      if (response.ok) {
        const data = await response.json();
        setArrivals(data.arrivals || []);
        setLastUpdated(data.calculated_at || new Date().toISOString());
      }
    } catch (error) {
      console.error('Failed to fetch arrivals:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch arrivals when modal opens or stop changes
  useEffect(() => {
    if (isOpen && stop) {
      fetchArrivals();
      // Set up periodic refresh
      const interval = setInterval(fetchArrivals, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [isOpen, stop]);

  // Handle favorite toggle
  const handleToggleFavorite = () => {
    if (!stop) return;

    const favorites = JSON.parse(localStorage.getItem('favoriteStops') || '[]');
    let newFavorites;

    if (isFavorite) {
      newFavorites = favorites.filter((id: number) => id !== stop.id);
    } else {
      newFavorites = [...favorites, stop.id];
    }

    localStorage.setItem('favoriteStops', JSON.stringify(newFavorites));
    setIsFavorite(!isFavorite);
    onToggleFavorite?.(stop.id);
  };

  // Handle subscription
  const handleSubscribe = (busId?: number) => {
    setShowSubscriptionModal(true);
  };

  // Format countdown time
  const formatCountdown = (seconds: number): string => {
    if (seconds <= 0) return t('map.arriving');
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get occupancy color
  const getOccupancyColor = (level: string): string => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30';
      case 'medium': return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/30';
      case 'high': return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/30';
      default: return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/30';
    }
  };

  if (!stop) return null;

  const displayName = i18n.language === 'kn' && stop.name_kannada ? stop.name_kannada : stop.name;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      className={`max-w-md ${className}`}
      title={displayName}
    >
      <ModalBody>
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          exit="exit"
          className="space-y-4"
        >
          {/* Stop Header */}
          <motion.div variants={staggerItem} className="text-center">
            <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
              {displayName}
            </h2>
            {i18n.language !== 'kn' && stop.name_kannada && (
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                {stop.name_kannada}
              </p>
            )}
            {stop.route_name && (
              <p className="text-sm text-bmtc-primary dark:text-blue-400 mt-1">
                {t('stop.route')}: {stop.route_name}
              </p>
            )}
          </motion.div>

          {/* Action Buttons */}
          <motion.div variants={staggerItem} className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleToggleFavorite}
              className="flex-1"
            >
              <svg className={`w-4 h-4 mr-2 ${isFavorite ? 'fill-current text-yellow-500' : ''}`} 
                   fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
              {isFavorite ? t('stop.favorited') : t('stop.addToFavorites')}
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => handleSubscribe()}
              className="flex-1"
            >
              {t('notifications.subscribe')}
            </Button>
          </motion.div>

          {/* Arrivals Section */}
          <motion.div variants={staggerItem}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                {t('stop.upcomingArrivals')}
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={fetchArrivals}
                disabled={isLoading}
                className="p-2"
              >
                <svg className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} 
                     fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </Button>
            </div>

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
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-bmtc-primary mx-auto"></div>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-2">
                    {t('common.loading')}
                  </p>
                </motion.div>
              ) : arrivals.length === 0 ? (
                <motion.div
                  key="no-arrivals"
                  variants={fadeUpVariants}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                  className="text-center py-8"
                >
                  <svg className="w-12 h-12 text-neutral-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-neutral-600 dark:text-neutral-400">
                    {t('stop.noBusesArriving')}
                  </p>
                </motion.div>
              ) : (
                <motion.div
                  key="arrivals"
                  variants={staggerContainer}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                  className="space-y-3 max-h-64 overflow-y-auto"
                >
                  {arrivals.map((arrival, index) => (
                    <motion.div
                      key={arrival.vehicle_id}
                      variants={staggerItem}
                      className="bg-neutral-50 dark:bg-neutral-700 rounded-lg p-3"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold text-bmtc-primary dark:text-blue-400">
                              {arrival.vehicle_number}
                            </span>
                            <span className="text-xs text-neutral-500 dark:text-neutral-400">
                              {arrival.route_number}
                            </span>
                            <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getOccupancyColor(arrival.occupancy.level)}`}>
                              {arrival.occupancy.percentage}%
                            </span>
                          </div>
                          <div className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                            {Math.round(arrival.distance_meters / 1000 * 10) / 10} {t('stop.kmAway')}
                          </div>
                        </div>
                        <div className="text-right">
                          <motion.div
                            className="text-lg font-bold text-bmtc-primary dark:text-blue-400"
                            variants={etaCountdowns[arrival.vehicle_id] <= 60 ? pulseVariants : {}}
                            animate={etaCountdowns[arrival.vehicle_id] <= 60 ? "animate" : ""}
                          >
                            {formatCountdown(etaCountdowns[arrival.vehicle_id] || arrival.eta.seconds)}
                          </motion.div>
                          <Button
                            variant="ghost"
                            size="xs"
                            onClick={() => handleSubscribe(arrival.vehicle_id)}
                            className="text-xs mt-1"
                          >
                            {t('stop.notifyMe')}
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Last Updated */}
          {lastUpdated && (
            <motion.div variants={staggerItem} className="text-xs text-neutral-500 dark:text-neutral-400 text-center">
              {t('stop.lastUpdated')}: {new Date(lastUpdated).toLocaleTimeString()}
            </motion.div>
          )}
        </motion.div>
      </ModalBody>

      {/* Subscription Modal */}
      <SubscriptionModal
        isOpen={showSubscriptionModal}
        onClose={() => setShowSubscriptionModal(false)}
        stopId={stop.id}
        stopName={stop.name}
        stopNameKannada={stop.name_kannada}
      />
    </Modal>
  );
};

export default StopDetailModal;