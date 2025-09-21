import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import Card, { CardHeader, CardContent } from './Card';
import Button from './Button';
import { fadeUpVariants, scaleVariants, pulseVariants } from '../../design-system/animations';
import { useBusRealTime, BusLocationUpdate } from '../../hooks/useBusRealTime';

// Types for bus data
export interface BusLocation {
    latitude: number;
    longitude: number;
    speed: number;
    bearing: number;
    recorded_at: string;
    age_minutes: number;
    is_recent?: boolean;
}

export interface BusTrip {
    id: number;
    route_id: number;
    route_name: string;
    route_number: string;
    start_time: string;
    driver_id: number;
}

export interface BusOccupancy {
    level: 'low' | 'medium' | 'high';
    percentage: number;
    passenger_count: number;
    last_updated?: string;
}

export interface BusETA {
    seconds: number;
    minutes: number;
    formatted: string;
    arrival_time: string;
    confidence?: {
        score: number;
        factors: string[];
    };
}

export interface BusData {
    id: number;
    vehicle_number: string;
    capacity: number;
    status: 'active' | 'maintenance' | 'offline';
    current_location: BusLocation | null;
    current_trip: BusTrip | null;
    occupancy: BusOccupancy;
    eta?: BusETA;
    next_stops?: Array<{
        id: number;
        name: string;
        name_kannada?: string;
        eta: BusETA;
    }>;
}

export interface BusDetailCardProps {
    bus: BusData;
    onClose?: () => void;
    onSubscribe?: (busId: number) => void;
    onBusUpdate?: (updatedBus: BusData) => void;
    className?: string;
    showSubscribeButton?: boolean;
    compact?: boolean;
    enableRealTimeUpdates?: boolean;
}

const BusDetailCard: React.FC<BusDetailCardProps> = ({
    bus,
    onClose,
    onSubscribe,
    onBusUpdate,
    className = '',
    showSubscribeButton = true,
    compact = false,
    enableRealTimeUpdates = true
}) => {
    const { t, i18n } = useTranslation();
    const [etaCountdown, setEtaCountdown] = useState<number>(0);
    const [isSubscribed, setIsSubscribed] = useState(false);
    const [currentBus, setCurrentBus] = useState<BusData>(bus);

    // Real-time updates
    const handleLocationUpdate = (update: BusLocationUpdate) => {
        if (update.vehicle_id === currentBus.id) {
            const updatedBus: BusData = {
                ...currentBus,
                current_location: {
                    ...update.location,
                    is_recent: true
                },
                occupancy: update.occupancy || currentBus.occupancy
            };

            setCurrentBus(updatedBus);
            onBusUpdate?.(updatedBus);
        }
    };

    const { subscribeToBus, unsubscribeFromBus, isConnected } = useBusRealTime({
        busId: enableRealTimeUpdates ? bus.id : undefined,
        onLocationUpdate: handleLocationUpdate,
        autoConnect: enableRealTimeUpdates
    });

    // Update current bus when prop changes
    useEffect(() => {
        setCurrentBus(bus);
    }, [bus]);

    // Initialize ETA countdown
    useEffect(() => {
        if (currentBus.eta) {
            setEtaCountdown(currentBus.eta.seconds);
        }
    }, [currentBus.eta]);

    // ETA countdown timer
    useEffect(() => {
        if (etaCountdown <= 0) return;

        const timer = setInterval(() => {
            setEtaCountdown(prev => Math.max(0, prev - 1));
        }, 1000);

        return () => clearInterval(timer);
    }, [etaCountdown]);

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

    // Get status color
    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'active': return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30';
            case 'maintenance': return 'text-orange-600 bg-orange-100 dark:text-orange-400 dark:bg-orange-900/30';
            case 'offline': return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/30';
            default: return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/30';
        }
    };

    // Connection status indicator
    const getConnectionStatus = () => {
        if (!enableRealTimeUpdates) return null;

        return (
            <div className="flex items-center space-x-1 text-xs">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-neutral-500 dark:text-neutral-400">
                    {isConnected ? 'Live' : 'Offline'}
                </span>
            </div>
        );
    };

    const handleSubscribe = () => {
        if (onSubscribe) {
            onSubscribe(currentBus.id);
            setIsSubscribed(true);
        }
    };

    return (
        <motion.div
            className={`relative ${className}`}
            variants={fadeUpVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
        >
            <Card
                variant="elevated"
                padding={compact ? "sm" : "md"}
                interactive={false}
                className="w-full max-w-sm bg-white dark:bg-neutral-800 shadow-lg"
            >
                <CardHeader
                    title={
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                                <span className="text-lg font-bold text-bmtc-primary dark:text-blue-400">
                                    {currentBus.vehicle_number}
                                </span>
                                {getConnectionStatus()}
                            </div>
                            {onClose && (
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={onClose}
                                    className="p-1 h-8 w-8"
                                    aria-label={t('common.close')}
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </Button>
                            )}
                        </div>
                    }
                    subtitle={
                        currentBus.current_trip ? (
                            <div className="flex items-center space-x-2">
                                <span className="text-sm font-medium">
                                    {currentBus.current_trip.route_number}
                                </span>
                                <span className="text-xs text-neutral-500 dark:text-neutral-400">
                                    {i18n.language === 'kn' && currentBus.current_trip.route_name ?
                                        currentBus.current_trip.route_name : currentBus.current_trip.route_name}
                                </span>
                            </div>
                        ) : (
                            <span className="text-sm text-neutral-500 dark:text-neutral-400">
                                {t('bus.noActiveTrip')}
                            </span>
                        )
                    }
                />

                <CardContent>
                    <div className="space-y-4">
                        {/* ETA Section */}
                        {currentBus.eta && (
                            <motion.div
                                className="text-center p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg"
                                variants={scaleVariants}
                                initial="hidden"
                                animate="visible"
                            >
                                <div className="text-xs text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">
                                    {t('map.eta')}
                                </div>
                                <motion.div
                                    className="text-2xl font-bold text-bmtc-primary dark:text-blue-400"
                                    variants={etaCountdown <= 60 ? pulseVariants : {}}
                                    animate={etaCountdown <= 60 ? "animate" : ""}
                                >
                                    {formatCountdown(etaCountdown)}
                                </motion.div>
                                {currentBus.eta.confidence && (
                                    <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
                                        {t('bus.confidence')}: {Math.round(currentBus.eta.confidence.score * 100)}%
                                    </div>
                                )}
                            </motion.div>
                        )}

                        {/* Status and Occupancy */}
                        <div className="grid grid-cols-2 gap-3">
                            <motion.div
                                className="text-center"
                                variants={fadeUpVariants}
                                initial="hidden"
                                animate="visible"
                                transition={{ delay: 0.1 }}
                            >
                                <div className="text-xs text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">
                                    {t('bus.status')}
                                </div>
                                <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(currentBus.status)}`}>
                                    {t(`bus.${currentBus.status}`)}
                                </span>
                            </motion.div>

                            <motion.div
                                className="text-center"
                                variants={fadeUpVariants}
                                initial="hidden"
                                animate="visible"
                                transition={{ delay: 0.2 }}
                            >
                                <div className="text-xs text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">
                                    {t('bus.occupancy')}
                                </div>
                                <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getOccupancyColor(currentBus.occupancy.level)}`}>
                                    {currentBus.occupancy.percentage}%
                                </span>
                            </motion.div>
                        </div>

                        {/* Occupancy Bar */}
                        <motion.div
                            className="space-y-2"
                            variants={fadeUpVariants}
                            initial="hidden"
                            animate="visible"
                            transition={{ delay: 0.3 }}
                        >
                            <div className="flex justify-between text-xs text-neutral-600 dark:text-neutral-400">
                                <span>{currentBus.occupancy.passenger_count} {t('bus.passengers')}</span>
                                <span>{currentBus.capacity - currentBus.occupancy.passenger_count} {t('bus.seatsAvailable')}</span>
                            </div>
                            <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-2">
                                <motion.div
                                    className={`h-2 rounded-full ${currentBus.occupancy.level === 'low' ? 'bg-green-500' :
                                        currentBus.occupancy.level === 'medium' ? 'bg-yellow-500' : 'bg-red-500'
                                        }`}
                                    initial={{ width: 0 }}
                                    animate={{ width: `${currentBus.occupancy.percentage}%` }}
                                    transition={{ duration: 1, delay: 0.5 }}
                                />
                            </div>
                        </motion.div>

                        {/* Next Stops */}
                        {currentBus.next_stops && currentBus.next_stops.length > 0 && !compact && (
                            <motion.div
                                className="space-y-2"
                                variants={fadeUpVariants}
                                initial="hidden"
                                animate="visible"
                                transition={{ delay: 0.4 }}
                            >
                                <div className="text-xs text-neutral-600 dark:text-neutral-400 uppercase tracking-wide">
                                    {t('bus.nextStops')}
                                </div>
                                <div className="space-y-2 max-h-32 overflow-y-auto">
                                    {currentBus.next_stops.slice(0, 3).map((stop, index) => (
                                        <motion.div
                                            key={stop.id}
                                            className="flex justify-between items-center p-2 bg-neutral-50 dark:bg-neutral-700 rounded"
                                            variants={fadeUpVariants}
                                            initial="hidden"
                                            animate="visible"
                                            transition={{ delay: 0.5 + index * 0.1 }}
                                        >
                                            <div className="flex-1 min-w-0">
                                                <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
                                                    {i18n.language === 'kn' && stop.name_kannada ? stop.name_kannada : stop.name}
                                                </div>
                                            </div>
                                            <div className="text-xs text-neutral-500 dark:text-neutral-400 ml-2">
                                                {Math.round(stop.eta.minutes)} {t('map.minutes')}
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            </motion.div>
                        )}

                        {/* Location Info */}
                        {currentBus.current_location && (
                            <motion.div
                                className="text-xs text-neutral-500 dark:text-neutral-400 text-center"
                                variants={fadeUpVariants}
                                initial="hidden"
                                animate="visible"
                                transition={{ delay: 0.6 }}
                            >
                                {t('bus.lastUpdated')}: {Math.round(currentBus.current_location.age_minutes)} {t('bus.minutesAgo')}
                                {currentBus.current_location.speed > 0 && (
                                    <span className="ml-2">• {t('bus.speed')}: {Math.round(currentBus.current_location.speed)} km/h</span>
                                )}
                            </motion.div>
                        )}

                        {/* Subscribe Button */}
                        {showSubscribeButton && (
                            <motion.div
                                variants={fadeUpVariants}
                                initial="hidden"
                                animate="visible"
                                transition={{ delay: 0.7 }}
                            >
                                <Button
                                    variant={isSubscribed ? "outline" : "primary"}
                                    size="sm"
                                    onClick={handleSubscribe}
                                    disabled={isSubscribed}
                                    className="w-full"
                                >
                                    {isSubscribed ? t('notifications.unsubscribe') : t('notifications.subscribe')}
                                </Button>
                            </motion.div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
};

export default BusDetailCard;