import React, { forwardRef, useState } from 'react';
import { motion } from 'framer-motion';

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  error?: string;
  helperText?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'filled' | 'outlined';
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  loading?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      size = 'md',
      variant = 'default',
      leftIcon,
      rightIcon,
      loading = false,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    const [isFocused, setIsFocused] = useState(false);

    const baseClasses = [
      'w-full rounded-lg transition-all duration-200',
      'focus:outline-none focus:ring-2 focus:ring-offset-1',
      'disabled:opacity-50 disabled:cursor-not-allowed',
    ];

    const variantClasses = {
      default: [
        'border border-neutral-300 dark:border-neutral-600',
        'bg-white dark:bg-neutral-800',
        'text-neutral-900 dark:text-neutral-100',
        'placeholder-neutral-500 dark:placeholder-neutral-400',
        'focus:border-primary-500 focus:ring-primary-500',
        error ? 'border-error-500 focus:border-error-500 focus:ring-error-500' : '',
      ],
      filled: [
        'border-0 bg-neutral-100 dark:bg-neutral-700',
        'text-neutral-900 dark:text-neutral-100',
        'placeholder-neutral-500 dark:placeholder-neutral-400',
        'focus:bg-white dark:focus:bg-neutral-800',
        'focus:ring-primary-500',
        error ? 'bg-error-50 dark:bg-error-900/20 focus:ring-error-500' : '',
      ],
      outlined: [
        'border-2 border-neutral-300 dark:border-neutral-600',
        'bg-transparent',
        'text-neutral-900 dark:text-neutral-100',
        'placeholder-neutral-500 dark:placeholder-neutral-400',
        'focus:border-primary-500 focus:ring-primary-500',
        error ? 'border-error-500 focus:border-error-500 focus:ring-error-500' : '',
      ],
    };

    const sizeClasses = {
      sm: ['px-3 py-2 text-sm'],
      md: ['px-4 py-2.5 text-base'],
      lg: ['px-5 py-3 text-lg'],
    };

    const iconSizeClasses = {
      sm: 'w-4 h-4',
      md: 'w-5 h-5',
      lg: 'w-6 h-6',
    };

    const paddingWithIcons = {
      sm: {
        left: leftIcon ? 'pl-10' : '',
        right: rightIcon || loading ? 'pr-10' : '',
      },
      md: {
        left: leftIcon ? 'pl-12' : '',
        right: rightIcon || loading ? 'pr-12' : '',
      },
      lg: {
        left: leftIcon ? 'pl-14' : '',
        right: rightIcon || loading ? 'pr-14' : '',
      },
    };

    const inputClasses = [
      ...baseClasses,
      ...variantClasses[variant],
      ...sizeClasses[size],
      paddingWithIcons[size].left,
      paddingWithIcons[size].right,
      className,
    ].join(' ');

    return (
      <div className="w-full">
        {/* Label */}
        {label && (
          <motion.label
            className={`
              block text-sm font-medium mb-2
              ${error ? 'text-error-700 dark:text-error-400' : 'text-neutral-700 dark:text-neutral-300'}
            `}
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            {label}
          </motion.label>
        )}

        {/* Input Container */}
        <div className="relative">
          {/* Left Icon */}
          {leftIcon && (
            <motion.div
              className={`
                absolute left-3 top-1/2 transform -translate-y-1/2
                text-neutral-500 dark:text-neutral-400
                ${iconSizeClasses[size]}
              `}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
            >
              {leftIcon}
            </motion.div>
          )}

          {/* Input */}
          <motion.input
            ref={ref}
            className={inputClasses}
            disabled={disabled || loading}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            {...props}
          />

          {/* Right Icon or Loading */}
          {(rightIcon || loading) && (
            <motion.div
              className={`
                absolute right-3 top-1/2 transform -translate-y-1/2
                text-neutral-500 dark:text-neutral-400
                ${iconSizeClasses[size]}
              `}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
            >
              {loading ? (
                <motion.div
                  className={`border-2 border-current border-t-transparent rounded-full ${iconSizeClasses[size]}`}
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                />
              ) : (
                rightIcon
              )}
            </motion.div>
          )}

          {/* Focus Ring Animation */}
          <motion.div
            className={`
              absolute inset-0 rounded-lg pointer-events-none
              ${error ? 'ring-error-500' : 'ring-primary-500'}
            `}
            initial={{ scale: 1, opacity: 0 }}
            animate={{
              scale: isFocused ? 1.02 : 1,
              opacity: isFocused ? 0.1 : 0,
            }}
            transition={{ duration: 0.2 }}
          />
        </div>

        {/* Helper Text or Error */}
        {(error || helperText) && (
          <motion.p
            className={`
              mt-2 text-sm
              ${error ? 'text-error-600 dark:text-error-400' : 'text-neutral-600 dark:text-neutral-400'}
            `}
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            {error || helperText}
          </motion.p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;