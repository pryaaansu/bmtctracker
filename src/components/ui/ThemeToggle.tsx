import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from '../../contexts/ThemeContext'
import { iconButtonVariants } from '../../design-system/animations'

const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme, isTransitioning } = useTheme()

  return (
    <motion.button
      variants={iconButtonVariants}
      initial="idle"
      whileHover="hover"
      whileTap="tap"
      onClick={toggleTheme}
      disabled={isTransitioning}
      className="
        relative p-3 rounded-xl
        bg-neutral-100 dark:bg-neutral-800
        text-neutral-700 dark:text-neutral-300
        hover:bg-neutral-200 dark:hover:bg-neutral-700
        focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
        transition-all duration-300 ease-out
        disabled:opacity-50 disabled:cursor-not-allowed
        shadow-sm hover:shadow-md
      "
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {/* Background glow effect */}
      <motion.div
        className="absolute inset-0 rounded-xl bg-gradient-to-r from-primary-500/20 to-secondary-500/20"
        initial={{ opacity: 0, scale: 0.8 }}
        whileHover={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.2 }}
      />
      
      {/* Icon container with rotation */}
      <motion.div
        className="relative z-10"
        initial={false}
        animate={{ 
          rotate: theme === 'dark' ? 180 : 0,
          scale: isTransitioning ? 0.8 : 1
        }}
        transition={{ 
          duration: 0.5, 
          ease: [0.4, 0, 0.2, 1],
          type: "spring",
          stiffness: 200,
          damping: 20
        }}
      >
        <AnimatePresence mode="wait">
          {theme === 'light' ? (
            <motion.svg
              key="moon"
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              initial={{ opacity: 0, rotate: -90 }}
              animate={{ opacity: 1, rotate: 0 }}
              exit={{ opacity: 0, rotate: 90 }}
              transition={{ duration: 0.2 }}
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" 
              />
            </motion.svg>
          ) : (
            <motion.svg
              key="sun"
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              initial={{ opacity: 0, rotate: -90 }}
              animate={{ opacity: 1, rotate: 0 }}
              exit={{ opacity: 0, rotate: 90 }}
              transition={{ duration: 0.2 }}
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" 
              />
            </motion.svg>
          )}
        </AnimatePresence>
      </motion.div>
      
      {/* Ripple effect */}
      <motion.div
        className="absolute inset-0 rounded-xl bg-white/20 dark:bg-white/10"
        initial={{ scale: 0, opacity: 0 }}
        whileTap={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.1 }}
      />
    </motion.button>
  )
}

export default ThemeToggle