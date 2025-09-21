import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { SOSButton } from '../SOSButton';

// Mock the hooks
vi.mock('../../../hooks/useToast', () => ({
  useToast: () => ({
    showToast: vi.fn()
  })
}));

// Mock fetch
global.fetch = vi.fn();

// Mock geolocation
const mockGeolocation = {
  getCurrentPosition: vi.fn(),
  watchPosition: vi.fn(),
  clearWatch: vi.fn()
};

Object.defineProperty(global.navigator, 'geolocation', {
  value: mockGeolocation,
  writable: true
});

describe('SOSButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders SOS button', () => {
    render(<SOSButton />);
    
    const sosButton = screen.getByRole('button', { name: /emergency sos button/i });
    expect(sosButton).toBeInTheDocument();
    expect(sosButton).toHaveClass('bg-red-500');
  });

  it('opens emergency modal when clicked', async () => {
    render(<SOSButton />);
    
    const sosButton = screen.getByRole('button', { name: /emergency sos button/i });
    fireEvent.click(sosButton);
    
    await waitFor(() => {
      expect(screen.getByText('Emergency Report')).toBeInTheDocument();
    });
    
    // Check if emergency types are displayed
    expect(screen.getByText('Medical Emergency')).toBeInTheDocument();
    expect(screen.getByText('Safety Concern')).toBeInTheDocument();
    expect(screen.getByText('Harassment')).toBeInTheDocument();
    expect(screen.getByText('Accident')).toBeInTheDocument();
    expect(screen.getByText('Other Emergency')).toBeInTheDocument();
  });

  it('captures location when modal opens', async () => {
    const mockPosition = {
      coords: {
        latitude: 12.9716,
        longitude: 77.5946
      }
    };

    mockGeolocation.getCurrentPosition.mockImplementationOnce((success) => {
      success(mockPosition);
    });

    render(<SOSButton />);
    
    const sosButton = screen.getByRole('button', { name: /emergency sos button/i });
    fireEvent.click(sosButton);
    
    await waitFor(() => {
      expect(mockGeolocation.getCurrentPosition).toHaveBeenCalled();
    });
    
    await waitFor(() => {
      expect(screen.getByText(/location captured: 12.9716, 77.5946/i)).toBeInTheDocument();
    });
  });

  it('handles location error gracefully', async () => {
    const mockError = new Error('Location access denied');
    
    mockGeolocation.getCurrentPosition.mockImplementationOnce((success, error) => {
      error(mockError);
    });

    render(<SOSButton />);
    
    const sosButton = screen.getByRole('button', { name: /emergency sos button/i });
    fireEvent.click(sosButton);
    
    await waitFor(() => {
      expect(mockGeolocation.getCurrentPosition).toHaveBeenCalled();
    });
  });

  it('allows selecting emergency type', async () => {
    render(<SOSButton />);
    
    const sosButton = screen.getByRole('button', { name: /emergency sos button/i });
    fireEvent.click(sosButton);
    
    await waitFor(() => {
      expect(screen.getByText('Emergency Report')).toBeInTheDocument();
    });
    
    const medicalButton = screen.getByText('Medical Emergency').closest('button');
    fireEvent.click(medicalButton!);
    
    expect(medicalButton).toHaveClass('border-red-500');
  });

  it('allows entering description', async () => {
    render(<SOSButton />);
    
    const sosButton = screen.getByRole('button', { name: /emergency sos button/i });
    fireEvent.click(sosButton);
    
    await waitFor(() => {
      expect(screen.getByText('Emergency Report')).toBeInTheDocument();
    });
    
    const descriptionTextarea = screen.getByPlaceholderText('Describe the emergency situation...');
    fireEvent.change(descriptionTextarea, { 
      target: { value: 'Person needs immediate medical attention' } 
    });
    
    expect(descriptionTextarea).toHaveValue('Person needs immediate medical attention');
  });

  it('submits emergency report successfully', async () => {
    const mockResponse = {
      ok: true,
      json: async () => ({
        id: 1,
        type: 'medical',
        status: 'reported'
      })
    };
    
    (global.fetch as any).mockResolvedValueOnce(mockResponse);
    localStorage.setItem('token', 'test-token');

    render(<SOSButton />);
    
    const sosButton = screen.getByRole('button', { name: /emergency sos button/i });
    fireEvent.click(sosButton);
    
    await waitFor(() => {
      expect(screen.getByText('Emergency Report')).toBeInTheDocument();
    });
    
    // Select emergency type
    const medicalButton = screen.getByText('Medical Emergency').closest('button');
    fireEvent.click(medicalButton!);
    
    // Submit
    const submitButton = screen.getByText('Send Emergency Alert').closest('button');
    fireEvent.click(submitButton!);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/emergency/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token'
        },
        body: expect.stringContaining('"type":"medical"')
      });
    });
  });

  it('handles submission error', async () => {
    const mockResponse = {
      ok: false,
      status: 500
    };
    
    (global.fetch as any).mockResolvedValueOnce(mockResponse);

    render(<SOSButton />);
    
    const sosButton = screen.getByRole('button', { name: /emergency sos button/i });
    fireEvent.click(sosButton);
    
    await waitFor(() => {
      expect(screen.getByText('Emergency Report')).toBeInTheDocument();
    });
    
    // Select emergency type
    const medicalButton = screen.getByText('Medical Emergency').closest('button');
    fireEvent.click(medicalButton!);
    
    // Submit
    const submitButton = screen.getByText('Send Emergency Alert').closest('button');
    fireEvent.click(submitButton!);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });
  });

  it('prevents submission without emergency type', async () => {
    render(<SOSButton />);
    
    const sosButton = screen.getByRole('button', { name: /emergency sos button/i });
    fireEvent.click(sosButton);
    
    await waitFor(() => {
      expect(screen.getByText('Emergency Report')).toBeInTheDocument();
    });
    
    // Try to submit without selecting type
    const submitButton = screen.getByText('Send Emergency Alert').closest('button');
    expect(submitButton).toBeDisabled();
  });

  it('closes modal when cancel is clicked', async () => {
    render(<SOSButton />);
    
    const sosButton = screen.getByRole('button', { name: /emergency sos button/i });
    fireEvent.click(sosButton);
    
    await waitFor(() => {
      expect(screen.getByText('Emergency Report')).toBeInTheDocument();
    });
    
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    
    await waitFor(() => {
      expect(screen.queryByText('Emergency Report')).not.toBeInTheDocument();
    });
  });

  it('shows loading state during submission', async () => {
    const mockResponse = new Promise(resolve => {
      setTimeout(() => resolve({ ok: true, json: async () => ({}) }), 100);
    });
    
    (global.fetch as any).mockReturnValueOnce(mockResponse);

    render(<SOSButton />);
    
    const sosButton = screen.getByRole('button', { name: /emergency sos button/i });
    fireEvent.click(sosButton);
    
    await waitFor(() => {
      expect(screen.getByText('Emergency Report')).toBeInTheDocument();
    });
    
    // Select emergency type
    const medicalButton = screen.getByText('Medical Emergency').closest('button');
    fireEvent.click(medicalButton!);
    
    // Submit
    const submitButton = screen.getByText('Send Emergency Alert').closest('button');
    fireEvent.click(submitButton!);
    
    // Check loading state
    expect(screen.getByText('Sending...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });

  it('displays current timestamp', async () => {
    render(<SOSButton />);
    
    const sosButton = screen.getByRole('button', { name: /emergency sos button/i });
    fireEvent.click(sosButton);
    
    await waitFor(() => {
      expect(screen.getByText('Emergency Report')).toBeInTheDocument();
    });
    
    // Check if timestamp is displayed (format may vary based on locale)
    const timestampElement = screen.getByText(new RegExp(new Date().getFullYear().toString()));
    expect(timestampElement).toBeInTheDocument();
  });

  it('shows emergency contact information', async () => {
    render(<SOSButton />);
    
    const sosButton = screen.getByRole('button', { name: /emergency sos button/i });
    fireEvent.click(sosButton);
    
    await waitFor(() => {
      expect(screen.getByText('Emergency Report')).toBeInTheDocument();
    });
    
    expect(screen.getByText(/emergency services will be notified immediately/i)).toBeInTheDocument();
    expect(screen.getByText(/call 100 \(police\) or 108 \(ambulance\)/i)).toBeInTheDocument();
  });
});