import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useI18n } from '../../hooks/useI18n'

interface KeyboardNavigationProps {
  children: React.ReactNode
  className?: string
}

const KeyboardNavigation: React.FC<KeyboardNavigationProps> = ({ children, className = '' }) => {
  const { t } = useI18n()
  const [showHelp, setShowHelp] = useState(false)
  const [isKeyboardUser, setIsKeyboardUser] = useState(false)

  useEffect(() => {
    let keyboardTimeout: NodeJS.Timeout

    const handleKeyDown = (e: KeyboardEvent) => {
      // Detect keyboard usage
      if (e.key === 'Tab' || e.key === 'Enter' || e.key === ' ' || e.key === 'Escape') {
        setIsKeyboardUser(true)
        clearTimeout(keyboardTimeout)
        keyboardTimeout = setTimeout(() => setIsKeyboardUser(false), 5000)
      }

      // Show help with F1 or Ctrl+?
      if (e.key === 'F1' || (e.ctrlKey && e.key === '?')) {
        e.preventDefault()
        setShowHelp(true)
      }

      // Hide help with Escape
      if (e.key === 'Escape' && showHelp) {
        setShowHelp(false)
      }
    }

    const handleMouseDown = () => {
      setIsKeyboardUser(false)
      clearTimeout(keyboardTimeout)
    }

    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('mousedown', handleMouseDown)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('mousedown', handleMouseDown)
      clearTimeout(keyboardTimeout)
    }
  }, [showHelp])

  return (
    <div className={`keyboard-navigation-container ${className}`}>
      {/* Skip to content link */}
      <a
        href="#main-content"
        className="skip-link"
        onFocus={() => setIsKeyboardUser(true)}
      >
        {t('accessibility.skipToContent')}
      </a>

      {/* Keyboard user indicator */}
      <AnimatePresence>
        {isKeyboardUser && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-4 right-4 z-50 bg-primary-600 text-white px-3 py-2 rounded-lg shadow-lg text-sm"
          >
            <div className="flex items-center space-x-2">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h6a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              <span>Keyboard Navigation Active</span>
              <button
                onClick={() => setShowHelp(true)}
                className="text-xs underline hover:no-underline"
              >
                Help (F1)
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Keyboard help modal */}
      <AnimatePresence>
        {showHelp && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
            onClick={() => setShowHelp(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md mx-4 shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {t('keyboard.instructions')}
                </h3>
                <button
                  onClick={() => setShowHelp(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  aria-label="Close help"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
                <div className="flex justify-between">
                  <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Tab</kbd>
                  <span>{t('keyboard.tab')}</span>
                </div>
                <div className="flex justify-between">
                  <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Enter</kbd>
                  <span>{t('keyboard.enter')}</span>
                </div>
                <div className="flex justify-between">
                  <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Space</kbd>
                  <span>{t('keyboard.space')}</span>
                </div>
                <div className="flex justify-between">
                  <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Esc</kbd>
                  <span>{t('keyboard.escape')}</span>
                </div>
                <div className="flex justify-between">
                  <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">↑↓←→</kbd>
                  <span>{t('keyboard.arrows')}</span>
                </div>
                <div className="flex justify-between">
                  <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Home</kbd>
                  <span>{t('keyboard.home')}</span>
                </div>
                <div className="flex justify-between">
                  <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">End</kbd>
                  <span>{t('keyboard.end')}</span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Press <kbd className="px-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">F1</kbd> anytime to show this help
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {children}
    </div>
  )
}

export default KeyboardNavigation