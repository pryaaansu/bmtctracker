import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAccessibility } from '../../contexts/AccessibilityContext'
import { useI18n } from '../../hooks/useI18n'
import Button from './Button'
import Modal from './Modal'

interface AccessibilitySettingsProps {
  isOpen: boolean
  onClose: () => void
}

const AccessibilitySettings: React.FC<AccessibilitySettingsProps> = ({ isOpen, onClose }) => {
  const { settings, updateSetting, speak, resetSettings } = useAccessibility()
  const { t } = useI18n()
  const [testTTS, setTestTTS] = useState(false)

  const handleTTSTest = () => {
    setTestTTS(true)
    speak(t('tts.welcome'))
    setTimeout(() => setTestTTS(false), 2000)
  }

  const fontSizeOptions = [
    { value: 'small', label: t('accessibility.fontSize') + ' - Small' },
    { value: 'medium', label: t('accessibility.fontSize') + ' - Medium' },
    { value: 'large', label: t('accessibility.fontSize') + ' - Large' },
    { value: 'extra-large', label: t('accessibility.fontSize') + ' - Extra Large' }
  ] as const

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Accessibility Settings">
      <div className="space-y-6">
        {/* High Contrast */}
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="high-contrast" className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {t('accessibility.highContrast')}
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Increases contrast for better visibility
            </p>
          </div>
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={() => updateSetting('highContrast', !settings.highContrast)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              settings.highContrast ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700'
            }`}
            role="switch"
            aria-checked={settings.highContrast}
            aria-labelledby="high-contrast"
          >
            <motion.span
              animate={{ x: settings.highContrast ? 20 : 2 }}
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              className="inline-block h-4 w-4 transform rounded-full bg-white shadow-lg"
            />
          </motion.button>
        </div>

        {/* Font Size */}
        <div>
          <label htmlFor="font-size" className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
            {t('accessibility.fontSize')}
          </label>
          <select
            id="font-size"
            value={settings.fontSize}
            onChange={(e) => updateSetting('fontSize', e.target.value as any)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {fontSizeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Reduced Motion */}
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="reduced-motion" className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Reduce Motion
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Minimizes animations and transitions
            </p>
          </div>
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={() => updateSetting('reducedMotion', !settings.reducedMotion)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              settings.reducedMotion ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700'
            }`}
            role="switch"
            aria-checked={settings.reducedMotion}
            aria-labelledby="reduced-motion"
          >
            <motion.span
              animate={{ x: settings.reducedMotion ? 20 : 2 }}
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              className="inline-block h-4 w-4 transform rounded-full bg-white shadow-lg"
            />
          </motion.button>
        </div>

        {/* Text to Speech */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <label htmlFor="tts-enabled" className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {t('accessibility.textToSpeech')}
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Reads important information aloud
              </p>
            </div>
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => updateSetting('ttsEnabled', !settings.ttsEnabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                settings.ttsEnabled ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700'
              }`}
              role="switch"
              aria-checked={settings.ttsEnabled}
              aria-labelledby="tts-enabled"
            >
              <motion.span
                animate={{ x: settings.ttsEnabled ? 20 : 2 }}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                className="inline-block h-4 w-4 transform rounded-full bg-white shadow-lg"
              />
            </motion.button>
          </div>
          
          {settings.ttsEnabled && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <Button
                onClick={handleTTSTest}
                disabled={testTTS}
                variant="secondary"
                size="sm"
                className="w-full"
              >
                {testTTS ? 'Testing...' : 'Test Text-to-Speech'}
              </Button>
            </motion.div>
          )}
        </div>

        {/* Screen Reader Support */}
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="screen-reader" className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Screen Reader Support
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Enhanced support for screen readers
            </p>
          </div>
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={() => updateSetting('screenReaderEnabled', !settings.screenReaderEnabled)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              settings.screenReaderEnabled ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700'
            }`}
            role="switch"
            aria-checked={settings.screenReaderEnabled}
            aria-labelledby="screen-reader"
          >
            <motion.span
              animate={{ x: settings.screenReaderEnabled ? 20 : 2 }}
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              className="inline-block h-4 w-4 transform rounded-full bg-white shadow-lg"
            />
          </motion.button>
        </div>

        {/* Keyboard Navigation Help */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
            {t('keyboard.instructions')}
          </h4>
          <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
            <div>{t('keyboard.tab')}</div>
            <div>{t('keyboard.enter')}</div>
            <div>{t('keyboard.space')}</div>
            <div>{t('keyboard.escape')}</div>
            <div>{t('keyboard.arrows')}</div>
          </div>
        </div>

        {/* Reset Button */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button
            onClick={resetSettings}
            variant="secondary"
            size="sm"
            className="w-full"
          >
            Reset to Defaults
          </Button>
        </div>
      </div>
    </Modal>
  )
}

export default AccessibilitySettings