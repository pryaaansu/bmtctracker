import React, { useState } from 'react';
import { RouteList } from './RouteList';
import { RouteManager } from './RouteManager';
import { BulkRouteOperations } from './BulkRouteOperations';

interface Route {
  id?: number;
  name: string;
  route_number: string;
  geojson: string;
  polyline: string;
  stops: any[];
  is_active: boolean;
  created_at?: string;
}

export const RouteManagement: React.FC = () => {
  const [showRouteManager, setShowRouteManager] = useState(false);
  const [editingRoute, setEditingRoute] = useState<Route | null>(null);
  const [showBulkOperations, setShowBulkOperations] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleCreateRoute = () => {
    setEditingRoute(null);
    setShowRouteManager(true);
  };

  const handleEditRoute = (route: Route) => {
    setEditingRoute(route);
    setShowRouteManager(true);
  };

  const handleRouteCreated = (route: Route) => {
    setRefreshTrigger(prev => prev + 1);
    setShowRouteManager(false);
  };

  const handleRouteUpdated = (route: Route) => {
    setRefreshTrigger(prev => prev + 1);
    setShowRouteManager(false);
  };

  const handleCloseManager = () => {
    setShowRouteManager(false);
    setEditingRoute(null);
  };

  return (
    <div className="space-y-6">
      <RouteList
        onCreateRoute={handleCreateRoute}
        onEditRoute={handleEditRoute}
        refreshTrigger={refreshTrigger}
      />

      <RouteManager
        isOpen={showRouteManager}
        onClose={handleCloseManager}
        editingRoute={editingRoute}
        onRouteCreated={handleRouteCreated}
        onRouteUpdated={handleRouteUpdated}
      />

      <BulkRouteOperations
        isOpen={showBulkOperations}
        onClose={() => setShowBulkOperations(false)}
        onOperationComplete={() => setRefreshTrigger(prev => prev + 1)}
      />
    </div>
  );
};