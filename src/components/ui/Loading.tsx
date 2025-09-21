import React from 'react';
import { motion } from 'framer-motion';
import { spinVariants, pulseVariants, bounceVariants } from '../../design-system/animations';

export interface LoadingProps {
  type?: 'spinner' | 'dots' | 'pulse' | 'skeleton';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  color?: 'primary' | 'secondary' | 'neutral';
  text?: string;
  fullScreen?: boolean;
  className?: string;
}

const Loading: React.FC<LoadingProps> = ({
  type = 'spinner',
  size = 'md',
  color = 'primary',
  text,
  fullScreen = false,
  className = '',
}) => {
  const colorClasses = {
    primary: 'text-primary-600',
    secondary: 'text-secondary-600',
    neutral: 'text-neutral-600',
  };

  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
  };

  const containerClasses = fullScreen
    ? 'fixed inset-0 flex items-center justify-center bg-white/80 dark:bg-neutral-900/80 backdrop-blur-sm z-50'
    : 'flex items-center justify-center';

  const renderSpinner = () => (
    <motion.div
      className={`
        border-2 border-current border-t-transparent rounded-full
        ${sizeClasses[size]} ${colorClasses[color]}
      `}
      variants={spinVariants}
      animate="animate"
    />
  );

  const renderDots = () => (
    <div className="flex space-x-1">
      {[0, 1, 2].map((index) => (
        <motion.div
          key={index}
          className={`
            rounded-full bg-current
            ${size === 'sm' ? 'w-2 h-2' : size === 'md' ? 'w-3 h-3' : size === 'lg' ? 'w-4 h-4' : 'w-5 h-5'}
            ${colorClasses[color]}
          `}
          variants={bounceVariants}
          animate="animate"
          transition={{
            delay: index * 0.1,
            duration: 0.6,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  );

  const renderPulse = () => (
    <motion.div
      className={`
        rounded-full bg-current
        ${sizeClasses[size]} ${colorClasses[color]}
      `}
      variants={pulseVariants}
      animate="animate"
    />
  );

  const renderSkeleton = () => (
    <div className="animate-pulse space-y-3">
      <div className="h-4 bg-neutral-300 dark:bg-neutral-600 rounded w-3/4"></div>
      <div className="space-y-2">
        <div className="h-3 bg-neutral-300 dark:bg-neutral-600 rounded"></div>
        <div className="h-3 bg-neutral-300 dark:bg-neutral-600 rounded w-5/6"></div>
      </div>
    </div>
  );

  const renderLoadingContent = () => {
    switch (type) {
      case 'dots':
        return renderDots();
      case 'pulse':
        return renderPulse();
      case 'skeleton':
        return renderSkeleton();
      default:
        return renderSpinner();
    }
  };

  return (
    <motion.div
      className={`${containerClasses} ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex flex-col items-center space-y-3">
        {renderLoadingContent()}
        {text && (
          <motion.p
            className={`
              ${textSizeClasses[size]} ${colorClasses[color]}
              font-medium text-center
            `}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            {text}
          </motion.p>
        )}
      </div>
    </motion.div>
  );
};

// Skeleton Components for specific use cases
export const SkeletonText: React.FC<{
  lines?: number;
  className?: string;
}> = ({ lines = 3, className = '' }) => (
  <div className={`animate-pulse space-y-2 ${className}`}>
    {Array.from({ length: lines }).map((_, index) => (
      <div
        key={index}
        className={`
          h-3 bg-neutral-300 dark:bg-neutral-600 rounded
          ${index === lines - 1 ? 'w-3/4' : 'w-full'}
        `}
      />
    ))}
  </div>
);

export const SkeletonCard: React.FC<{
  className?: string;
}> = ({ className = '' }) => (
  <div className={`animate-pulse ${className}`}>
    <div className="rounded-xl bg-neutral-300 dark:bg-neutral-600 h-48 w-full mb-4"></div>
    <div className="space-y-3">
      <div className="h-4 bg-neutral-300 dark:bg-neutral-600 rounded w-3/4"></div>
      <div className="space-y-2">
        <div className="h-3 bg-neutral-300 dark:bg-neutral-600 rounded"></div>
        <div className="h-3 bg-neutral-300 dark:bg-neutral-600 rounded w-5/6"></div>
      </div>
    </div>
  </div>
);

export const SkeletonAvatar: React.FC<{
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}> = ({ size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  };

  return (
    <div
      className={`
        animate-pulse rounded-full bg-neutral-300 dark:bg-neutral-600
        ${sizeClasses[size]} ${className}
      `}
    />
  );
};

export default Loading;