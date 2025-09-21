import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useI18n } from '../../hooks/useI18n';
import { useConnectivity } from '../../hooks/useConnectivity';
import { Card, CardContent, CardHeader } from './Card';
import { Button } from './Button';

export interface LocationData {
  vehicleId: string;
  routeId: string;
  routeName: string;
  latitude: number;
  longitude: number;
  speed: number;
  bearing: number;
  timestamp: number;
  accuracy?: number;
  isRealTime: boolean;
}

interface LastKnownLocationProps {
  locations: LocationData[];
  onLocationClick?: (location: LocationData) => void;
  className?: string;
}

export function LastKnownLocation({ 
  locations, 
  onLocationClick,
  className = '' 
}: LastKnownLocationProps) {
  const [sortedLocations, setSortedLocations] = useState<LocationData[]>([]);
  const [showStaleOnly, setShowStaleOnly] = useState(false);
  
  const { t } = useI18n();
  const connectivity = useConnectivity();

  useEffect(() => {
    // Sort locations by timestamp (most recent first)
    const sorted = [...locations].sort((a, b) => b.timestamp - a.timestamp);
    setSortedLocations(sorted);
  }, [locations]);

  const getLocationAge = (timestamp: number) => {
    const now = Date.now();
    const ageMs = now - timestamp;
    const ageMinutes = Math.floor(ageMs / (1000 * 60));
    const ageHours = Math.floor(ageMs / (1000 * 60 * 60));
    const ageDays = Math.floor(ageMs / (1000 * 60 * 60 * 24));

    if (ageMinutes < 1) {
      return { text: t('common.justNow'), isStale: false, severity: 'fresh' };
    } else if (ageMinutes < 60) {
      return { 
        text: t('common.minutesAgo', { count: ageMinutes }), 
        isStale: ageMinutes > 5, 
        severity: ageMinutes > 15 ? 'stale' : ageMinutes > 5 ? 'aging' : 'fresh'
      };
    } else if (ageHours < 24) {
      return { 
        text: t('common.hoursAgo', { count: ageHours }), 
        isStale: true, 
        severity: 'stale'
      };
    } else {
      return { 
        text: t('common.daysAgo', { count: ageDays }), 
        isStale: true, 
        severity: 'very-stale'
      };
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'fresh':
        return 'text-green-600 dark:text-green-400';
      case 'aging':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'stale':
        return 'text-orange-600 dark:text-orange-400';
      case 'very-stale':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'fresh':
        return '🟢';
      case 'aging':
        return '🟡';
      case 'stale':
        return '🟠';
      case 'very-stale':
        return '🔴';
      default:
        return '⚪';
    }
  };

  const filteredLocations = showStaleOnly 
    ? sortedLocations.filter(loc => getLocationAge(loc.timestamp).isStale)
    : sortedLocations;

  const staleCount = sortedLocations.filter(loc => getLocationAge(loc.timestamp).isStale).length;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('offline.lastKnownLocations')}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {connectivity.isOffline && t('offline.dataStale')}
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          {staleCount > 0 && (
            <Button
              size="sm"
              variant={showStaleOnly ? 'primary' : 'outline'}
              onClick={() => setShowStaleOnly(!showStaleOnly)}
            >
              {showStaleOnly ? t('common.showAll') : t('offline.showStale')} ({staleCount})
            </Button>
          )}
        </div>
      </div>

      {/* Connection Status Banner */}
      {connectivity.isOffline && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-3 bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200 rounded-lg"
        >
          <div className="flex items-center space-x-2">
            <span>ℹ️</span>
            <span className="text-sm">
              {t('offline.refreshWhenOnline')}
            </span>
          </div>
        </motion.div>
      )}

      {/* Locations List */}
      <div className="space-y-3">
        <AnimatePresence>
          {filteredLocations.map((location) => {
            const ageInfo = getLocationAge(location.timestamp);
            
            return (
              <motion.div
                key={`${location.vehicleId}-${location.timestamp}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                layout
                className={`cursor-pointer ${onLocationClick ? 'hover:shadow-md' : ''}`}
                onClick={() => onLocationClick?.(location)}
              >
                <Card className={`transition-all ${
                  ageInfo.isStale ? 'opacity-75' : ''
                }`}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="font-semibold text-gray-900 dark:text-white">
                            {location.routeId}
                          </span>
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            Vehicle {location.vehicleId}
                          </span>
                          {!location.isRealTime && (
                            <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-xs rounded">
                              {t('offline.cached')}
                            </span>
                          )}
                        </div>
                        
                        <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                          {location.routeName}
                        </p>
                        
                        <div className="grid grid-cols-2 gap-4 text-xs text-gray-600 dark:text-gray-400">
                          <div>
                            <span className="font-medium">{t('common.location')}:</span>
                            <br />
                            {location.latitude.toFixed(6)}, {location.longitude.toFixed(6)}
                          </div>
                          <div>
                            <span className="font-medium">{t('bus.speed')}:</span>
                            <br />
                            {location.speed.toFixed(1)} km/h
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="flex items-center space-x-1 mb-1">
                          <span>{getSeverityIcon(ageInfo.severity)}</span>
                          <span className={`text-xs font-medium ${getSeverityColor(ageInfo.severity)}`}>
                            {ageInfo.text}
                          </span>
                        </div>
                        
                        <p className="text-xs text-gray-500">
                          {new Date(location.timestamp).toLocaleTimeString()}
                        </p>
                        
                        {location.accuracy && (
                          <p className="text-xs text-gray-500 mt-1">
                            ±{location.accuracy}m
                          </p>
                        )}
                      </div>
                    </div>
                    
                    {ageInfo.isStale && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="mt-3 p-2 bg-orange-50 dark:bg-orange-900/20 rounded text-xs text-orange-800 dark:text-orange-200"
                      >
                        <span>⚠️ {t('offline.dataStale')}</span>
                      </motion.div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Empty State */}
      {filteredLocations.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📍</div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {showStaleOnly ? t('offline.noStaleData') : t('offline.noLocationData')}
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            {connectivity.isOffline 
              ? t('offline.connectToGetFresh')
              : t('offline.waitingForData')
            }
          </p>
        </div>
      )}

      {/* Summary Stats */}
      {sortedLocations.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {sortedLocations.length}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">
              {t('offline.totalLocations')}
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {sortedLocations.filter(loc => !getLocationAge(loc.timestamp).isStale).length}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">
              {t('offline.fresh')}
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
              {staleCount}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">
              {t('offline.stale')}
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {sortedLocations.filter(loc => loc.isRealTime).length}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">
              {t('offline.realTime')}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default LastKnownLocation;