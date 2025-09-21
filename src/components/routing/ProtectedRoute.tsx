import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { Loading } from '../ui';
import { fadeVariants } from '../../design-system/animations';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'passenger' | 'driver' | 'admin';
  requireAuth?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  requireAuth = true,
}) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  // Show loading while checking authentication
  if (isLoading) {
    return (
      <motion.div
        variants={fadeVariants}
        initial="hidden"
        animate="visible"
        className="min-h-screen flex items-center justify-center"
      >
        <Loading
          type="spinner"
          size="lg"
          text="Checking authentication..."
          color="primary"
        />
      </motion.div>
    );
  }

  // Redirect to login if authentication is required but user is not logged in
  if (requireAuth && !user) {
    return (
      <Navigate
        to="/login"
        state={{ from: location }}
        replace
      />
    );
  }

  // Check role-based access
  if (requiredRole && user?.role !== requiredRole) {
    // Redirect based on user role
    const redirectPath = user?.role === 'admin' 
      ? '/admin' 
      : user?.role === 'driver' 
        ? '/driver' 
        : '/';
    
    return <Navigate to={redirectPath} replace />;
  }

  return (
    <motion.div
      variants={fadeVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
    >
      {children}
    </motion.div>
  );
};

export default ProtectedRoute;