import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { EmergencyManagement } from '../EmergencyManagement';

// Mock the hooks
vi.mock('../../../hooks/useToast', () => ({
  useToast: () => ({
    showToast: vi.fn()
  })
}));

// Mock fetch
global.fetch = vi.fn();

const mockEmergencyData = {
  stats: {
    total_incidents: 15,
    incidents_by_type: { medical: 5, safety: 3, accident: 2, harassment: 1, other: 4 },
    incidents_by_status: { reported: 3, acknowledged: 2, in_progress: 1, resolved: 8, closed: 1 },
    recent_incidents: [
      {
        id: 1,
        type: 'medical',
        description: 'Person collapsed at bus stop',
        status: 'reported',
        reported_at: '2024-01-15T10:30:00Z',
        emergency_call_made: true
      },
      {
        id: 2,
        type: 'safety',
        description: 'Suspicious activity',
        status: 'acknowledged',
        reported_at: '2024-01-15T09:15:00Z',
        emergency_call_made: false
      }
    ],
    active_incidents: 6,
    resolved_today: 3
  },
  recent_broadcasts: [
    {
      id: 1,
      title: 'Service Disruption',
      message: 'Route 500D temporarily suspended',
      sent_at: '2024-01-15T08:00:00Z',
      total_recipients: 100,
      successful_deliveries: 95,
      failed_deliveries: 5,
      send_sms: true,
      send_push: true,
      send_whatsapp: false
    }
  ],
  emergency_contacts: [
    {
      id: 1,
      name: 'Police Emergency',
      phone_number: '100',
      type: 'police',
      is_active: true,
      priority: 1
    }
  ]
};

describe('EmergencyManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem('token', 'test-token');
  });

  it('renders emergency stats correctly', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockEmergencyData
    });

    render(<EmergencyManagement />);

    await waitFor(() => {
      expect(screen.getByText('15')).toBeInTheDocument(); // Total incidents
      expect(screen.getByText('6')).toBeInTheDocument(); // Active incidents
      expect(screen.getByText('3')).toBeInTheDocument(); // Resolved today
    });
  });

  it('displays recent incidents list', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockEmergencyData
    });

    render(<EmergencyManagement />);

    await waitFor(() => {
      expect(screen.getByText('Medical Emergency')).toBeInTheDocument();
      expect(screen.getByText('Person collapsed at bus stop')).toBeInTheDocument();
      expect(screen.getByText('Safety Emergency')).toBeInTheDocument();
      expect(screen.getByText('Suspicious activity')).toBeInTheDocument();
    });
  });

  it('displays recent broadcasts', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockEmergencyData
    });

    render(<EmergencyManagement />);

    await waitFor(() => {
      expect(screen.getByText('Service Disruption')).toBeInTheDocument();
      expect(screen.getByText('Route 500D temporarily suspended')).toBeInTheDocument();
      expect(screen.getByText('95/100')).toBeInTheDocument();
    });
  });

  it('opens incident detail modal when incident is clicked', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockEmergencyData
    });

    render(<EmergencyManagement />);

    await waitFor(() => {
      const incidentCard = screen.getByText('Person collapsed at bus stop').closest('div');
      fireEvent.click(incidentCard!);
    });

    await waitFor(() => {
      expect(screen.getByText('Incident Details')).toBeInTheDocument();
      expect(screen.getByText('medical')).toBeInTheDocument();
    });
  });

  it('allows updating incident status', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockEmergencyData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...mockEmergencyData.stats.recent_incidents[0],
          status: 'acknowledged'
        })
      });

    render(<EmergencyManagement />);

    await waitFor(() => {
      const incidentCard = screen.getByText('Person collapsed at bus stop').closest('div');
      fireEvent.click(incidentCard!);
    });

    await waitFor(() => {
      const acknowledgeButton = screen.getByText('Acknowledge');
      fireEvent.click(acknowledgeButton);
    });

    expect(global.fetch).toHaveBeenCalledWith('/api/v1/emergency/incidents/1', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token'
      },
      body: JSON.stringify({
        status: 'acknowledged',
        admin_notes: undefined
      })
    });
  });

  it('opens emergency broadcast modal', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockEmergencyData
    });

    render(<EmergencyManagement />);

    await waitFor(() => {
      const sendAlertButton = screen.getByText('Send Alert');
      fireEvent.click(sendAlertButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Send Emergency Broadcast')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Service Disruption Alert')).toBeInTheDocument();
    });
  });

  it('allows sending emergency broadcast', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockEmergencyData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 2,
          title: 'Test Alert',
          message: 'Test message',
          sent_at: '2024-01-15T12:00:00Z',
          total_recipients: 50,
          successful_deliveries: 48,
          failed_deliveries: 2
        })
      });

    render(<EmergencyManagement />);

    await waitFor(() => {
      const sendAlertButton = screen.getByText('Send Alert');
      fireEvent.click(sendAlertButton);
    });

    await waitFor(() => {
      const titleInput = screen.getByPlaceholderText('Service Disruption Alert');
      const messageInput = screen.getByPlaceholderText('Describe the emergency situation and any actions users should take...');
      
      fireEvent.change(titleInput, { target: { value: 'Test Alert' } });
      fireEvent.change(messageInput, { target: { value: 'Test message' } });
    });

    const sendButton = screen.getByText('Send Broadcast');
    fireEvent.click(sendButton);

    expect(global.fetch).toHaveBeenCalledWith('/api/v1/emergency/broadcast', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token'
      },
      body: JSON.stringify({
        title: 'Test Alert',
        message: 'Test message',
        route_id: null,
        stop_id: null,
        send_sms: true,
        send_push: true,
        send_whatsapp: false
      })
    });
  });

  it('validates broadcast form before sending', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockEmergencyData
    });

    render(<EmergencyManagement />);

    await waitFor(() => {
      const sendAlertButton = screen.getByText('Send Alert');
      fireEvent.click(sendAlertButton);
    });

    await waitFor(() => {
      const sendButton = screen.getByText('Send Broadcast');
      expect(sendButton).toBeDisabled();
    });
  });

  it('handles API errors gracefully', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    render(<EmergencyManagement />);

    // Should show loading state and then handle error
    await waitFor(() => {
      // Component should handle the error gracefully
      expect(screen.queryByText('15')).not.toBeInTheDocument();
    });
  });

  it('shows correct status colors for incidents', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockEmergencyData
    });

    render(<EmergencyManagement />);

    await waitFor(() => {
      const reportedStatus = screen.getByText('reported');
      const acknowledgedStatus = screen.getByText('acknowledged');
      
      expect(reportedStatus).toHaveClass('text-red-800');
      expect(acknowledgedStatus).toHaveClass('text-yellow-800');
    });
  });

  it('allows configuring broadcast channels', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockEmergencyData
    });

    render(<EmergencyManagement />);

    await waitFor(() => {
      const sendAlertButton = screen.getByText('Send Alert');
      fireEvent.click(sendAlertButton);
    });

    await waitFor(() => {
      const smsCheckbox = screen.getByLabelText('SMS');
      const pushCheckbox = screen.getByLabelText('Push Notification');
      const whatsappCheckbox = screen.getByLabelText('WhatsApp');
      
      expect(smsCheckbox).toBeChecked();
      expect(pushCheckbox).toBeChecked();
      expect(whatsappCheckbox).not.toBeChecked();
      
      fireEvent.click(whatsappCheckbox);
      expect(whatsappCheckbox).toBeChecked();
    });
  });

  it('shows loading state initially', () => {
    (global.fetch as any).mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<EmergencyManagement />);

    expect(screen.getByRole('generic')).toHaveClass('animate-spin');
  });
});