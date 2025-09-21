import React from 'react'
import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import useTTS from '../useTTS'
import { AccessibilityProvider } from '../../contexts/AccessibilityContext'
import { ThemeProvider } from '../../contexts/ThemeContext'
import '../../i18n/config'

// Mock speech synthesis
const mockUtterance = {
  text: '',
  voice: null,
  rate: 1,
  pitch: 1,
  volume: 1,
  onstart: null,
  onend: null,
  onerror: null
}

const mockSpeechSynthesis = {
  speak: vi.fn(),
  cancel: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  getVoices: vi.fn(() => [
    { name: 'English Voice', lang: 'en-US' },
    { name: 'Hindi Voice', lang: 'hi-IN' },
    { name: 'Kannada Voice', lang: 'kn-IN' }
  ]),
  onvoiceschanged: null,
  speaking: false,
  pending: false,
  paused: false
}

Object.defineProperty(window, 'speechSynthesis', {
  writable: true,
  value: mockSpeechSynthesis
})

Object.defineProperty(window, 'SpeechSynthesisUtterance', {
  writable: true,
  value: vi.fn(() => mockUtterance)
})

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    <AccessibilityProvider>
      {children}
    </AccessibilityProvider>
  </ThemeProvider>
)

describe('useTTS', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('initializes with correct default values', () => {
    const { result } = renderHook(() => useTTS(), {
      wrapper: TestWrapper
    })

    expect(result.current.isSupported).toBe(true)
    expect(result.current.isSpeaking).toBe(false)
    expect(result.current.enabled).toBe(false) // TTS disabled by default
    expect(typeof result.current.speak).toBe('function')
    expect(typeof result.current.stop).toBe('function')
  })

  it('does not speak when TTS is disabled', () => {
    const { result } = renderHook(() => useTTS(), {
      wrapper: TestWrapper
    })

    act(() => {
      result.current.speak('Hello world')
    })

    expect(mockSpeechSynthesis.speak).not.toHaveBeenCalled()
  })

  it('speaks when TTS is enabled', () => {
    const { result } = renderHook(() => useTTS(), {
      wrapper: TestWrapper
    })

    // Enable TTS first (this would normally be done through AccessibilitySettings)
    // For testing, we'll mock the enabled state
    Object.defineProperty(result.current, 'enabled', {
      value: true,
      writable: true
    })

    act(() => {
      result.current.speak('Hello world')
    })

    expect(window.SpeechSynthesisUtterance).toHaveBeenCalledWith('Hello world')
    expect(mockSpeechSynthesis.speak).toHaveBeenCalled()
  })

  it('cancels speech when stop is called', () => {
    const { result } = renderHook(() => useTTS(), {
      wrapper: TestWrapper
    })

    act(() => {
      result.current.stop()
    })

    expect(mockSpeechSynthesis.cancel).toHaveBeenCalled()
  })

  it('pauses and resumes speech', () => {
    const { result } = renderHook(() => useTTS(), {
      wrapper: TestWrapper
    })

    act(() => {
      result.current.pause()
    })
    expect(mockSpeechSynthesis.pause).toHaveBeenCalled()

    act(() => {
      result.current.resume()
    })
    expect(mockSpeechSynthesis.resume).toHaveBeenCalled()
  })

  it('provides convenience methods for common use cases', () => {
    const { result } = renderHook(() => useTTS(), {
      wrapper: TestWrapper
    })

    expect(typeof result.current.speakBusArrival).toBe('function')
    expect(typeof result.current.speakNotification).toBe('function')
    expect(typeof result.current.speakError).toBe('function')
    expect(typeof result.current.speakSuccess).toBe('function')
  })

  it('formats bus arrival announcements correctly', () => {
    const { result } = renderHook(() => useTTS(), {
      wrapper: TestWrapper
    })

    // Mock enabled state
    Object.defineProperty(result.current, 'enabled', {
      value: true,
      writable: true
    })

    act(() => {
      result.current.speakBusArrival('335E', 'Majestic', 5)
    })

    expect(window.SpeechSynthesisUtterance).toHaveBeenCalledWith(
      'Bus 335E is arriving at Majestic in 5 minutes'
    )
  })

  it('handles speech synthesis not supported', () => {
    // Temporarily remove speechSynthesis
    const originalSpeechSynthesis = window.speechSynthesis
    delete (window as any).speechSynthesis

    const { result } = renderHook(() => useTTS(), {
      wrapper: TestWrapper
    })

    expect(result.current.isSupported).toBe(false)

    act(() => {
      result.current.speak('Hello world')
    })

    // Should not throw error
    expect(result.current.isSpeaking).toBe(false)

    // Restore speechSynthesis
    Object.defineProperty(window, 'speechSynthesis', {
      value: originalSpeechSynthesis,
      writable: true
    })
  })

  it('selects appropriate voice for language', () => {
    const { result } = renderHook(() => useTTS(), {
      wrapper: TestWrapper
    })

    expect(result.current.voices).toHaveLength(3)
    expect(result.current.voices[0].name).toBe('English Voice')
    expect(result.current.voices[1].name).toBe('Hindi Voice')
    expect(result.current.voices[2].name).toBe('Kannada Voice')
  })

  it('interrupts speech when interrupt option is true', () => {
    const { result } = renderHook(() => useTTS(), {
      wrapper: TestWrapper
    })

    // Mock enabled state
    Object.defineProperty(result.current, 'enabled', {
      value: true,
      writable: true
    })

    act(() => {
      result.current.speak('Hello world', { interrupt: true })
    })

    expect(mockSpeechSynthesis.cancel).toHaveBeenCalled()
    expect(mockSpeechSynthesis.speak).toHaveBeenCalled()
  })

  it('applies custom speech options', () => {
    const { result } = renderHook(() => useTTS(), {
      wrapper: TestWrapper
    })

    // Mock enabled state
    Object.defineProperty(result.current, 'enabled', {
      value: true,
      writable: true
    })

    act(() => {
      result.current.speak('Hello world', {
        rate: 1.5,
        pitch: 0.8,
        volume: 0.5
      })
    })

    expect(mockUtterance.rate).toBe(1.5)
    expect(mockUtterance.pitch).toBe(0.8)
    expect(mockUtterance.volume).toBe(0.5)
  })
})