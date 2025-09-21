import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { languages, type LanguageCode } from '../../i18n/config'

interface LanguageToggleProps {
  variant?: 'button' | 'dropdown'
  className?: string
}

const LanguageToggle: React.FC<LanguageToggleProps> = ({ 
  variant = 'button',
  className = ''
}) => {
  const { i18n } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const currentLang = i18n.language as LanguageCode
  const currentLanguage = languages[currentLang]

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'kn' : 'en'
    i18n.changeLanguage(newLang)
  }

  const selectLanguage = (langCode: LanguageCode) => {
    i18n.changeLanguage(langCode)
    setIsOpen(false)
  }

  if (variant === 'dropdown') {
    return (
      <div className={`relative ${className}`}>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200 shadow-sm"
          aria-label="Select language"
          aria-expanded={isOpen}
        >
          <span className="text-lg" role="img" aria-label={currentLanguage.name}>
            {currentLanguage.flag}
          </span>
          <span className="text-sm font-medium">
            {currentLanguage.nativeName}
          </span>
          <motion.svg
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </motion.svg>
        </motion.button>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full mt-2 left-0 right-0 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 overflow-hidden"
            >
              {Object.entries(languages).map(([code, lang]) => (
                <motion.button
                  key={code}
                  whileHover={{ backgroundColor: 'rgba(59, 130, 246, 0.1)' }}
                  onClick={() => selectLanguage(code as LanguageCode)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 text-left transition-colors duration-150 ${
                    code === currentLang 
                      ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' 
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  <span className="text-lg" role="img" aria-label={lang.name}>
                    {lang.flag}
                  </span>
                  <div className="flex-1">
                    <div className="text-sm font-medium">{lang.nativeName}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">{lang.name}</div>
                  </div>
                  {code === currentLang && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="w-2 h-2 bg-blue-500 rounded-full"
                    />
                  )}
                </motion.button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Backdrop */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 z-40"
            />
          )}
        </AnimatePresence>
      </div>
    )
  }

  // Button variant (default)
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={toggleLanguage}
      className={`flex items-center space-x-2 px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200 ${className}`}
      aria-label={`Switch to ${i18n.language === 'en' ? 'Kannada' : 'English'}`}
    >
      <motion.span 
        key={currentLang}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="text-lg" 
        role="img" 
        aria-label={currentLanguage.name}
      >
        {currentLanguage.flag}
      </motion.span>
      <motion.span 
        key={`${currentLang}-text`}
        initial={{ opacity: 0, x: 10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.2, delay: 0.1 }}
        className="text-sm font-medium"
      >
        {i18n.language === 'en' ? 'ಕನ್ನಡ' : 'English'}
      </motion.span>
    </motion.button>
  )
}

export default LanguageToggle