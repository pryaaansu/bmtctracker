import { useTranslation } from 'react-i18next'
import { languages, type LanguageCode } from '../i18n/config'

export const useI18n = () => {
  const { t, i18n } = useTranslation()
  
  const currentLang = i18n.language as LanguageCode
  const currentLanguage = languages[currentLang]
  
  const changeLanguage = (langCode: LanguageCode) => {
    i18n.changeLanguage(langCode)
  }
  
  const toggleLanguage = () => {
    const newLang = currentLang === 'en' ? 'kn' : 'en'
    changeLanguage(newLang)
  }
  
  const isRTL = currentLanguage?.dir === 'rtl'
  
  // Format numbers according to locale
  const formatNumber = (num: number) => {
    return new Intl.NumberFormat(currentLang === 'kn' ? 'kn-IN' : 'en-IN').format(num)
  }
  
  // Format dates according to locale
  const formatDate = (date: Date, options?: Intl.DateTimeFormatOptions) => {
    const locale = currentLang === 'kn' ? 'kn-IN' : 'en-IN'
    return new Intl.DateTimeFormat(locale, options).format(date)
  }
  
  // Format relative time (e.g., "2 minutes ago")
  const formatRelativeTime = (date: Date) => {
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (diffInSeconds < 60) {
      return t('notifications.justNow')
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60)
      return t('notifications.minutesAgo', { count: minutes })
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600)
      return t('notifications.hoursAgo', { count: hours })
    } else {
      const days = Math.floor(diffInSeconds / 86400)
      return t('notifications.daysAgo', { count: days })
    }
  }
  
  return {
    t,
    i18n,
    currentLang,
    currentLanguage,
    changeLanguage,
    toggleLanguage,
    isRTL,
    formatNumber,
    formatDate,
    formatRelativeTime,
    availableLanguages: languages
  }
}

export default useI18n