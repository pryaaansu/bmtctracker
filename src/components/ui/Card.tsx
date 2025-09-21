import React, { forwardRef } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cardVariants } from '../../design-system/animations';

export interface CardProps extends HTMLMotionProps<'div'> {
  variant?: 'default' | 'elevated' | 'outlined' | 'filled';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  interactive?: boolean;
  children: React.ReactNode;
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'default',
      padding = 'md',
      interactive = false,
      children,
      className = '',
      ...props
    },
    ref
  ) => {
    const baseClasses = [
      'rounded-xl',
      'transition-all duration-200',
      'bg-white dark:bg-neutral-800',
    ];

    const variantClasses = {
      default: [
        'shadow-sm',
        'border border-neutral-200 dark:border-neutral-700',
      ],
      elevated: [
        'shadow-medium',
        'border border-neutral-100 dark:border-neutral-700',
      ],
      outlined: [
        'border-2 border-neutral-300 dark:border-neutral-600',
        'shadow-none',
      ],
      filled: [
        'bg-neutral-50 dark:bg-neutral-700',
        'border border-neutral-200 dark:border-neutral-600',
        'shadow-none',
      ],
    };

    const paddingClasses = {
      none: [],
      sm: ['p-3'],
      md: ['p-4'],
      lg: ['p-6'],
      xl: ['p-8'],
    };

    const interactiveClasses = interactive
      ? [
          'cursor-pointer',
          'hover:shadow-lg hover:-translate-y-1',
          'active:translate-y-0 active:shadow-md',
        ]
      : [];

    const allClasses = [
      ...baseClasses,
      ...variantClasses[variant],
      ...paddingClasses[padding],
      ...interactiveClasses,
      className,
    ].join(' ');

    const motionProps = interactive
      ? {
          variants: cardVariants,
          initial: 'hidden',
          animate: 'visible',
          whileHover: 'hover',
          whileTap: 'tap',
        }
      : {
          variants: cardVariants,
          initial: 'hidden',
          animate: 'visible',
        };

    return (
      <motion.div
        ref={ref}
        className={allClasses}
        {...motionProps}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

Card.displayName = 'Card';

// Card Header Component
export interface CardHeaderProps {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  title,
  subtitle,
  action,
  children,
  className = '',
}) => {
  return (
    <motion.div
      className={`flex items-start justify-between mb-4 ${className}`}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
    >
      <div className="flex-1 min-w-0">
        {title && (
          <motion.h3
            className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 truncate"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            {title}
          </motion.h3>
        )}
        {subtitle && (
          <motion.p
            className="text-sm text-neutral-600 dark:text-neutral-400 mt-1"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            {subtitle}
          </motion.p>
        )}
        {children}
      </div>
      {action && (
        <motion.div
          className="flex-shrink-0 ml-4"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          {action}
        </motion.div>
      )}
    </motion.div>
  );
};

// Card Content Component
export interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export const CardContent: React.FC<CardContentProps> = ({
  children,
  className = '',
}) => {
  return (
    <motion.div
      className={`text-neutral-700 dark:text-neutral-300 ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.2 }}
    >
      {children}
    </motion.div>
  );
};

// Card Footer Component
export interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

export const CardFooter: React.FC<CardFooterProps> = ({
  children,
  className = '',
}) => {
  return (
    <motion.div
      className={`mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-700 ${className}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
    >
      {children}
    </motion.div>
  );
};

export default Card;