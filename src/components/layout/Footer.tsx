import React from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { fadeUpVariants } from '../../design-system/animations';

const Footer: React.FC = () => {
  const { t } = useTranslation();

  return (
    <motion.footer
      className="bg-white dark:bg-neutral-800 border-t border-neutral-200 dark:border-neutral-700"
      variants={fadeUpVariants}
      initial="hidden"
      animate="visible"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          {/* Logo and Description */}
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 17a1 1 0 102 0 1 1 0 00-2 0zM12 17a1 1 0 102 0 1 1 0 00-2 0zM16 17a1 1 0 102 0 1 1 0 00-2 0zM1.946 9.315c-.522-.174-.527-.455.01-.634l19.087-6.362c.529-.176.832.12.684.638l-5.454 19.086c-.15.529-.455.547-.679.045L12 14l6-8-8 6-8.054-2.685z" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                BMTC Transport Tracker
              </h3>
              <p className="text-xs text-neutral-500 dark:text-neutral-400">
                Real-time public transport tracking
              </p>
            </div>
          </div>

          {/* Links */}
          <div className="flex items-center space-x-6">
            <motion.a
              href="/privacy"
              className="text-sm text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors duration-200"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Privacy Policy
            </motion.a>
            <motion.a
              href="/terms"
              className="text-sm text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors duration-200"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Terms of Service
            </motion.a>
            <motion.a
              href="/support"
              className="text-sm text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors duration-200"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Support
            </motion.a>
          </div>

          {/* Copyright */}
          <div className="text-xs text-neutral-500 dark:text-neutral-400 text-center md:text-right">
            <p>© 2024 BMTC Transport Tracker</p>
            <p>Built for Government Hackathon</p>
          </div>
        </div>

        {/* Additional Info */}
        <motion.div
          className="mt-6 pt-6 border-t border-neutral-200 dark:border-neutral-700"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex flex-col sm:flex-row justify-between items-center space-y-2 sm:space-y-0">
            <div className="flex items-center space-x-4 text-xs text-neutral-500 dark:text-neutral-400">
              <span className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
                <span>System Status: Online</span>
              </span>
              <span>Last Updated: {new Date().toLocaleTimeString()}</span>
            </div>
            
            <div className="flex items-center space-x-3">
              <span className="text-xs text-neutral-500 dark:text-neutral-400">
                Powered by:
              </span>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-medium text-neutral-700 dark:text-neutral-300">React</span>
                <span className="text-neutral-300 dark:text-neutral-600">•</span>
                <span className="text-xs font-medium text-neutral-700 dark:text-neutral-300">FastAPI</span>
                <span className="text-neutral-300 dark:text-neutral-600">•</span>
                <span className="text-xs font-medium text-neutral-700 dark:text-neutral-300">WebSocket</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.footer>
  );
};

export default Footer;