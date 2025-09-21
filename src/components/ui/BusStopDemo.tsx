import React, { useState } from 'react';
import { motion } from 'framer-motion';
import BusDetailCard, { BusData } from './BusDetailCard';
import StopDetailModal, { StopData } from './StopDetailModal';
import Button from './Button';
import { fadeUpVariants, staggerContainer, staggerItem } from '../../design-system/animations';

// Mock data for demonstration
const mockBusData: BusData = {
  id: 1,
  vehicle_number: "KA-01-HB-1234",
  capacity: 40,
  status: "active",
  current_location: {
    latitude: 12.9716,
    longitude: 77.5946,
    speed: 25,
    bearing: 45,
    recorded_at: new Date().toISOString(),
    age_minutes: 2,
    is_recent: true
  },
  current_trip: {
    id: 1,
    route_id: 1,
    route_name: "Majestic to Electronic City",
    route_number: "335E",
    start_time: new Date().toISOString(),
    driver_id: 1
  },
  occupancy: {
    level: "medium",
    percentage: 65,
    passenger_count: 26
  },
  eta: {
    seconds: 420,
    minutes: 7,
    formatted: "7m 0s",
    arrival_time: new Date(Date.now() + 420000).toISOString(),
    confidence: {
      score: 0.85,
      factors: ["Real-time GPS", "Traffic data"]
    }
  },
  next_stops: [
    {
      id: 1,
      name: "Silk Board Junction",
      name_kannada: "ಸಿಲ್ಕ್ ಬೋರ್ಡ್ ಜಂಕ್ಷನ್",
      eta: {
        seconds: 420,
        minutes: 7,
        formatted: "7m 0s",
        arrival_time: new Date(Date.now() + 420000).toISOString()
      }
    },
    {
      id: 2,
      name: "BTM Layout",
      name_kannada: "ಬಿಟಿಎಂ ಲೇಔಟ್",
      eta: {
        seconds: 720,
        minutes: 12,
        formatted: "12m 0s",
        arrival_time: new Date(Date.now() + 720000).toISOString()
      }
    }
  ]
};

const mockStopData: StopData = {
  id: 1,
  name: "Silk Board Junction",
  name_kannada: "ಸಿಲ್ಕ್ ಬೋರ್ಡ್ ಜಂಕ್ಷನ್",
  latitude: 12.9165,
  longitude: 77.6224,
  route_id: 1,
  route_name: "Majestic to Electronic City",
  arrivals: [
    {
      vehicle_id: 1,
      vehicle_number: "KA-01-HB-1234",
      route_name: "Majestic to Electronic City",
      route_number: "335E",
      eta: {
        seconds: 420,
        minutes: 7,
        formatted: "7m 0s",
        arrival_time: new Date(Date.now() + 420000).toISOString()
      },
      occupancy: {
        level: "medium",
        percentage: 65
      },
      distance_meters: 2500,
      calculation_method: "gps_based",
      calculated_at: new Date().toISOString()
    },
    {
      vehicle_id: 2,
      vehicle_number: "KA-01-HB-5678",
      route_name: "Majestic to Electronic City",
      route_number: "335E",
      eta: {
        seconds: 900,
        minutes: 15,
        formatted: "15m 0s",
        arrival_time: new Date(Date.now() + 900000).toISOString()
      },
      occupancy: {
        level: "low",
        percentage: 30
      },
      distance_meters: 5200,
      calculation_method: "gps_based",
      calculated_at: new Date().toISOString()
    }
  ]
};

const BusStopDemo: React.FC = () => {
  const [showStopModal, setShowStopModal] = useState(false);
  const [showBusCard, setShowBusCard] = useState(false);

  const handleSubscribe = (busId: number) => {
    console.log('Subscribe to bus:', busId);
    // Here you would typically open a subscription modal
    alert(`Subscription requested for bus ${busId}`);
  };

  const handleStopSubscribe = (stopId: number, busId?: number) => {
    console.log('Subscribe to stop:', stopId, 'for bus:', busId);
    // Here you would typically open a subscription modal
    alert(`Subscription requested for stop ${stopId}${busId ? ` and bus ${busId}` : ''}`);
  };

  const handleToggleFavorite = (stopId: number) => {
    console.log('Toggle favorite for stop:', stopId);
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="p-6 space-y-6 max-w-4xl mx-auto"
    >
      <motion.div variants={staggerItem}>
        <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-4">
          Bus and Stop Detail Components Demo
        </h1>
        <p className="text-neutral-600 dark:text-neutral-400 mb-6">
          This demo showcases the BusDetailCard and StopDetailModal components with real-time updates and animations.
        </p>
      </motion.div>

      <motion.div variants={staggerItem} className="flex flex-wrap gap-4">
        <Button
          variant="primary"
          onClick={() => setShowBusCard(!showBusCard)}
        >
          {showBusCard ? 'Hide' : 'Show'} Bus Detail Card
        </Button>
        <Button
          variant="outline"
          onClick={() => setShowStopModal(true)}
        >
          Show Stop Detail Modal
        </Button>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bus Detail Card Demo */}
        <motion.div variants={staggerItem}>
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Bus Detail Card
          </h2>
          <div className="bg-neutral-100 dark:bg-neutral-800 rounded-lg p-4 min-h-[400px] flex items-center justify-center">
            {showBusCard ? (
              <BusDetailCard
                bus={mockBusData}
                onClose={() => setShowBusCard(false)}
                onSubscribe={handleSubscribe}
                enableRealTimeUpdates={false} // Disable for demo
              />
            ) : (
              <div className="text-center text-neutral-500 dark:text-neutral-400">
                <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                        d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m-6 3l6-3" />
                </svg>
                <p>Click "Show Bus Detail Card" to see the component</p>
              </div>
            )}
          </div>
        </motion.div>

        {/* Features List */}
        <motion.div variants={staggerItem}>
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Features
          </h2>
          <div className="space-y-4">
            <div className="bg-white dark:bg-neutral-800 rounded-lg p-4 shadow-sm">
              <h3 className="font-semibold text-green-600 dark:text-green-400 mb-2">
                ✅ Bus Detail Card
              </h3>
              <ul className="text-sm text-neutral-600 dark:text-neutral-400 space-y-1">
                <li>• Real-time ETA countdown with animations</li>
                <li>• Live occupancy display with progress bar</li>
                <li>• WebSocket integration for updates</li>
                <li>• Bilingual support (English/Kannada)</li>
                <li>• Smooth animations and micro-interactions</li>
                <li>• Connection status indicator</li>
              </ul>
            </div>

            <div className="bg-white dark:bg-neutral-800 rounded-lg p-4 shadow-sm">
              <h3 className="font-semibold text-green-600 dark:text-green-400 mb-2">
                ✅ Stop Detail Modal
              </h3>
              <ul className="text-sm text-neutral-600 dark:text-neutral-400 space-y-1">
                <li>• Multiple bus arrivals with countdowns</li>
                <li>• Favorite stops with localStorage</li>
                <li>• Real-time arrival updates</li>
                <li>• Individual bus subscription buttons</li>
                <li>• Auto-refresh every 30 seconds</li>
                <li>• Responsive modal design</li>
              </ul>
            </div>

            <div className="bg-white dark:bg-neutral-800 rounded-lg p-4 shadow-sm">
              <h3 className="font-semibold text-blue-600 dark:text-blue-400 mb-2">
                🔄 Real-time Features
              </h3>
              <ul className="text-sm text-neutral-600 dark:text-neutral-400 space-y-1">
                <li>• WebSocket connection management</li>
                <li>• Automatic reconnection with backoff</li>
                <li>• Live ETA updates and countdowns</li>
                <li>• Bus location tracking</li>
                <li>• Connection status indicators</li>
              </ul>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Stop Detail Modal */}
      <StopDetailModal
        stop={mockStopData}
        isOpen={showStopModal}
        onClose={() => setShowStopModal(false)}
        onSubscribe={handleStopSubscribe}
        onToggleFavorite={handleToggleFavorite}
        enableRealTimeUpdates={false} // Disable for demo
      />
    </motion.div>
  );
};

export default BusStopDemo;