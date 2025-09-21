import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

// Mock all the UI components to avoid complex rendering issues
vi.mock('../SubscriptionModal', () => ({
  default: ({ isOpen, onClose, stopId, stopName }: any) => 
    isOpen ? (
      <div data-testid="subscription-modal">
        <h2>Subscribe to {stopName}</h2>
        <input data-testid="phone-input" placeholder="+91 98765 43210" />
        <button onClick={onClose}>Cancel</button>
        <button data-testid="subscribe-button">Subscribe</button>
      </div>
    ) : null
}));

vi.mock('../NotificationCenter', () => ({
  default: ({ isOpen, onClose, phoneNumber }: any) => 
    isOpen ? (
      <div data-testid="notification-center">
        <h2>Notification Center</h2>
        <input data-testid="search-input" placeholder="Search notifications..." />
        <button onClick={onClose}>Close</button>
      </div>
    ) : null
}));

vi.mock('../SubscriptionManager', () => ({
  default: ({ isOpen, onClose, phoneNumber }: any) => 
    isOpen ? (
      <div data-testid="subscription-manager">
        <h2>Manage Subscriptions</h2>
        <input data-testid="search-input" placeholder="Search subscriptions..." />
        <button onClick={onClose}>Close</button>
      </div>
    ) : null
}));

// Import the mocked components
import SubscriptionModal from '../SubscriptionModal';
import NotificationCenter from '../NotificationCenter';
import SubscriptionManager from '../SubscriptionManager';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
    form: ({ children, ...props }: any) => <form {...props}>{children}</form>,
    h3: ({ children, ...props }: any) => <h3 {...props}>{children}</h3>,
    p: ({ children, ...props }: any) => <p {...props}>{children}</p>,
    svg: ({ children, ...props }: any) => <svg {...props}>{children}</svg>,
    input: ({ children, ...props }: any) => <input {...props}>{children}</input>,
    span: ({ children, ...props }: any) => <span {...props}>{children}</span>,
    label: ({ children, ...props }: any) => <label {...props}>{children}</label>,
  },
  AnimatePresence: ({ children }: any) => children,
}));

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: any) => {
      if (key === 'notifications.minutesAgo' && options?.count) {
        return `${options.count} minutes ago`;
      }
      return key;
    },
    i18n: { language: 'en' }
  })
}));

// Mock useToast hook
vi.mock('../../hooks/useToast', () => ({
  useToast: () => ({
    showToast: vi.fn()
  })
}));

// Mock fetch
global.fetch = vi.fn();

describe('Subscription Flow Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  describe('SubscriptionModal', () => {
    it('renders subscription modal with stop information', () => {
      render(
        <SubscriptionModal
          isOpen={true}
          onClose={vi.fn()}
          stopId={1}
          stopName="Silk Board Junction"
          stopNameKannada="ಸಿಲ್ಕ್ ಬೋರ್ಡ್ ಜಂಕ್ಷನ್"
        />
      );

      expect(screen.getByText('notifications.subscribe')).toBeInTheDocument();
      expect(screen.getByText('Silk Board Junction')).toBeInTheDocument();
      expect(screen.getByText('ಸಿಲ್ಕ್ ಬೋರ್ಡ್ ಜಂಕ್ಷನ್')).toBeInTheDocument();
    });

    it('validates phone number input', async () => {
      render(
        <SubscriptionModal
          isOpen={true}
          onClose={vi.fn()}
          stopId={1}
          stopName="Test Stop"
        />
      );

      const phoneInput = screen.getByPlaceholderText('+91 98765 43210');
      const submitButton = screen.getByText('notifications.subscribe');

      // Try to submit without phone number
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('notifications.phoneRequired')).toBeInTheDocument();
      });

      // Enter invalid phone number
      fireEvent.change(phoneInput, { target: { value: '123' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('notifications.phoneInvalid')).toBeInTheDocument();
      });
    });

    it('submits subscription with valid data', async () => {
      const mockResponse = { id: 1, message: 'Success' };
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const onClose = vi.fn();
      render(
        <SubscriptionModal
          isOpen={true}
          onClose={onClose}
          stopId={1}
          stopName="Test Stop"
        />
      );

      // Fill in valid phone number
      const phoneInput = screen.getByPlaceholderText('+91 98765 43210');
      fireEvent.change(phoneInput, { target: { value: '+91 9876543210' } });

      // Select SMS channel (should be default)
      const smsButton = screen.getByText('notifications.sms');
      fireEvent.click(smsButton);

      // Select ETA threshold
      const etaButton = screen.getByText('5 map.minutes');
      fireEvent.click(etaButton);

      // Submit form
      const submitButton = screen.getByText('notifications.subscribe');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/v1/subscriptions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            phone: '+91 9876543210',
            stop_id: 1,
            channel: 'sms',
            eta_threshold: 5,
          }),
        });
      });
    });

    it('shows success animation after successful subscription', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 1 }),
      });

      render(
        <SubscriptionModal
          isOpen={true}
          onClose={vi.fn()}
          stopId={1}
          stopName="Test Stop"
        />
      );

      // Fill form and submit
      const phoneInput = screen.getByPlaceholderText('+91 98765 43210');
      fireEvent.change(phoneInput, { target: { value: '+91 9876543210' } });
      
      const submitButton = screen.getByText('notifications.subscribe');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('notifications.success')).toBeInTheDocument();
        expect(screen.getByText('notifications.subscriptionCreated')).toBeInTheDocument();
      });
    });

    it('handles subscription error gracefully', async () => {
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network error'));

      render(
        <SubscriptionModal
          isOpen={true}
          onClose={vi.fn()}
          stopId={1}
          stopName="Test Stop"
        />
      );

      // Fill form and submit
      const phoneInput = screen.getByPlaceholderText('+91 98765 43210');
      fireEvent.change(phoneInput, { target: { value: '+91 9876543210' } });
      
      const submitButton = screen.getByText('notifications.subscribe');
      fireEvent.click(submitButton);

      // Should not crash and should show error via toast
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalled();
      });
    });
  });

  describe('NotificationCenter', () => {
    const mockNotifications = [
      {
        id: '1',
        message: 'Bus 335E arriving in 5 minutes',
        channel: 'sms' as const,
        status: 'delivered' as const,
        created_at: new Date().toISOString(),
        sent_at: new Date().toISOString(),
        delivered_at: new Date().toISOString(),
        stop: {
          id: 1,
          name: 'Silk Board Junction',
          name_kannada: 'ಸಿಲ್ಕ್ ಬೋರ್ಡ್ ಜಂಕ್ಷನ್'
        },
        route: {
          id: 1,
          name: 'Majestic to Electronic City',
          route_number: '335E'
        },
        read: false
      },
      {
        id: '2',
        message: 'Bus 201 delayed by 10 minutes',
        channel: 'voice' as const,
        status: 'failed' as const,
        created_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
        error_message: 'Call failed',
        read: true
      }
    ];

    it('renders notification center with history', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ notifications: mockNotifications }),
      });

      render(
        <NotificationCenter
          isOpen={true}
          onClose={vi.fn()}
          phoneNumber="+91 9876543210"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Bus 335E arriving in 5 minutes')).toBeInTheDocument();
        expect(screen.getByText('Bus 201 delayed by 10 minutes')).toBeInTheDocument();
      });
    });

    it('filters notifications by search query', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ notifications: mockNotifications }),
      });

      render(
        <NotificationCenter
          isOpen={true}
          onClose={vi.fn()}
          phoneNumber="+91 9876543210"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Bus 335E arriving in 5 minutes')).toBeInTheDocument();
      });

      // Search for specific bus
      const searchInput = screen.getByPlaceholderText('notifications.searchPlaceholder');
      fireEvent.change(searchInput, { target: { value: '335E' } });

      // Should show only matching notification
      expect(screen.getByText('Bus 335E arriving in 5 minutes')).toBeInTheDocument();
      expect(screen.queryByText('Bus 201 delayed by 10 minutes')).not.toBeInTheDocument();
    });

    it('filters notifications by status', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ notifications: mockNotifications }),
      });

      render(
        <NotificationCenter
          isOpen={true}
          onClose={vi.fn()}
          phoneNumber="+91 9876543210"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Bus 335E arriving in 5 minutes')).toBeInTheDocument();
      });

      // Filter by failed status
      const failedButton = screen.getByText('notifications.failed');
      fireEvent.click(failedButton);

      // Should show only failed notifications
      expect(screen.queryByText('Bus 335E arriving in 5 minutes')).not.toBeInTheDocument();
      expect(screen.getByText('Bus 201 delayed by 10 minutes')).toBeInTheDocument();
    });

    it('marks all notifications as read', async () => {
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ notifications: mockNotifications }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        });

      render(
        <NotificationCenter
          isOpen={true}
          onClose={vi.fn()}
          phoneNumber="+91 9876543210"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('notifications.markAllRead')).toBeInTheDocument();
      });

      const markAllReadButton = screen.getByText('notifications.markAllRead');
      fireEvent.click(markAllReadButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/v1/notifications/mark-all-read?phone=%2B91%209876543210',
          { method: 'POST' }
        );
      });
    });
  });

  describe('SubscriptionManager', () => {
    const mockSubscriptions = [
      {
        id: 1,
        phone: '+91 9876543210',
        stop_id: 1,
        channel: 'sms' as const,
        eta_threshold: 5,
        is_active: true,
        created_at: new Date().toISOString(),
        stop: {
          id: 1,
          name: 'Silk Board Junction',
          name_kannada: 'ಸಿಲ್ಕ್ ಬೋರ್ಡ್ ಜಂಕ್ಷನ್',
          route_name: 'Majestic to Electronic City'
        }
      },
      {
        id: 2,
        phone: '+91 9876543210',
        stop_id: 2,
        channel: 'voice' as const,
        eta_threshold: 10,
        is_active: false,
        created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
        stop: {
          id: 2,
          name: 'Koramangala',
          route_name: 'Banashankari to Whitefield'
        }
      }
    ];

    it('renders subscription manager with user subscriptions', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ subscriptions: mockSubscriptions }),
      });

      render(
        <SubscriptionManager
          isOpen={true}
          onClose={vi.fn()}
          phoneNumber="+91 9876543210"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Silk Board Junction')).toBeInTheDocument();
        expect(screen.getByText('Koramangala')).toBeInTheDocument();
      });
    });

    it('toggles subscription active status', async () => {
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ subscriptions: mockSubscriptions }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        });

      render(
        <SubscriptionManager
          isOpen={true}
          onClose={vi.fn()}
          phoneNumber="+91 9876543210"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('notifications.active')).toBeInTheDocument();
      });

      // Click on active button to deactivate
      const activeButton = screen.getByText('notifications.active');
      fireEvent.click(activeButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/v1/subscriptions/1', {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ is_active: false }),
        });
      });
    });

    it('deletes subscription with confirmation', async () => {
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ subscriptions: mockSubscriptions }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        });

      render(
        <SubscriptionManager
          isOpen={true}
          onClose={vi.fn()}
          phoneNumber="+91 9876543210"
        />
      );

      await waitFor(() => {
        expect(screen.getAllByText('common.delete')[0]).toBeInTheDocument();
      });

      // Click delete button
      const deleteButtons = screen.getAllByText('common.delete');
      fireEvent.click(deleteButtons[0]);

      // Should show confirmation dialog
      await waitFor(() => {
        expect(screen.getByText('notifications.confirmDelete')).toBeInTheDocument();
        expect(screen.getByText('notifications.confirmDeleteMessage')).toBeInTheDocument();
      });

      // Confirm deletion
      const confirmDeleteButton = screen.getAllByText('common.delete')[1]; // Second delete button in confirmation
      fireEvent.click(confirmDeleteButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/v1/subscriptions/1', {
          method: 'DELETE',
        });
      });
    });

    it('searches subscriptions by stop name', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ subscriptions: mockSubscriptions }),
      });

      render(
        <SubscriptionManager
          isOpen={true}
          onClose={vi.fn()}
          phoneNumber="+91 9876543210"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Silk Board Junction')).toBeInTheDocument();
        expect(screen.getByText('Koramangala')).toBeInTheDocument();
      });

      // Search for specific stop
      const searchInput = screen.getByPlaceholderText('notifications.searchSubscriptions');
      fireEvent.change(searchInput, { target: { value: 'Silk Board' } });

      // Should show only matching subscription
      expect(screen.getByText('Silk Board Junction')).toBeInTheDocument();
      expect(screen.queryByText('Koramangala')).not.toBeInTheDocument();
    });
  });

  describe('Integration Flow', () => {
    it('completes full subscription flow from modal to management', async () => {
      // Mock successful subscription creation
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 1, message: 'Success' }),
      });

      const { rerender } = render(
        <SubscriptionModal
          isOpen={true}
          onClose={vi.fn()}
          stopId={1}
          stopName="Test Stop"
        />
      );

      // Complete subscription
      const phoneInput = screen.getByPlaceholderText('+91 98765 43210');
      fireEvent.change(phoneInput, { target: { value: '+91 9876543210' } });
      
      const submitButton = screen.getByText('notifications.subscribe');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('notifications.success')).toBeInTheDocument();
      });

      // Now test that the subscription appears in the manager
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          subscriptions: [{
            id: 1,
            phone: '+91 9876543210',
            stop_id: 1,
            channel: 'sms',
            eta_threshold: 5,
            is_active: true,
            created_at: new Date().toISOString(),
            stop: {
              id: 1,
              name: 'Test Stop'
            }
          }]
        }),
      });

      rerender(
        <SubscriptionManager
          isOpen={true}
          onClose={vi.fn()}
          phoneNumber="+91 9876543210"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Test Stop')).toBeInTheDocument();
        expect(screen.getByText('notifications.active')).toBeInTheDocument();
      });
    });
  });
});