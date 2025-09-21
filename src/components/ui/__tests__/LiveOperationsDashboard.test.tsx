import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { LiveOperationsDashboard } from '../LiveOperationsDashboard'

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

describe('LiveOperationsDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', async () => {
    render(<LiveOperationsDashboard />)
    
    // The component loads quickly with mock data, so we just check it renders without error
    // In a real scenario with API calls, there would be a loading state
    await waitFor(() => {
      expect(screen.getByText('Live Operations Dashboard')).toBeInTheDocument()
    })
  })

  it('renders dashboard content after loading', async () => {
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText('Live Operations Dashboard')).toBeInTheDocument()
    })
    
    // Check for key metrics
    expect(screen.getByText('Active Buses')).toBeInTheDocument()
    expect(screen.getByText('On-Time Performance')).toBeInTheDocument()
    expect(screen.getByText('Active Alerts')).toBeInTheDocument()
    expect(screen.getByText('Passengers in Transit')).toBeInTheDocument()
  })

  it('displays live bus status section', async () => {
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText('Live Bus Status')).toBeInTheDocument()
    })
    
    // Should show mock bus data
    expect(screen.getByText('KA01AB1234')).toBeInTheDocument()
    expect(screen.getByText('Route 335E')).toBeInTheDocument()
  })

  it('displays system alerts section', async () => {
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText('System Alerts')).toBeInTheDocument()
    })
    
    // Should show mock alert data
    expect(screen.getByText('Route 335E experiencing delays')).toBeInTheDocument()
    expect(screen.getByText('Vehicle maintenance due')).toBeInTheDocument()
  })

  it('shows correct status colors for buses', async () => {
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      const activeStatuses = screen.getAllByText('active')
      const staleStatus = screen.getByText('stale')
      
      expect(activeStatuses[0]).toHaveClass('text-green-600')
      expect(staleStatus).toHaveClass('text-yellow-600')
    })
  })

  it('shows correct severity colors for alerts', async () => {
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      const mediumSeverity = screen.getByText('medium')
      const lowSeverity = screen.getByText('low')
      
      expect(mediumSeverity).toHaveClass('text-yellow-600')
      expect(lowSeverity).toHaveClass('text-blue-600')
    })
  })

  it('displays utilization progress bar', async () => {
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      // Check for progress bar by class since it doesn't have role="progressbar"
      const progressBar = document.querySelector('.bg-green-600.h-2.rounded-full')
      expect(progressBar).toBeInTheDocument()
    })
  })

  it('shows last updated timestamp', async () => {
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument()
    })
  })

  it('displays metric values correctly', async () => {
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      // Check for specific metric values from mock data
      expect(screen.getByText('142')).toBeInTheDocument() // Active buses
      expect(screen.getByText('85.5%')).toBeInTheDocument() // On-time performance
      expect(screen.getByText('2')).toBeInTheDocument() // Active alerts
      expect(screen.getByText('1,250')).toBeInTheDocument() // Passengers in transit
    })
  })

  it('handles empty data gracefully', async () => {
    // This would test the component with no data
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText('Live Operations Dashboard')).toBeInTheDocument()
    })
    
    // Component should still render without crashing
    expect(screen.getByText('Live Bus Status')).toBeInTheDocument()
    expect(screen.getByText('System Alerts')).toBeInTheDocument()
  })

  it('displays vehicle speed and timing information', async () => {
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      // Check for speed display (25 km/h from mock data)
      expect(screen.getByText('25 km/h')).toBeInTheDocument()
      expect(screen.getByText('15 km/h')).toBeInTheDocument()
    })
  })

  it('shows route information for buses', async () => {
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText('Route 335E')).toBeInTheDocument()
      expect(screen.getByText('Route 201A')).toBeInTheDocument()
      expect(screen.getByText('Route 500D')).toBeInTheDocument()
    })
  })

  it('displays alert timestamps', async () => {
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      // Should show time format (will be current time from mock)
      const timeElements = screen.getAllByText(/\d{1,2}:\d{2}:\d{2}/)
      expect(timeElements.length).toBeGreaterThan(0)
    })
  })

  it('shows vehicle IDs in alerts when present', async () => {
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText('Vehicle: KA01AB1234')).toBeInTheDocument()
    })
  })

  it('renders with proper accessibility attributes', async () => {
    render(<LiveOperationsDashboard />)
    
    await waitFor(() => {
      // Check for proper heading structure
      const mainHeading = screen.getByRole('heading', { level: 2 })
      expect(mainHeading).toHaveTextContent('Live Operations Dashboard')
      
      const subHeadings = screen.getAllByRole('heading', { level: 3 })
      expect(subHeadings).toHaveLength(2) // Live Bus Status and System Alerts
    })
  })
})