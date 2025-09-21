import React, { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { debounce } from 'lodash'

interface SearchSuggestion {
  type: 'route' | 'stop'
  id: number
  title: string
  title_kannada?: string
  subtitle: string
  route_number?: string
  latitude?: number
  longitude?: number
  distance_km?: number
  icon: string
  score: number
}

interface SearchBarProps {
  placeholder?: string
  onSelect?: (suggestion: SearchSuggestion) => void
  onSearch?: (query: string) => void
  className?: string
  showHistory?: boolean
  userLocation?: { lat: number; lng: number } | null
}

const SearchBar: React.FC<SearchBarProps> = ({
  placeholder,
  onSelect,
  onSearch,
  className = '',
  showHistory = true,
  userLocation
}) => {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [searchHistory, setSearchHistory] = useState<SearchSuggestion[]>([])
  
  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)
  
  // Load search history from localStorage
  useEffect(() => {
    if (showHistory) {
      const saved = localStorage.getItem('bmtc-search-history')
      if (saved) {
        try {
          setSearchHistory(JSON.parse(saved))
        } catch (error) {
          console.error('Failed to load search history:', error)
        }
      }
    }
  }, [showHistory])
  
  // Save search history to localStorage
  const saveToHistory = useCallback((suggestion: SearchSuggestion) => {
    if (!showHistory) return
    
    setSearchHistory(prev => {
      // Remove if already exists
      const filtered = prev.filter(item => 
        !(item.type === suggestion.type && item.id === suggestion.id)
      )
      // Add to beginning
      const updated = [suggestion, ...filtered].slice(0, 10) // Keep only 10 items
      localStorage.setItem('bmtc-search-history', JSON.stringify(updated))
      return updated
    })
  }, [showHistory])
  
  // Debounced search function
  const debouncedSearch = useCallback(
    debounce(async (searchQuery: string) => {
      if (searchQuery.length < 1) {
        setSuggestions([])
        setIsLoading(false)
        return
      }
      
      try {
        const params = new URLSearchParams({
          q: searchQuery,
          limit: '8'
        })
        
        if (userLocation) {
          params.append('lat', userLocation.lat.toString())
          params.append('lng', userLocation.lng.toString())
        }
        
        const response = await fetch(`/api/v1/search/autocomplete?${params}`)
        if (!response.ok) throw new Error('Search failed')
        
        const data = await response.json()
        setSuggestions(data.suggestions || [])
      } catch (error) {
        console.error('Search error:', error)
        setSuggestions([])
      } finally {
        setIsLoading(false)
      }
    }, 300),
    [userLocation]
  )
  
  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setQuery(value)
    setSelectedIndex(-1)
    
    if (value.trim()) {
      setIsLoading(true)
      debouncedSearch(value.trim())
    } else {
      setSuggestions([])
      setIsLoading(false)
    }
  }
  
  // Handle suggestion selection
  const handleSelect = (suggestion: SearchSuggestion) => {
    setQuery(suggestion.title)
    setIsOpen(false)
    setSelectedIndex(-1)
    saveToHistory(suggestion)
    onSelect?.(suggestion)
  }
  
  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    const currentSuggestions = query.trim() ? suggestions : searchHistory
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => 
          prev < currentSuggestions.length - 1 ? prev + 1 : 0
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : currentSuggestions.length - 1
        )
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && currentSuggestions[selectedIndex]) {
          handleSelect(currentSuggestions[selectedIndex])
        } else if (query.trim()) {
          onSearch?.(query.trim())
          setIsOpen(false)
        }
        break
      case 'Escape':
        setIsOpen(false)
        setSelectedIndex(-1)
        inputRef.current?.blur()
        break
    }
  }
  
  // Handle focus
  const handleFocus = () => {
    setIsOpen(true)
  }
  
  // Handle blur
  const handleBlur = (_e: React.FocusEvent) => {
    // Delay closing to allow clicking on suggestions
    setTimeout(() => {
      if (!suggestionsRef.current?.contains(document.activeElement)) {
        setIsOpen(false)
        setSelectedIndex(-1)
      }
    }, 150)
  }
  
  // Clear search
  const handleClear = () => {
    setQuery('')
    setSuggestions([])
    setIsOpen(false)
    setSelectedIndex(-1)
    inputRef.current?.focus()
  }
  
  // Get icon for suggestion type
  const getIcon = (suggestion: SearchSuggestion) => {
    switch (suggestion.type) {
      case 'route':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
        )
      case 'stop':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        )
      default:
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        )
    }
  }
  
  const currentSuggestions = query.trim() ? suggestions : (showHistory ? searchHistory : [])
  const showSuggestions = isOpen && (currentSuggestions.length > 0 || isLoading)
  
  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder || t('common.search')}
          className="input-field pl-10 pr-10"
          autoComplete="off"
        />
        
        {/* Search icon */}
        <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
          {isLoading ? (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-4 h-4 text-gray-400"
            >
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </motion.div>
          ) : (
            <svg
              className="w-4 h-4 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          )}
        </div>
        
        {/* Clear button */}
        {query && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
      
      {/* Suggestions dropdown */}
      <AnimatePresence>
        {showSuggestions && (
          <motion.div
            ref={suggestionsRef}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto"
          >
            {!query.trim() && showHistory && searchHistory.length > 0 && (
              <div className="px-3 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700">
                {t('search.recentSearches')}
              </div>
            )}
            
            {currentSuggestions.map((suggestion, index) => (
              <motion.button
                key={`${suggestion.type}-${suggestion.id}`}
                onClick={() => handleSelect(suggestion)}
                className={`w-full px-3 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-3 ${
                  index === selectedIndex ? 'bg-gray-50 dark:bg-gray-700' : ''
                }`}
                whileHover={{ backgroundColor: 'rgba(0, 0, 0, 0.05)' }}
              >
                <div className={`flex-shrink-0 p-2 rounded-lg ${
                  suggestion.type === 'route' 
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                    : 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                }`}>
                  {getIcon(suggestion)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {suggestion.title}
                    </p>
                    {suggestion.title_kannada && (
                      <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                        ({suggestion.title_kannada})
                      </p>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {suggestion.subtitle}
                  </p>
                </div>
                
                {suggestion.distance_km !== undefined && (
                  <div className="flex-shrink-0 text-xs text-gray-400">
                    {suggestion.distance_km < 1 
                      ? `${Math.round(suggestion.distance_km * 1000)}m`
                      : `${suggestion.distance_km.toFixed(1)}km`
                    }
                  </div>
                )}
              </motion.button>
            ))}
            
            {isLoading && (
              <div className="px-3 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                <motion.div
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  {t('search.searching')}...
                </motion.div>
              </div>
            )}
            
            {!isLoading && currentSuggestions.length === 0 && query.trim() && (
              <div className="px-3 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                {t('search.noResults')}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default SearchBar