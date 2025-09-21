import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapContainer, TileLayer, Marker, Polyline, useMapEvents } from 'react-leaflet';
import { LatLng, Icon } from 'leaflet';
import { Button } from './Button';
import { Input } from './Input';
import { Modal } from './Modal';
import { Card } from './Card';
import { Toast } from './Toast';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../hooks/useI18n';

interface RouteStop {
  id?: number;
  name: string;
  name_kannada?: string;
  latitude: number;
  longitude: number;
  stop_order: number;
}

interface Route {
  id?: number;
  name: string;
  route_number: string;
  geojson: string;
  polyline: string;
  stops: RouteStop[];
  is_active: boolean;
}

interface RouteManagerProps {
  isOpen: boolean;
  onClose: () => void;
  editingRoute?: Route | null;
  onRouteCreated?: (route: Route) => void;
  onRouteUpdated?: (route: Route) => void;
}

// Custom map component for handling clicks
const MapClickHandler: React.FC<{
  onMapClick: (latlng: LatLng) => void;
  isAddingStop: boolean;
}> = ({ onMapClick, isAddingStop }) => {
  useMapEvents({
    click: (e) => {
      if (isAddingStop) {
        onMapClick(e.latlng);
      }
    },
  });
  return null;
};

// Custom icons for different stop states
const createStopIcon = (order: number, isSelected: boolean = false) => {
  const color = isSelected ? '#ef4444' : '#3b82f6';
  return new Icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(`
      <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <circle cx="16" cy="16" r="12" fill="${color}" stroke="white" stroke-width="2"/>
        <text x="16" y="20" text-anchor="middle" fill="white" font-size="10" font-weight="bold">${order}</text>
      </svg>
    `)}`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
};

export const RouteManager: React.FC<RouteManagerProps> = ({
  isOpen,
  onClose,
  editingRoute,
  onRouteCreated,
  onRouteUpdated,
}) => {
  const { t } = useI18n();
  const { showToast } = useToast();
  
  const [route, setRoute] = useState<Route>({
    name: '',
    route_number: '',
    geojson: '',
    polyline: '',
    stops: [],
    is_active: true,
  });
  
  const [isAddingStop, setIsAddingStop] = useState(false);
  const [selectedStopIndex, setSelectedStopIndex] = useState<number | null>(null);
  const [draggedStopIndex, setDraggedStopIndex] = useState<number | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Initialize route data when editing
  useEffect(() => {
    if (editingRoute) {
      setRoute(editingRoute);
    } else {
      setRoute({
        name: '',
        route_number: '',
        geojson: '',
        polyline: '',
        stops: [],
        is_active: true,
      });
    }
  }, [editingRoute]);

  // Generate GeoJSON and polyline from stops
  const generateRouteGeometry = useCallback(() => {
    if (route.stops.length < 2) return;

    const coordinates = route.stops
      .sort((a, b) => a.stop_order - b.stop_order)
      .map(stop => [stop.longitude, stop.latitude]);

    const geojson = JSON.stringify({
      type: 'LineString',
      coordinates,
    });

    // Simple polyline encoding (in production, use a proper library)
    const polyline = coordinates.map(coord => `${coord[1]},${coord[0]}`).join(';');

    setRoute(prev => ({
      ...prev,
      geojson,
      polyline,
    }));
  }, [route.stops]);

  useEffect(() => {
    generateRouteGeometry();
  }, [generateRouteGeometry]);

  const handleMapClick = (latlng: LatLng) => {
    if (!isAddingStop) return;

    const newStop: RouteStop = {
      name: `Stop ${route.stops.length + 1}`,
      name_kannada: '',
      latitude: latlng.lat,
      longitude: latlng.lng,
      stop_order: route.stops.length,
    };

    setRoute(prev => ({
      ...prev,
      stops: [...prev.stops, newStop],
    }));

    setIsAddingStop(false);
  };

  const handleStopUpdate = (index: number, field: keyof RouteStop, value: any) => {
    setRoute(prev => ({
      ...prev,
      stops: prev.stops.map((stop, i) => 
        i === index ? { ...stop, [field]: value } : stop
      ),
    }));
  };

  const handleStopDelete = (index: number) => {
    setRoute(prev => ({
      ...prev,
      stops: prev.stops
        .filter((_, i) => i !== index)
        .map((stop, i) => ({ ...stop, stop_order: i })),
    }));
  };

  const handleStopReorder = (fromIndex: number, toIndex: number) => {
    const newStops = [...route.stops];
    const [movedStop] = newStops.splice(fromIndex, 1);
    newStops.splice(toIndex, 0, movedStop);
    
    // Update stop orders
    const reorderedStops = newStops.map((stop, index) => ({
      ...stop,
      stop_order: index,
    }));

    setRoute(prev => ({
      ...prev,
      stops: reorderedStops,
    }));
  };

  const validateRoute = async () => {
    setIsValidating(true);
    try {
      const response = await fetch('/api/v1/admin/routes/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(route),
      });

      if (response.ok) {
        const result = await response.json();
        setValidationResult(result);
        
        if (result.warnings.length > 0) {
          showToast(
            `${t('validation.warnings')}: ${result.warnings.join(', ')}`,
            'warning'
          );
        }
        
        return result.is_valid;
      } else {
        throw new Error('Validation failed');
      }
    } catch (error) {
      showToast(t('validation.error'), 'error');
      return false;
    } finally {
      setIsValidating(false);
    }
  };

  const handleSave = async () => {
    if (route.stops.length < 2) {
      showToast(t('route.error.minimum_stops'), 'error');
      return;
    }

    const isValid = await validateRoute();
    if (!isValid) {
      showToast(
        `${t('validation.failed')}: ${validationResult?.errors?.join(', ') || ''}`,
        'error'
      );
      return;
    }

    setIsSaving(true);
    try {
      const url = editingRoute 
        ? `/api/v1/admin/routes/${editingRoute.id}`
        : '/api/v1/admin/routes';
      
      const method = editingRoute ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(route),
      });

      if (response.ok) {
        const result = await response.json();
        showToast(
          editingRoute ? t('route.updated') : t('route.created'),
          'success'
        );
        
        if (editingRoute && onRouteUpdated) {
          onRouteUpdated(route);
        } else if (!editingRoute && onRouteCreated) {
          onRouteCreated(result.route);
        }
        
        onClose();
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Save failed');
      }
    } catch (error) {
      showToast(
        `${t('route.save.error')}: ${error instanceof Error ? error.message : 'Unknown error'}`,
        'error'
      );
    } finally {
      setIsSaving(false);
    }
  };

  const routeCoordinates = route.stops
    .sort((a, b) => a.stop_order - b.stop_order)
    .map(stop => [stop.latitude, stop.longitude] as [number, number]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={editingRoute ? t('route.edit') : t('route.create')}
      size="xl"
    >
      <div className="flex flex-col h-[80vh]">
        {/* Route Basic Info */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label={t('route.name')}
              value={route.name}
              onChange={(e) => setRoute(prev => ({ ...prev, name: e.target.value }))}
              placeholder={t('route.name.placeholder')}
              required
            />
            <Input
              label={t('route.number')}
              value={route.route_number}
              onChange={(e) => setRoute(prev => ({ ...prev, route_number: e.target.value }))}
              placeholder={t('route.number.placeholder')}
              required
            />
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Map Section */}
          <div className="flex-1 relative">
            <div className="absolute top-4 left-4 z-[1000] space-y-2">
              <Button
                onClick={() => setIsAddingStop(!isAddingStop)}
                variant={isAddingStop ? 'secondary' : 'primary'}
                size="sm"
              >
                {isAddingStop ? t('route.stop.cancel') : t('route.stop.add')}
              </Button>
              
              {isAddingStop && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-blue-100 dark:bg-blue-900 p-2 rounded text-sm"
                >
                  {t('route.stop.click_instruction')}
                </motion.div>
              )}
            </div>

            <MapContainer
              center={[12.9716, 77.5946]} // Bangalore center
              zoom={12}
              style={{ height: '100%', width: '100%' }}
              className={isAddingStop ? 'cursor-crosshair' : ''}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              
              <MapClickHandler
                onMapClick={handleMapClick}
                isAddingStop={isAddingStop}
              />

              {/* Route polyline */}
              {routeCoordinates.length > 1 && (
                <Polyline
                  positions={routeCoordinates}
                  color="#3b82f6"
                  weight={4}
                  opacity={0.7}
                />
              )}

              {/* Stop markers */}
              {route.stops.map((stop, index) => (
                <Marker
                  key={index}
                  position={[stop.latitude, stop.longitude]}
                  icon={createStopIcon(stop.stop_order + 1, selectedStopIndex === index)}
                  eventHandlers={{
                    click: () => setSelectedStopIndex(index),
                  }}
                />
              ))}
            </MapContainer>
          </div>

          {/* Stops Panel */}
          <div className="w-80 border-l border-gray-200 dark:border-gray-700 flex flex-col">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-lg">{t('route.stops')} ({route.stops.length})</h3>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              <AnimatePresence>
                {route.stops
                  .sort((a, b) => a.stop_order - b.stop_order)
                  .map((stop, index) => (
                    <motion.div
                      key={`${stop.latitude}-${stop.longitude}-${index}`}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedStopIndex === index
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedStopIndex(selectedStopIndex === index ? null : index)}
                      draggable
                      onDragStart={() => setDraggedStopIndex(index)}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={() => {
                        if (draggedStopIndex !== null && draggedStopIndex !== index) {
                          handleStopReorder(draggedStopIndex, index);
                          setDraggedStopIndex(null);
                        }
                      }}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                            {stop.stop_order + 1}
                          </div>
                          <span className="font-medium">{stop.name}</span>
                        </div>
                        <Button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStopDelete(index);
                          }}
                          variant="ghost"
                          size="sm"
                          className="text-red-500 hover:text-red-700"
                        >
                          ×
                        </Button>
                      </div>

                      {selectedStopIndex === index && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="space-y-2"
                        >
                          <Input
                            label={t('stop.name')}
                            value={stop.name}
                            onChange={(e) => handleStopUpdate(index, 'name', e.target.value)}
                            size="sm"
                          />
                          <Input
                            label={t('stop.name_kannada')}
                            value={stop.name_kannada || ''}
                            onChange={(e) => handleStopUpdate(index, 'name_kannada', e.target.value)}
                            size="sm"
                          />
                          <div className="grid grid-cols-2 gap-2">
                            <Input
                              label={t('stop.latitude')}
                              type="number"
                              step="0.000001"
                              value={stop.latitude}
                              onChange={(e) => handleStopUpdate(index, 'latitude', parseFloat(e.target.value))}
                              size="sm"
                            />
                            <Input
                              label={t('stop.longitude')}
                              type="number"
                              step="0.000001"
                              value={stop.longitude}
                              onChange={(e) => handleStopUpdate(index, 'longitude', parseFloat(e.target.value))}
                              size="sm"
                            />
                          </div>
                        </motion.div>
                      )}
                    </motion.div>
                  ))}
              </AnimatePresence>

              {route.stops.length === 0 && (
                <div className="text-center text-gray-500 py-8">
                  <p>{t('route.stops.empty')}</p>
                  <p className="text-sm mt-2">{t('route.stops.add_instruction')}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Validation Results */}
        {validationResult && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            {validationResult.errors.length > 0 && (
              <div className="mb-2">
                <h4 className="font-medium text-red-600 mb-1">{t('validation.errors')}:</h4>
                <ul className="text-sm text-red-600 list-disc list-inside">
                  {validationResult.errors.map((error: string, index: number) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {validationResult.warnings.length > 0 && (
              <div>
                <h4 className="font-medium text-yellow-600 mb-1">{t('validation.warnings')}:</h4>
                <ul className="text-sm text-yellow-600 list-disc list-inside">
                  {validationResult.warnings.map((warning: string, index: number) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-between">
          <Button
            onClick={validateRoute}
            variant="secondary"
            disabled={isValidating || route.stops.length < 2}
            loading={isValidating}
          >
            {t('route.validate')}
          </Button>

          <div className="space-x-2">
            <Button onClick={onClose} variant="ghost">
              {t('common.cancel')}
            </Button>
            <Button
              onClick={handleSave}
              disabled={isSaving || route.stops.length < 2 || !route.name || !route.route_number}
              loading={isSaving}
            >
              {editingRoute ? t('common.update') : t('common.create')}
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};