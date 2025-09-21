import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import AccessibilitySettings from '../AccessibilitySettings'
import { AccessibilityProvider } from '../../../contexts/AccessibilityContext'
import { ThemeProvider } from '../../../contexts/ThemeContext'
import '../../../i18n/config'

// Mock speech synthesis
const mockSpeechSynthesis = {
  speak: vi.fn(),
  cancel: vi.fn(),
  getVoices: vi.fn(() => []),
  onvoiceschanged: null,
  speaking: false,
  pending: false,
  paused: false
}

Object.defineProperty(window, 'speechSynthesis', {
  writable: true,
  value: mockSpeechSynthesis
})

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    <AccessibilityProvider>
      {children}
    </AccessibilityProvider>
  </ThemeProvider>
)

describe('AccessibilitySettings', () => {
  const mockOnClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders accessibility settings modal', () => {
    render(
      <TestWrapper>
        <AccessibilitySettings isOpen={true} onClose={mockOnClose} />
      </TestWrapper>
    )

    expect(screen.getByText('Accessibility Settings')).toBeInTheDocument()
    expect(screen.getByLabelText(/high contrast/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/font size/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/reduce motion/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/text to speech/i)).toBeInTheDocument()
  })

  it('toggles high contrast mode', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <AccessibilitySettings isOpen={true} onClose={mockOnClose} />
      </TestWrapper>
    )

    const highContrastToggle = screen.getByLabelText(/high contrast/i)
    expect(highContrastToggle).toHaveAttribute('aria-checked', 'false')

    await user.click(highContrastToggle)
    expect(highContrastToggle).toHaveAttribute('aria-checked', 'true')
  })

  it('changes font size', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <AccessibilitySettings isOpen={true} onClose={mockOnClose} />
      </TestWrapper>
    )

    const fontSizeSelect = screen.getByLabelText(/font size/i)
    expect(fontSizeSelect).toHaveValue('medium')

    await user.selectOptions(fontSizeSelect, 'large')
    expect(fontSizeSelect).toHaveValue('large')
  })

  it('enables TTS and shows test button', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <AccessibilitySettings isOpen={true} onClose={mockOnClose} />
      </TestWrapper>
    )

    const ttsToggle = screen.getByLabelText(/text to speech/i)
    await user.click(ttsToggle)

    expect(screen.getByText('Test Text-to-Speech')).toBeInTheDocument()
  })

  it('tests TTS functionality', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <AccessibilitySettings isOpen={true} onClose={mockOnClose} />
      </TestWrapper>
    )

    // Enable TTS first
    const ttsToggle = screen.getByLabelText(/text to speech/i)
    await user.click(ttsToggle)

    // Click test button
    const testButton = screen.getByText('Test Text-to-Speech')
    await user.click(testButton)

    expect(mockSpeechSynthesis.speak).toHaveBeenCalled()
  })

  it('displays keyboard navigation instructions', () => {
    render(
      <TestWrapper>
        <AccessibilitySettings isOpen={true} onClose={mockOnClose} />
      </TestWrapper>
    )

    expect(screen.getByText(/keyboard navigation instructions/i)).toBeInTheDocument()
    expect(screen.getByText(/tab.*navigate between elements/i)).toBeInTheDocument()
    expect(screen.getByText(/enter.*activate buttons/i)).toBeInTheDocument()
  })

  it('resets settings to defaults', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <AccessibilitySettings isOpen={true} onClose={mockOnClose} />
      </TestWrapper>
    )

    // Change some settings
    const highContrastToggle = screen.getByLabelText(/high contrast/i)
    await user.click(highContrastToggle)

    const fontSizeSelect = screen.getByLabelText(/font size/i)
    await user.selectOptions(fontSizeSelect, 'large')

    // Reset settings
    const resetButton = screen.getByText('Reset to Defaults')
    await user.click(resetButton)

    // Check that settings are reset
    expect(highContrastToggle).toHaveAttribute('aria-checked', 'false')
    expect(fontSizeSelect).toHaveValue('medium')
  })

  it('persists settings in localStorage', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <AccessibilitySettings isOpen={true} onClose={mockOnClose} />
      </TestWrapper>
    )

    const highContrastToggle = screen.getByLabelText(/high contrast/i)
    await user.click(highContrastToggle)

    await waitFor(() => {
      const stored = localStorage.getItem('bmtc-accessibility-settings')
      expect(stored).toBeTruthy()
      const settings = JSON.parse(stored!)
      expect(settings.highContrast).toBe(true)
    })
  })

  it('has proper ARIA attributes', () => {
    render(
      <TestWrapper>
        <AccessibilitySettings isOpen={true} onClose={mockOnClose} />
      </TestWrapper>
    )

    // Check switches have proper ARIA attributes
    const switches = screen.getAllByRole('switch')
    switches.forEach(switchElement => {
      expect(switchElement).toHaveAttribute('aria-checked')
      expect(switchElement).toHaveAttribute('role', 'switch')
    })

    // Check select has proper label
    const fontSizeSelect = screen.getByLabelText(/font size/i)
    expect(fontSizeSelect).toHaveAttribute('id')
  })

  it('supports keyboard navigation', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <AccessibilitySettings isOpen={true} onClose={mockOnClose} />
      </TestWrapper>
    )

    // Tab through interactive elements
    await user.tab()
    
    // Check if we can navigate to interactive elements
    expect(document.activeElement).toBeTruthy()
    
    // Use Enter to activate if it's a switch
    if (document.activeElement?.getAttribute('role') === 'switch') {
      await user.keyboard('{Enter}')
      expect(document.activeElement).toHaveAttribute('aria-checked', 'true')
    }
  })
})