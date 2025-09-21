import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';
import { useAuth } from '../../contexts/AuthContext';
import { slideLeftVariants, overlayVariants } from '../../design-system/animations';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user } = useAuth();
  const location = useLocation();

  // Determine if we should show sidebar based on route and user role
  const shouldShowSidebar = user && (
    location.pathname.startsWith('/admin') || 
    location.pathname.startsWith('/driver')
  );

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900 transition-colors duration-300">
      {/* Header */}
      <Header 
        onMenuClick={shouldShowSidebar ? toggleSidebar : undefined}
        showMenuButton={shouldShowSidebar}
      />

      <div className="flex">
        {/* Sidebar */}
        {shouldShowSidebar && (
          <>
            {/* Desktop Sidebar */}
            <motion.aside
              className="hidden lg:flex lg:flex-shrink-0"
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 256, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
            >
              <div className="w-64">
                <Sidebar onClose={closeSidebar} />
              </div>
            </motion.aside>

            {/* Mobile Sidebar Overlay */}
            <AnimatePresence>
              {sidebarOpen && (
                <>
                  <motion.div
                    className="fixed inset-0 z-40 lg:hidden"
                    variants={overlayVariants}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                    onClick={closeSidebar}
                  />
                  <motion.aside
                    className="fixed inset-y-0 left-0 z-50 w-64 lg:hidden"
                    variants={slideLeftVariants}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                  >
                    <Sidebar onClose={closeSidebar} />
                  </motion.aside>
                </>
              )}
            </AnimatePresence>
          </>
        )}

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0">
          <motion.main
            className={`
              flex-1 pt-16
              ${shouldShowSidebar ? 'lg:pl-0' : ''}
            `}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            {children}
          </motion.main>

          {/* Footer */}
          <Footer />
        </div>
      </div>
    </div>
  );
};

export default Layout;