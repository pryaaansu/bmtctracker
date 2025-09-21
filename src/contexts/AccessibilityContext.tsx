import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useI18n } from '../hooks/useI18n'

interface AccessibilitySettings {
  highContrast: boolean
  fontSize: 'small' | 'medium' | 'large' | 'extra-large'
  reducedMotion: boolean
  screenReaderEnabled: boolean
  ttsEnabled: boolean
  keyboardNavigation: boolean
  focusVisible: boolean
}

interface AccessibilityContextType {
  settings: AccessibilitySettings
  updateSetting: <K extends keyof AccessibilitySettings>(
    key: K,
    value: AccessibilitySettings[K]
  ) => void
  speak: (text: string, priority?: 'polite' | 'assertive') => void
  announceToScreenReader: (message: string) => void
  resetSettings: () => void
}

const defaultSettings: AccessibilitySettings = {
  highContrast: false,
  fontSize: 'medium',
  reducedMotion: false,
  screenReaderEnabled: false,
  ttsEnabled: false,
  keyboardNavigation: true,
  focusVisible: true
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined)

interface AccessibilityProviderProps {
  children: ReactNode
}

export const AccessibilityProvider: React.FC<AccessibilityProviderProps> = ({ children }) => {
  const { t } = useI18n()
  const [settings, setSettings] = useState<AccessibilitySettings>(() => {
    const stored = localStorage.getItem('bmtc-accessibility-settings')
    if (stored) {
      try {
        return { ...defaultSettings, ...JSON.parse(stored) }
      } catch {
        return defaultSettings
      }
    }
    
    // Detect system preferences
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches
    
    return {
      ...defaultSettings,
      reducedMotion: prefersReducedMotion,
      highContrast: prefersHighContrast
    }
  })

  // TTS synthesis reference
  const [synthesis, setSynthesis] = useState<SpeechSynthesis | null>(null)
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([])

  // Initialize TTS
  useEffect(() => {
    if ('speechSynthesis' in window) {
      setSynthesis(window.speechSynthesis)
      
      const loadVoices = () => {
        const availableVoices = window.speechSynthesis.getVoices()
        setVoices(availableVoices)
      }
      
      loadVoices()
      window.speechSynthesis.onvoiceschanged = loadVoices
    }
  }, [])

  // Save settings to localStorage
  useEffect(() => {
    localStorage.setItem('bmtc-accessibility-settings', JSON.stringify(settings))
  }, [settings])

  // Apply CSS classes based on settings
  useEffect(() => {
    const root = document.documentElement
    
    // High contrast
    if (settings.highContrast) {
      root.classList.add('high-contrast')
    } else {
      root.classList.remove('high-contrast')
    }
    
    // Font size
    root.classList.remove('font-small', 'font-medium', 'font-large', 'font-extra-large')
    root.classList.add(`font-${settings.fontSize}`)
    
    // Reduced motion
    if (settings.reducedMotion) {
      root.classList.add('reduce-motion')
    } else {
      root.classList.remove('reduce-motion')
    }
    
    // Focus visible
    if (settings.focusVisible) {
      root.classList.add('focus-visible')
    } else {
      root.classList.remove('focus-visible')
    }
  }, [settings])

  // Listen for system preference changes
  useEffect(() => {
    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    const highContrastQuery = window.matchMedia('(prefers-contrast: high)')
    
    const handleReducedMotionChange = (e: MediaQueryListEvent) => {
      setSettings(prev => ({ ...prev, reducedMotion: e.matches }))
    }
    
    const handleHighContrastChange = (e: MediaQueryListEvent) => {
      setSettings(prev => ({ ...prev, highContrast: e.matches }))
    }
    
    reducedMotionQuery.addEventListener('change', handleReducedMotionChange)
    highContrastQuery.addEventListener('change', handleHighContrastChange)
    
    return () => {
      reducedMotionQuery.removeEventListener('change', handleReducedMotionChange)
      highContrastQuery.removeEventListener('change', handleHighContrastChange)
    }
  }, [])

  const updateSetting = <K extends keyof AccessibilitySettings>(
    key: K,
    value: AccessibilitySettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  const speak = (text: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!settings.ttsEnabled || !synthesis) return
    
    // Cancel any ongoing speech
    synthesis.cancel()
    
    const utterance = new SpeechSynthesisUtterance(text)
    
    // Find appropriate voice for current language
    const currentLang = document.documentElement.lang || 'en'
    const voice = voices.find(v => 
      v.lang.startsWith(currentLang) || 
      (currentLang === 'kn' && v.lang.includes('hi')) // Fallback to Hindi for Kannada
    )
    
    if (voice) {
      utterance.voice = voice
    }
    
    utterance.rate = 0.9
    utterance.pitch = 1
    utterance.volume = 0.8
    
    synthesis.speak(utterance)
  }

  const announceToScreenReader = (message: string) => {
    // Create a live region for screen reader announcements
    const announcement = document.createElement('div')
    announcement.setAttribute('aria-live', 'assertive')
    announcement.setAttribute('aria-atomic', 'true')
    announcement.className = 'sr-only'
    announcement.textContent = message
    
    document.body.appendChild(announcement)
    
    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement)
    }, 1000)
    
    // Also speak if TTS is enabled
    if (settings.ttsEnabled) {
      speak(message, 'assertive')
    }
  }

  const resetSettings = () => {
    setSettings(defaultSettings)
  }

  const contextValue: AccessibilityContextType = {
    settings,
    updateSetting,
    speak,
    announceToScreenReader,
    resetSettings
  }

  return (
    <AccessibilityContext.Provider value={contextValue}>
      {children}
    </AccessibilityContext.Provider>
  )
}

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext)
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider')
  }
  return context
}

export default AccessibilityContext