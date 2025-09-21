import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './Button';
import { Input } from './Input';
import { Card } from './Card';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../hooks/useI18n';

interface Route {
  id: number;
  name: string;
  route_number: string;
  is_active: boolean;
  stops_count?: number;
}

interface RouteSelectorProps {
  selectedRouteIds: number[];
  onSelectionChange: (routeIds: number[]) => void;
  maxHeight?: string;
}

export const RouteSelector: React.FC<RouteSelectorProps> = ({
  selectedRouteIds,
  onSelectionChange,
  maxHeight = '300px',
}) => {
  const { t } = useI18n();
  const { showToast } = useToast();
  
  const [routes, setRoutes] = useState<Route[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | null>(null);

  const fetchRoutes = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (filterActive !== null) params.append('active_only', filterActive.toString());
      params.append('limit', '100'); // Get more routes for selection
      
      const response = await fetch(`/api/v1/routes?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setRoutes(data.routes);
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
  }, [searchTerm, filterActive]);

  const handleRouteToggle = (routeId: number) => {
    const newSelection = selectedRouteIds.includes(routeId)
      ? selectedRouteIds.filter(id => id !== routeId)
      : [...selectedRouteIds, routeId];
    
    onSelectionChange(newSelection);
  };

  const handleSelectAll = () => {
    const filteredRouteIds = filteredRoutes.map(route => route.id);
    if (selectedRouteIds.length === filteredRouteIds.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(filteredRouteIds);
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
    <div className="space-y-4">
      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-2">
        <div className="flex-1">
          <Input
            placeholder={t('routes.search.placeholder')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            size="sm"
          />
        </div>
        
        <div className="flex gap-1">
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

      {/* Selection Summary */}
      <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
        <span>
          {selectedRouteIds.length === 0 
            ? t('bulk.export.all_routes')
            : t('bulk.export.selected_routes', { count: selectedRouteIds.length })
          }
        </span>
        
        {filteredRoutes.length > 0 && (
          <Button
            onClick={handleSelectAll}
            variant="ghost"
            size="sm"
          >
            {selectedRouteIds.length === filteredRoutes.length 
              ? t('common.clear') 
              : t('routes.select_all')
            }
          </Button>
        )}
      </div>

      {/* Routes List */}
      <Card className="p-0">
        <div 
          className="overflow-y-auto"
          style={{ maxHeight }}
        >
          {loading ? (
            <div className="p-4 space-y-2">
              {[...Array(5)].map((_, index) => (
                <div key={index} className="flex items-center space-x-3 animate-pulse">
                  <div className="w-4 h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-1"></div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              <AnimatePresence>
                {filteredRoutes.map((route) => (
                  <motion.div
                    key={route.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className={`p-3 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors ${
                      selectedRouteIds.includes(route.id) 
                        ? 'bg-blue-50 dark:bg-blue-900/20' 
                        : ''
                    }`}
                    onClick={() => handleRouteToggle(route.id)}
                  >
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={selectedRouteIds.includes(route.id)}
                        onChange={() => handleRouteToggle(route.id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        onClick={(e) => e.stopPropagation()}
                      />
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">
                              {route.route_number}
                            </p>
                            <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                              {route.name}
                            </p>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            {route.stops_count !== undefined && (
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {route.stops_count} {t('route.stops').toLowerCase()}
                              </span>
                            )}
                            
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              route.is_active
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                                : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                            }`}>
                              {route.is_active ? t('status.active') : t('status.inactive')}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              
              {filteredRoutes.length === 0 && !loading && (
                <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                  <p>{t('routes.empty')}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};