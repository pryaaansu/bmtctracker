import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './Button';
import { Input } from './Input';
import { Card } from './Card';
import { Modal } from './Modal';
import { Toast } from './Toast';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../hooks/useI18n';

interface Route {
  id: number;
  name: string;
  route_number: string;
  geojson: string;
  polyline: string;
  is_active: boolean;
  created_at: string;
  stops_count?: number;
}

interface RouteListProps {
  onEditRoute: (route: Route) => void;
  onCreateRoute: () => void;
  refreshTrigger?: number;
}

export const RouteList: React.FC<RouteListProps> = ({
  onEditRoute,
  onCreateRoute,
  refreshTrigger = 0,
}) => {
  const { t } = useI18n();
  const { showToast } = useToast();
  
  const [routes, setRoutes] = useState<Route[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | null>(null);
  const [selectedRoutes, setSelectedRoutes] = useState<Set<number>>(new Set());
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [routeToDelete, setRouteToDelete] = useState<Route | null>(null);
  const [bulkDeleting, setBulkDeleting] = useState(false);

  const fetchRoutes = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (filterActive !== null) params.append('active_only', filterActive.toString());
      
      const response = await fetch(`/api/v1/routes?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        
        // Fetch stop counts for each route
        const routesWithStops = await Promise.all(
          data.routes.map(async (route: Route) => {
            try {
              const stopsResponse = await fetch(`/api/v1/routes/${route.id}/stops`, {
                headers: {
                  'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
              });
              
              if (stopsResponse.ok) {
                const stopsData = await stopsResponse.json();
                return { ...route, stops_count: stopsData.total_stops };
              }
            } catch (error) {
              console.error('Error fetching stops for route:', route.id, error);
            }
            return { ...route, stops_count: 0 };
          })
        );
        
        setRoutes(routesWithStops);
      } else {
        throw new Error('Failed to fetch routes');
      }
    } catch (error) {
      showToast(t('routes.fetch.error'), 'error');
      console.error('Error fetching routes:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoutes();
  }, [searchTerm, filterActive, refreshTrigger]);

  const handleDeleteRoute = async (route: Route) => {
    try {
      const response = await fetch(`/api/v1/admin/routes/${route.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        showToast(t('route.deleted'), 'success');
        fetchRoutes();
        setShowDeleteModal(false);
        setRouteToDelete(null);
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Delete failed');
      }
    } catch (error) {
      showToast(
        `${t('route.delete.error')}: ${error instanceof Error ? error.message : 'Unknown error'}`,
        'error'
      );
    }
  };

  const handleBulkDelete = async () => {
    setBulkDeleting(true);
    try {
      const deletePromises = Array.from(selectedRoutes).map(routeId =>
        fetch(`/api/v1/admin/routes/${routeId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        })
      );

      const results = await Promise.allSettled(deletePromises);
      const successful = results.filter(result => result.status === 'fulfilled').length;
      const failed = results.length - successful;

      if (successful > 0) {
        showToast(
          `${successful} ${t('routes.deleted')}${failed > 0 ? `, ${failed} ${t('routes.delete.failed')}` : ''}`,
          failed > 0 ? 'warning' : 'success'
        );
        fetchRoutes();
        setSelectedRoutes(new Set());
      }
    } catch (error) {
      showToast(t('routes.bulk_delete.error'), 'error');
    } finally {
      setBulkDeleting(false);
    }
  };

  const toggleRouteSelection = (routeId: number) => {
    const newSelection = new Set(selectedRoutes);
    if (newSelection.has(routeId)) {
      newSelection.delete(routeId);
    } else {
      newSelection.add(routeId);
    }
    setSelectedRoutes(newSelection);
  };

  const toggleSelectAll = () => {
    if (selectedRoutes.size === routes.length) {
      setSelectedRoutes(new Set());
    } else {
      setSelectedRoutes(new Set(routes.map(route => route.id)));
    }
  };

  const filteredRoutes = routes.filter(route => {
    const matchesSearch = !searchTerm || 
      route.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      route.route_number.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterActive === null || route.is_active === filterActive;
    
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t('routes.management')}
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            {t('routes.management.description')}
          </p>
        </div>
        
        <Button onClick={onCreateRoute} className="whitespace-nowrap">
          {t('route.create')}
        </Button>
      </div>

      {/* Search and Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder={t('routes.search.placeholder')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full"
            />
          </div>
          
          <div className="flex gap-2">
            <Button
              variant={filterActive === null ? 'primary' : 'secondary'}
              onClick={() => setFilterActive(null)}
              size="sm"
            >
              {t('routes.filter.all')}
            </Button>
            <Button
              variant={filterActive === true ? 'primary' : 'secondary'}
              onClick={() => setFilterActive(true)}
              size="sm"
            >
              {t('routes.filter.active')}
            </Button>
            <Button
              variant={filterActive === false ? 'primary' : 'secondary'}
              onClick={() => setFilterActive(false)}
              size="sm"
            >
              {t('routes.filter.inactive')}
            </Button>
          </div>
        </div>

        {/* Bulk Actions */}
        {selectedRoutes.size > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex items-center justify-between"
          >
            <span className="text-sm text-blue-700 dark:text-blue-300">
              {selectedRoutes.size} {t('routes.selected')}
            </span>
            <div className="space-x-2">
              <Button
                onClick={() => setSelectedRoutes(new Set())}
                variant="ghost"
                size="sm"
              >
                {t('common.clear')}
              </Button>
              <Button
                onClick={handleBulkDelete}
                variant="secondary"
                size="sm"
                loading={bulkDeleting}
                className="text-red-600 hover:text-red-700"
              >
                {t('routes.delete.selected')}
              </Button>
            </div>
          </motion.div>
        )}
      </Card>

      {/* Routes List */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, index) => (
            <Card key={index} className="p-4 animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded mb-4 w-2/3"></div>
              <div className="space-y-2">
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <>
          {/* Select All Checkbox */}
          {filteredRoutes.length > 0 && (
            <div className="flex items-center space-x-2 px-2">
              <input
                type="checkbox"
                checked={selectedRoutes.size === filteredRoutes.length}
                onChange={toggleSelectAll}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label className="text-sm text-gray-600 dark:text-gray-400">
                {t('routes.select_all')}
              </label>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <AnimatePresence>
              {filteredRoutes.map((route) => (
                <motion.div
                  key={route.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  layout
                >
                  <Card className={`p-4 cursor-pointer transition-all hover:shadow-lg ${
                    selectedRoutes.has(route.id) 
                      ? 'ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                      : ''
                  }`}>
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={selectedRoutes.has(route.id)}
                          onChange={() => toggleRouteSelection(route.id)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <div>
                          <h3 className="font-semibold text-gray-900 dark:text-white">
                            {route.route_number}
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {route.name}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          route.is_active
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                        }`}>
                          {route.is_active ? t('status.active') : t('status.inactive')}
                        </span>
                      </div>
                    </div>

                    <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
                      <div className="flex justify-between">
                        <span>{t('route.stops')}:</span>
                        <span className="font-medium">{route.stops_count || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>{t('route.created')}:</span>
                        <span>{new Date(route.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <div className="flex space-x-2">
                      <Button
                        onClick={() => onEditRoute(route)}
                        variant="secondary"
                        size="sm"
                        className="flex-1"
                      >
                        {t('common.edit')}
                      </Button>
                      <Button
                        onClick={() => {
                          setRouteToDelete(route);
                          setShowDeleteModal(true);
                        }}
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:text-red-700"
                      >
                        {t('common.delete')}
                      </Button>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {filteredRoutes.length === 0 && !loading && (
            <Card className="p-8 text-center">
              <div className="text-gray-500 dark:text-gray-400">
                <p className="text-lg mb-2">{t('routes.empty')}</p>
                <p className="text-sm mb-4">{t('routes.empty.description')}</p>
                <Button onClick={onCreateRoute}>
                  {t('route.create.first')}
                </Button>
              </div>
            </Card>
          )}
        </>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setRouteToDelete(null);
        }}
        title={t('route.delete.confirm')}
      >
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400">
            {t('route.delete.warning', { 
              routeName: routeToDelete?.name,
              routeNumber: routeToDelete?.route_number 
            })}
          </p>
          
          <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              {t('route.delete.consequences')}
            </p>
          </div>

          <div className="flex justify-end space-x-2">
            <Button
              onClick={() => {
                setShowDeleteModal(false);
                setRouteToDelete(null);
              }}
              variant="ghost"
            >
              {t('common.cancel')}
            </Button>
            <Button
              onClick={() => routeToDelete && handleDeleteRoute(routeToDelete)}
              variant="secondary"
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {t('common.delete')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};