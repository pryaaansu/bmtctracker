import { useState, useCallback } from 'react';
import { ToastProps } from '../components/ui/Toast';

interface ToastOptions {
  type?: ToastProps['type'];
  title?: string;
  duration?: number;
  action?: ToastProps['action'];
}

interface UseToastReturn {
  toasts: ToastProps[];
  showToast: (message: string, options?: ToastOptions) => string;
  hideToast: (id: string) => void;
  clearAllToasts: () => void;
}

let toastId = 0;

export const useToast = (): UseToastReturn => {
  const [toasts, setToasts] = useState<ToastProps[]>([]);

  const showToast = useCallback((message: string, options: ToastOptions = {}): string => {
    const id = `toast-${++toastId}`;
    
    const newToast: ToastProps = {
      id,
      message,
      type: options.type || 'info',
      title: options.title,
      duration: options.duration ?? 5000,
      action: options.action,
      onClose: (toastId: string) => {
        setToasts(prev => prev.filter(toast => toast.id !== toastId));
      },
    };

    setToasts(prev => [...prev, newToast]);
    return id;
  }, []);

  const hideToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const clearAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  return {
    toasts,
    showToast,
    hideToast,
    clearAllToasts,
  };
};

// Convenience methods
export const useToastHelpers = () => {
  const { showToast } = useToast();

  return {
    showSuccess: (message: string, options?: Omit<ToastOptions, 'type'>) =>
      showToast(message, { ...options, type: 'success' }),
    
    showError: (message: string, options?: Omit<ToastOptions, 'type'>) =>
      showToast(message, { ...options, type: 'error' }),
    
    showWarning: (message: string, options?: Omit<ToastOptions, 'type'>) =>
      showToast(message, { ...options, type: 'warning' }),
    
    showInfo: (message: string, options?: Omit<ToastOptions, 'type'>) =>
      showToast(message, { ...options, type: 'info' }),
  };
};