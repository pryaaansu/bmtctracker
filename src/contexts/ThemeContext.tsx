import React, { createContext, useContext, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { lightTheme, darkTheme, type Theme as ThemeTokens } from '../design-system/tokens'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
  themeTokens: ThemeTokens
  isTransitioning: boolean
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

interface ThemeProviderProps {
  children: React.ReactNode
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    return (saved as Theme) || (prefersDark ? 'dark' : 'light')
  })
  
  const [isTransitioning, setIsTransitioning] = useState(false)

  // Get current theme tokens
  const themeTokens = theme === 'dark' ? darkTheme : lightTheme

  useEffect(() => {
    const root = window.document.documentElement
    
    // Add transition class for smooth theme switching
    root.style.setProperty('--theme-transition', 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)')
    
    // Apply theme classes
    root.classList.remove('light', 'dark')
    root.classList.add(theme)
    
    // Save to localStorage
    localStorage.setItem('theme', theme)
    
    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem('theme')) {
        setTheme(e.matches ? 'dark' : 'light')
      }
    }
    
    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [theme])

  const toggleTheme = () => {
    setIsTransitioning(true)
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
    
    // Reset transition state after animation
    setTimeout(() => setIsTransitioning(false), 300)
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, themeTokens, isTransitioning }}>
      <motion.div
        key={theme}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        className="min-h-screen transition-colors duration-300"
      >
        {children}
      </motion.div>
    </ThemeContext.Provider>
  )
}