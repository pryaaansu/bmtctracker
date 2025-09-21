import React, { forwardRef } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { buttonVariants } from '../../design-system/animations';
import { useAccessibility } from '../../contexts/AccessibilityContext';

export interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'size'> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children: React.ReactNode;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  announceOnClick?: string;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      disabled = false,
      fullWidth = false,
      leftIcon,
      rightIcon,
      children,
      className = '',
      ariaLabel,
      ariaDescribedBy,
      announceOnClick,
      onClick,
      ...props
    },
    ref
  ) => {
    const { settings, announceToScreenReader } = useAccessibility();
    const baseClasses = [
      'inline-flex items-center justify-center',
      'font-medium rounded-lg',
      'transition-all duration-200',
      'focus:outline-none focus:ring-2 focus:ring-offset-2',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      'relative overflow-hidden',
    ];

    const variantClasses = {
      primary: [
        'bg-primary-600 hover:bg-primary-700 active:bg-primary-800',
        'text-white',
        'focus:ring-primary-500',
        'shadow-sm hover:shadow-md',
      ],
      secondary: [
        'bg-secondary-600 hover:bg-secondary-700 active:bg-secondary-800',
        'text-white',
        'focus:ring-secondary-500',
        'shadow-sm hover:shadow-md',
      ],
      outline: [
        'border-2 border-primary-600 hover:border-primary-700',
        'text-primary-600 hover:text-primary-700 hover:bg-primary-50',
        'dark:text-primary-400 dark:border-primary-400 dark:hover:bg-primary-900/20',
        'focus:ring-primary-500',
      ],
      ghost: [
        'text-neutral-700 hover:text-neutral-900 hover:bg-neutral-100',
        'dark:text-neutral-300 dark:hover:text-neutral-100 dark:hover:bg-neutral-800',
        'focus:ring-neutral-500',
      ],
      danger: [
        'bg-error-600 hover:bg-error-700 active:bg-error-800',
        'text-white',
        'focus:ring-error-500',
        'shadow-sm hover:shadow-md',
      ],
      success: [
        'bg-success-600 hover:bg-success-700 active:bg-success-800',
        'text-white',
        'focus:ring-success-500',
        'shadow-sm hover:shadow-md',
      ],
    };

    const sizeClasses = {
      sm: ['px-3 py-1.5 text-sm', 'gap-1.5'],
      md: ['px-4 py-2 text-base', 'gap-2'],
      lg: ['px-6 py-3 text-lg', 'gap-2.5'],
      xl: ['px-8 py-4 text-xl', 'gap-3'],
    };

    const widthClasses = fullWidth ? ['w-full'] : [];

    const allClasses = [
      ...baseClasses,
      ...variantClasses[variant],
      ...sizeClasses[size],
      ...widthClasses,
      className,
    ].join(' ');

    const isDisabled = disabled || loading;

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (announceOnClick) {
        announceToScreenReader(announceOnClick)
      }
      onClick?.(e)
    }

    // Disable animations if reduced motion is preferred
    const shouldAnimate = !settings.reducedMotion

    return (
      <motion.button
        ref={ref}
        className={allClasses}
        disabled={isDisabled}
        variants={shouldAnimate ? buttonVariants : undefined}
        initial={shouldAnimate ? "idle" : undefined}
        whileHover={!isDisabled && shouldAnimate ? "hover" : "idle"}
        whileTap={!isDisabled && shouldAnimate ? "tap" : "idle"}
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        aria-busy={loading}
        onClick={handleClick}
        {...props}
      >
        {/* Ripple Effect */}
        {shouldAnimate && (
          <motion.div
            className="absolute inset-0 bg-white/20 rounded-lg"
            initial={{ scale: 0, opacity: 0 }}
            whileTap={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.1 }}
          />
        )}
        
        {/* Loading Spinner */}
        {loading && (
          <motion.div
            className="absolute inset-0 flex items-center justify-center"
            initial={shouldAnimate ? { opacity: 0 } : { opacity: 1 }}
            animate={{ opacity: 1 }}
            transition={shouldAnimate ? { duration: 0.2 } : { duration: 0 }}
            role="status"
            aria-label="Loading"
          >
            <motion.div
              className="w-5 h-5 border-2 border-current border-t-transparent rounded-full"
              animate={shouldAnimate ? { rotate: 360 } : {}}
              transition={shouldAnimate ? { duration: 1, repeat: Infinity, ease: 'linear' } : {}}
            />
          </motion.div>
        )}
        
        {/* Content */}
        <motion.div
          className="flex items-center gap-inherit"
          animate={{ opacity: loading ? 0 : 1 }}
          transition={shouldAnimate ? { duration: 0.2 } : { duration: 0 }}
        >
          {leftIcon && (
            <motion.span
              className="flex-shrink-0"
              initial={shouldAnimate ? { scale: 0.8, opacity: 0 } : { scale: 1, opacity: 1 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={shouldAnimate ? { delay: 0.1 } : { duration: 0 }}
              aria-hidden="true"
            >
              {leftIcon}
            </motion.span>
          )}
          
          <span>{children}</span>
          
          {rightIcon && (
            <motion.span
              className="flex-shrink-0"
              initial={shouldAnimate ? { scale: 0.8, opacity: 0 } : { scale: 1, opacity: 1 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={shouldAnimate ? { delay: 0.1 } : { duration: 0 }}
              aria-hidden="true"
            >
              {rightIcon}
            </motion.span>
          )}
        </motion.div>
      </motion.button>
    );
  }
);

Button.displayName = 'Button';

export default Button;