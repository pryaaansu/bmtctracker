import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'
import { AccessibilityProvider } from './contexts/AccessibilityContext'
import { ToastContainer, KeyboardNavigation } from './components/ui'
import { OfflineBanner } from './components/ui/ConnectivityIndicator'
import { useToast } from './hooks'
import ErrorBoundary from './components/routing/ErrorBoundary'
import ProtectedRoute from './components/routing/ProtectedRoute'
import PageTransition from './components/routing/PageTransition'
import Layout from './components/layout/Layout'
import MapView from './pages/MapView'
import AdminDashboard from './pages/AdminDashboard'
import DriverPortal from './pages/DriverPortal'
import AnalyticsDashboard from './pages/AnalyticsDashboard'
import Login from './pages/Login'
import { registerServiceWorker } from './utils/serviceWorker'
import './i18n/config' // Initialize i18n

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function AppContent() {
  const { toasts } = useToast()

  return (
    <ErrorBoundary>
      <KeyboardNavigation>
        <Layout>
          <main id="main-content" tabIndex={-1}>
            <PageTransition>
              <Routes>
                {/* Public Routes */}
                <Route path="/" element={<MapView />} />
                <Route path="/login" element={<Login />} />
                
                {/* Protected Routes */}
                <Route 
                  path="/admin/*" 
                  element={
                    <ProtectedRoute requiredRole="admin">
                      <AdminDashboard />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/driver/*" 
                  element={
                    <ProtectedRoute requiredRole="driver">
                      <DriverPortal />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/analytics" 
                  element={
                    <ProtectedRoute requiredRole="admin">
                      <AnalyticsDashboard />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Catch-all route */}
                <Route path="*" element={<MapView />} />
              </Routes>
            </PageTransition>
          </main>
        </Layout>
        
        {/* Toast Notifications */}
        <ToastContainer toasts={toasts} position="top-right" />
      </KeyboardNavigation>
    </ErrorBoundary>
  )
}

function App() {
  useEffect(() => {
    // Register service worker for PWA capabilities
    registerServiceWorker({
      onUpdate: (registration) => {
        console.log('New app version available');
        // Show update notification to user
        if (window.confirm('A new version is available. Reload to update?')) {
          window.location.reload();
        }
      },
      onSuccess: (registration) => {
        console.log('App is ready for offline use');
      },
      onOffline: () => {
        console.log('App is now offline');
      },
      onOnline: () => {
        console.log('App is back online');
      }
    });
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AccessibilityProvider>
          <AuthProvider>
            <Router>
              <OfflineBanner />
              <AppContent />
            </Router>
          </AuthProvider>
        </AccessibilityProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App