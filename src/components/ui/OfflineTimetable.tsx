import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useI18n } from '../../hooks/useI18n';
import { useConnectivity } from '../../hooks/useConnectivity';
import { Button } from './Button';
import { Card, CardContent, CardHeader } from './Card';
import { Modal } from './Modal';
import { Loading } from './Loading';
import {
  generateQRCode,
  generateTimetableData,
  storeTimetableOffline,
  getTimetableOffline,
  getAllTimetablesOffline,
  downloadTimetablePDF,
  clearExpiredTimetables,
  type TimetableData,
  type QRCodeData
} from '../../utils/qrCode';

interface OfflineTimetableProps {
  stopId?: string;
  className?: string;
}

export function OfflineTimetable({ stopId, className = '' }: OfflineTimetableProps) {
  const [timetables, setTimetables] = useState<TimetableData[]>([]);
  const [selectedTimetable, setSelectedTimetable] = useState<TimetableData | null>(null);
  const [qrCodeUrl, setQrCodeUrl] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [showQRModal, setShowQRModal] = useState(false);
  const [error, setError] = useState<string>('');
  
  const { t } = useI18n();
  const connectivity = useConnectivity();

  useEffect(() => {
    loadOfflineTimetables();
    clearExpiredTimetables();
  }, []);

  const loadOfflineTimetables = async () => {
    try {
      setIsLoading(true);
      const storedTimetables = await getAllTimetablesOffline();
      setTimetables(storedTimetables);
    } catch (err) {
      console.error('Failed to load offline timetables:', err);
      setError(t('offline.loadError'));
    } finally {
      setIsLoading(false);
    }
  };

  const downloadTimetable = async (targetStopId: string) => {
    try {
      setIsLoading(true);
      setError('');

      // Try to get from offline storage first
      let timetableData = await getTimetableOffline(targetStopId);
      
      // If not found offline and we're online, generate new data
      if (!timetableData && connectivity.isOnline) {
        timetableData = await generateTimetableData(targetStopId);
        await storeTimetableOffline(timetableData);
      }

      if (!timetableData) {
        throw new Error('Timetable data not available offline');
      }

      setTimetables(prev => {
        const existing = prev.find(t => t.stopId === targetStopId);
        if (existing) {
          return prev.map(t => t.stopId === targetStopId ? timetableData! : t);
        }
        return [...prev, timetableData!];
      });

    } catch (err) {
      console.error('Failed to download timetable:', err);
      setError(t('offline.downloadError'));
    } finally {
      setIsLoading(false);
    }
  };

  const generateQRCodeForStop = async (timetable: TimetableData) => {
    try {
      setIsLoading(true);
      
      const qrData: QRCodeData = {
        stopId: timetable.stopId,
        stopName: timetable.stopName,
        routes: timetable.routes.map(r => r.routeId),
        location: { lat: 12.9716, lng: 77.5946 }, // Mock coordinates
        timestamp: Date.now(),
        version: '1.0'
      };

      const qrUrl = await generateQRCode(qrData, 300);
      setQrCodeUrl(qrUrl);
      setSelectedTimetable(timetable);
      setShowQRModal(true);
    } catch (err) {
      console.error('Failed to generate QR code:', err);
      setError(t('offline.qrError'));
    } finally {
      setIsLoading(false);
    }
  };

  const downloadPDF = async (timetable: TimetableData) => {
    try {
      await downloadTimetablePDF(timetable);
    } catch (err) {
      console.error('Failed to download PDF:', err);
      setError(t('offline.pdfError'));
    }
  };

  const formatLastUpdated = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (minutes < 60) {
      return t('offline.minutesAgo', { count: minutes });
    } else if (hours < 24) {
      return t('offline.hoursAgo', { count: hours });
    } else {
      return t('offline.daysAgo', { count: days });
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          {t('offline.title')}
        </h2>
        
        {stopId && (
          <Button
            onClick={() => downloadTimetable(stopId)}
            disabled={isLoading}
            className="flex items-center space-x-2"
          >
            <span>📥</span>
            <span>{t('offline.downloadTimetable')}</span>
          </Button>
        )}
      </div>

      {/* Connection Status */}
      <div className={`p-3 rounded-lg ${
        connectivity.isOnline 
          ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200'
          : 'bg-orange-50 dark:bg-orange-900/20 text-orange-800 dark:text-orange-200'
      }`}>
        <div className="flex items-center space-x-2">
          <span>{connectivity.isOnline ? '🟢' : '🟠'}</span>
          <span className="text-sm font-medium">
            {connectivity.isOnline ? t('connectivity.online') : t('connectivity.offline')}
          </span>
        </div>
        {connectivity.isOffline && (
          <p className="text-xs mt-1 opacity-80">
            {t('offline.cachedData')}
          </p>
        )}
      </div>

      {/* Error Message */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="p-3 bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 rounded-lg"
          >
            <div className="flex items-center space-x-2">
              <span>⚠️</span>
              <span className="text-sm">{error}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loading size="lg" />
        </div>
      )}

      {/* Timetables List */}
      <div className="space-y-3">
        <AnimatePresence>
          {timetables.map((timetable) => (
            <motion.div
              key={timetable.stopId}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              layout
            >
              <Card className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {timetable.stopName}
                      </h3>
                      {timetable.stopNameKannada && (
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {timetable.stopNameKannada}
                        </p>
                      )}
                      <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                        {t('offline.lastUpdated')}: {formatLastUpdated(timetable.lastUpdated)}
                      </p>
                    </div>
                    
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => generateQRCodeForStop(timetable)}
                        title={t('offline.qrCode')}
                      >
                        📱
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => downloadPDF(timetable)}
                        title="Download PDF"
                      >
                        📄
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent>
                  <div className="space-y-2">
                    {timetable.routes.map((route) => (
                      <div
                        key={route.routeId}
                        className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded"
                      >
                        <div>
                          <span className="font-medium text-sm">
                            {route.routeId}
                          </span>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            {route.direction}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-gray-500">
                            Every {route.frequency} min
                          </p>
                          <p className="text-xs text-gray-500">
                            {route.operatingHours.start} - {route.operatingHours.end}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {connectivity.isOffline && (
                    <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-xs text-blue-800 dark:text-blue-200">
                      <span>ℹ️ {t('offline.syncWhenOnline')}</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Empty State */}
      {!isLoading && timetables.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📅</div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {t('offline.noTimetables')}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {connectivity.isOnline 
              ? t('offline.downloadToGetStarted')
              : t('offline.connectToDownload')
            }
          </p>
        </div>
      )}

      {/* QR Code Modal */}
      <Modal
        isOpen={showQRModal}
        onClose={() => setShowQRModal(false)}
        title={`${t('offline.qrCode')} - ${selectedTimetable?.stopName}`}
      >
        <div className="text-center space-y-4">
          {qrCodeUrl && (
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="flex justify-center"
            >
              <img
                src={qrCodeUrl}
                alt="QR Code"
                className="border rounded-lg shadow-sm"
              />
            </motion.div>
          )}
          
          <div className="text-sm text-gray-600 dark:text-gray-400">
            <p>{t('offline.qrCodeInstructions')}</p>
            <p className="mt-2 font-mono text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded">
              bmtc://stop/{selectedTimetable?.stopId}
            </p>
          </div>
          
          <div className="flex space-x-3 justify-center">
            <Button
              variant="outline"
              onClick={() => {
                if (qrCodeUrl) {
                  const link = document.createElement('a');
                  link.href = qrCodeUrl;
                  link.download = `qr-${selectedTimetable?.stopId}.png`;
                  link.click();
                }
              }}
            >
              💾 {t('common.download')}
            </Button>
            <Button onClick={() => setShowQRModal(false)}>
              {t('common.close')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

export default OfflineTimetable;