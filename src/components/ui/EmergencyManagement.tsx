import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Button from './Button';
import Modal from './Modal';
import { useToast } from '../../hooks/useToast';

interface EmergencyIncident {
  id: number;
  type: string;
  description?: string;
  latitude?: number;
  longitude?: number;
  status: string;
  user_id?: number;
  phone_number?: string;
  reported_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  assigned_admin_id?: number;
  admin_notes?: string;
  emergency_call_made: boolean;
  emergency_call_time?: string;
}

interface EmergencyBroadcast {
  id: number;
  title: string;
  message: string;
  route_id?: number;
  stop_id?: number;
  sent_by_admin_id: number;
  sent_at: string;
  total_recipients: number;
  successful_deliveries: number;
  failed_deliveries: number;
  send_sms: boolean;
  send_push: boolean;
  send_whatsapp: boolean;
}

interface EmergencyStats {
  total_incidents: number;
  incidents_by_type: Record<string, number>;
  incidents_by_status: Record<string, number>;
  recent_incidents: EmergencyIncident[];
  active_incidents: number;
  resolved_today: number;
}

interface EmergencyContact {
  id: number;
  name: string;
  phone_number: string;
  type: string;
  is_active: boolean;
  priority: number;
}

export const EmergencyManagement: React.FC = () => {
  const [incidents, setIncidents] = useState<EmergencyIncident[]>([]);
  const [broadcasts, setBroadcasts] = useState<EmergencyBroadcast[]>([]);
  const [stats, setStats] = useState<EmergencyStats | null>(null);
  const [contacts, setContacts] = useState<EmergencyContact[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState<EmergencyIncident | null>(null);
  const [showBroadcastModal, setShowBroadcastModal] = useState(false);
  const [broadcastForm, setBroadcastForm] = useState({
    title: '',
    message: '',
    route_id: '',
    stop_id: '',
    send_sms: true,
    send_push: true,
    send_whatsapp: false
  });
  const { showToast } = useToast();

  useEffect(() => {
    fetchEmergencyData();
  }, []);

  const fetchEmergencyData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch dashboard data
      const dashboardResponse = await fetch('/api/v1/emergency/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (dashboardResponse.ok) {
        const dashboardData = await dashboardResponse.json();
        setStats(dashboardData.stats);
        setBroadcasts(dashboardData.recent_broadcasts);
        setContacts(dashboardData.emergency_contacts);
        setIncidents(dashboardData.stats.recent_incidents);
      }
    } catch (error) {
      console.error('Error fetching emergency data:', error);
      showToast('Failed to load emergency data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const updateIncidentStatus = async (incidentId: number, status: string, notes?: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/emergency/incidents/${incidentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          status,
          admin_notes: notes
        })
      });

      if (response.ok) {
        const updatedIncident = await response.json();
        setIncidents(prev => prev.map(inc => 
          inc.id === incidentId ? updatedIncident : inc
        ));
        showToast('Incident updated successfully', 'success');
        setSelectedIncident(null);
      } else {
        throw new Error('Failed to update incident');
      }
    } catch (error) {
      console.error('Error updating incident:', error);
      showToast('Failed to update incident', 'error');
    }
  };

  const sendEmergencyBroadcast = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/emergency/broadcast', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...broadcastForm,
          route_id: broadcastForm.route_id ? parseInt(broadcastForm.route_id) : null,
          stop_id: broadcastForm.stop_id ? parseInt(broadcastForm.stop_id) : null
        })
      });

      if (response.ok) {
        const newBroadcast = await response.json();
        setBroadcasts(prev => [newBroadcast, ...prev]);
        showToast('Emergency broadcast sent successfully', 'success');
        setShowBroadcastModal(false);
        setBroadcastForm({
          title: '',
          message: '',
          route_id: '',
          stop_id: '',
          send_sms: true,
          send_push: true,
          send_whatsapp: false
        });
      } else {
        throw new Error('Failed to send broadcast');
      }
    } catch (error) {
      console.error('Error sending broadcast:', error);
      showToast('Failed to send emergency broadcast', 'error');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'reported': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      case 'acknowledged': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'in_progress': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'resolved': return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'closed': return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'medical': return 'bg-red-500';
      case 'safety': return 'bg-orange-500';
      case 'harassment': return 'bg-purple-500';
      case 'accident': return 'bg-red-600';
      default: return 'bg-gray-500';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 dark:bg-red-900/20 rounded-lg">
                <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Incidents</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{stats.total_incidents}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg">
                <svg className="w-6 h-6 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Incidents</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{stats.active_incidents}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Resolved Today</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{stats.resolved_today}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Emergency Broadcast</p>
                <p className="text-sm text-gray-500 dark:text-gray-500">Send alerts to users</p>
              </div>
              <Button
                onClick={() => setShowBroadcastModal(true)}
                className="bg-red-600 hover:bg-red-700 text-white"
                size="sm"
              >
                Send Alert
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Incidents */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Recent Incidents</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {incidents.map((incident) => (
                <motion.div
                  key={incident.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer"
                  onClick={() => setSelectedIncident(incident)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <div className={`w-3 h-3 rounded-full ${getTypeColor(incident.type)} mt-1`}></div>
                      <div>
                        <p className="font-medium text-gray-900 dark:text-gray-100 capitalize">
                          {incident.type} Emergency
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {incident.description || 'No description provided'}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          {new Date(incident.reported_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(incident.status)}`}>
                      {incident.status.replace('_', ' ')}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Broadcasts */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Recent Broadcasts</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {broadcasts.map((broadcast) => (
                <div key={broadcast.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{broadcast.title}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{broadcast.message}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                        {new Date(broadcast.sent_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {broadcast.successful_deliveries}/{broadcast.total_recipients}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-500">delivered</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Incident Detail Modal */}
      <AnimatePresence>
        {selectedIncident && (
          <Modal
            isOpen={!!selectedIncident}
            onClose={() => setSelectedIncident(null)}
            title="Incident Details"
            className="max-w-2xl"
          >
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Type</label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-gray-100 capitalize">{selectedIncident.type}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Status</label>
                  <span className={`inline-block mt-1 px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(selectedIncident.status)}`}>
                    {selectedIncident.status.replace('_', ' ')}
                  </span>
                </div>
              </div>

              {selectedIncident.description && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Description</label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">{selectedIncident.description}</p>
                </div>
              )}

              {selectedIncident.latitude && selectedIncident.longitude && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Location</label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                    {selectedIncident.latitude.toFixed(6)}, {selectedIncident.longitude.toFixed(6)}
                  </p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Reported At</label>
                <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                  {new Date(selectedIncident.reported_at).toLocaleString()}
                </p>
              </div>

              {selectedIncident.emergency_call_made && (
                <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                  <p className="text-sm text-red-800 dark:text-red-400">
                    Emergency call was made at {selectedIncident.emergency_call_time ? new Date(selectedIncident.emergency_call_time).toLocaleString() : 'the time of reporting'}
                  </p>
                </div>
              )}

              <div className="flex space-x-3">
                {selectedIncident.status === 'reported' && (
                  <Button
                    onClick={() => updateIncidentStatus(selectedIncident.id, 'acknowledged')}
                    className="bg-yellow-600 hover:bg-yellow-700 text-white"
                  >
                    Acknowledge
                  </Button>
                )}
                {selectedIncident.status === 'acknowledged' && (
                  <Button
                    onClick={() => updateIncidentStatus(selectedIncident.id, 'in_progress')}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    Start Investigation
                  </Button>
                )}
                {['acknowledged', 'in_progress'].includes(selectedIncident.status) && (
                  <Button
                    onClick={() => updateIncidentStatus(selectedIncident.id, 'resolved', 'Incident resolved by admin')}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    Mark Resolved
                  </Button>
                )}
              </div>
            </div>
          </Modal>
        )}
      </AnimatePresence>

      {/* Emergency Broadcast Modal */}
      <AnimatePresence>
        {showBroadcastModal && (
          <Modal
            isOpen={showBroadcastModal}
            onClose={() => setShowBroadcastModal(false)}
            title="Send Emergency Broadcast"
            className="max-w-lg"
          >
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Alert Title *
                </label>
                <input
                  type="text"
                  value={broadcastForm.title}
                  onChange={(e) => setBroadcastForm(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg 
                           bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                           focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="Service Disruption Alert"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Message *
                </label>
                <textarea
                  value={broadcastForm.message}
                  onChange={(e) => setBroadcastForm(prev => ({ ...prev, message: e.target.value }))}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg 
                           bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                           focus:ring-2 focus:ring-red-500 focus:border-transparent
                           resize-none"
                  rows={4}
                  placeholder="Describe the emergency situation and any actions users should take..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Route ID (Optional)
                  </label>
                  <input
                    type="number"
                    value={broadcastForm.route_id}
                    onChange={(e) => setBroadcastForm(prev => ({ ...prev, route_id: e.target.value }))}
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg 
                             bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                             focus:ring-2 focus:ring-red-500 focus:border-transparent"
                    placeholder="Leave empty for all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Stop ID (Optional)
                  </label>
                  <input
                    type="number"
                    value={broadcastForm.stop_id}
                    onChange={(e) => setBroadcastForm(prev => ({ ...prev, stop_id: e.target.value }))}
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg 
                             bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                             focus:ring-2 focus:ring-red-500 focus:border-transparent"
                    placeholder="Leave empty for all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Delivery Channels
                </label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={broadcastForm.send_sms}
                      onChange={(e) => setBroadcastForm(prev => ({ ...prev, send_sms: e.target.checked }))}
                      className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">SMS</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={broadcastForm.send_push}
                      onChange={(e) => setBroadcastForm(prev => ({ ...prev, send_push: e.target.checked }))}
                      className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Push Notification</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={broadcastForm.send_whatsapp}
                      onChange={(e) => setBroadcastForm(prev => ({ ...prev, send_whatsapp: e.target.checked }))}
                      className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">WhatsApp</span>
                  </label>
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
                <Button
                  onClick={() => setShowBroadcastModal(false)}
                  variant="outline"
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={sendEmergencyBroadcast}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                  disabled={!broadcastForm.title || !broadcastForm.message}
                >
                  Send Broadcast
                </Button>
              </div>
            </div>
          </Modal>
        )}
      </AnimatePresence>
    </div>
  );
};