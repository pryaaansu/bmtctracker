import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import kn from './locales/kn.json'

// Language configuration with RTL support
export const languages = {
  en: {
    name: 'English',
    nativeName: 'English',
    dir: 'ltr' as const,
    flag: '🇺🇸'
  },
  kn: {
    name: 'Kannada',
    nativeName: 'ಕನ್ನಡ',
    dir: 'ltr' as const, // Kannada is LTR
    flag: '🇮🇳'
  }
} as const

export type LanguageCode = keyof typeof languages

// Get language from localStorage or browser preference
const getInitialLanguage = (): LanguageCode => {
  const stored = localStorage.getItem('bmtc-language') as LanguageCode
  if (stored && stored in languages) {
    return stored
  }
  
  // Check browser language
  const browserLang = navigator.language.split('-')[0] as LanguageCode
  if (browserLang in languages) {
    return browserLang
  }
  
  return 'en'
}

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      kn: { translation: kn }
    },
    lng: getInitialLanguage(),
    fallbackLng: 'en',
    debug: process.env.NODE_ENV === 'development',
    interpolation: {
      escapeValue: false
    },
    react: {
      useSuspense: false
    }
  })

// Save language preference when it changes
i18n.on('languageChanged', (lng: string) => {
  localStorage.setItem('bmtc-language', lng)
  
  // Update document direction and lang attribute
  const language = languages[lng as LanguageCode]
  if (language) {
    document.documentElement.dir = language.dir
    document.documentElement.lang = lng
  }
})

// Set initial document attributes
const initialLang = i18n.language as LanguageCode
const initialLanguage = languages[initialLang]
if (initialLanguage) {
  document.documentElement.dir = initialLanguage.dir
  document.documentElement.lang = initialLang
}

export default i18n