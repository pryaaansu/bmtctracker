import { useCallback, useEffect, useState } from 'react'
import { useAccessibility } from '../contexts/AccessibilityContext'
import { useI18n } from './useI18n'

interface TTSOptions {
  priority?: 'polite' | 'assertive'
  rate?: number
  pitch?: number
  volume?: number
  interrupt?: boolean
}

export const useTTS = () => {
  const { settings, speak: contextSpeak } = useAccessibility()
  const { currentLang } = useI18n()
  const [isSupported, setIsSupported] = useState(false)
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([])
  const [isSpeaking, setIsSpeaking] = useState(false)

  useEffect(() => {
    if ('speechSynthesis' in window) {
      setIsSupported(true)
      
      const loadVoices = () => {
        const availableVoices = window.speechSynthesis.getVoices()
        setVoices(availableVoices)
      }
      
      loadVoices()
      window.speechSynthesis.onvoiceschanged = loadVoices
      
      // Monitor speaking state
      const checkSpeaking = () => {
        setIsSpeaking(window.speechSynthesis.speaking)
      }
      
      const interval = setInterval(checkSpeaking, 100)
      return () => clearInterval(interval)
    }
  }, [])

  const speak = useCallback((text: string, options: TTSOptions = {}) => {
    if (!settings.ttsEnabled || !isSupported || !text.trim()) return

    const {
      priority = 'polite',
      rate = 0.9,
      pitch = 1,
      volume = 0.8,
      interrupt = false
    } = options

    if (interrupt) {
      window.speechSynthesis.cancel()
    }

    const utterance = new SpeechSynthesisUtterance(text)
    
    // Find appropriate voice for current language
    const voice = voices.find(v => 
      v.lang.startsWith(currentLang) || 
      (currentLang === 'kn' && (v.lang.includes('hi') || v.lang.includes('en-IN')))
    )
    
    if (voice) {
      utterance.voice = voice
    }
    
    utterance.rate = rate
    utterance.pitch = pitch
    utterance.volume = volume
    
    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)
    
    window.speechSynthesis.speak(utterance)
  }, [settings.ttsEnabled, isSupported, voices, currentLang])

  const stop = useCallback(() => {
    if (isSupported) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
    }
  }, [isSupported])

  const pause = useCallback(() => {
    if (isSupported && isSpeaking) {
      window.speechSynthesis.pause()
    }
  }, [isSupported, isSpeaking])

  const resume = useCallback(() => {
    if (isSupported) {
      window.speechSynthesis.resume()
    }
  }, [isSupported])

  // Convenience methods for common use cases
  const speakBusArrival = useCallback((route: string, stop: string, eta: number) => {
    const text = `Bus ${route} is arriving at ${stop} in ${eta} minutes`
    speak(text, { priority: 'assertive', interrupt: true })
  }, [speak])

  const speakNotification = useCallback((message: string) => {
    speak(message, { priority: 'assertive' })
  }, [speak])

  const speakError = useCallback((error: string) => {
    speak(`Error: ${error}`, { priority: 'assertive', interrupt: true })
  }, [speak])

  const speakSuccess = useCallback((message: string) => {
    speak(message, { priority: 'polite' })
  }, [speak])

  return {
    speak,
    stop,
    pause,
    resume,
    speakBusArrival,
    speakNotification,
    speakError,
    speakSuccess,
    isSupported,
    isSpeaking,
    voices,
    enabled: settings.ttsEnabled
  }
}

export default useTTS