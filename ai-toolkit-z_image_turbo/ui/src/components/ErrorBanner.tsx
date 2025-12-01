'use client';

import { X, AlertCircle } from 'lucide-react';
import { useEffect } from 'react';

interface ErrorBannerProps {
  error: {
    message?: string;
    details?: string;
    suggestion?: string;
  } | null;
  onDismiss?: () => void;
  autoDismiss?: boolean;
  autoDismissDelay?: number;
}

export default function ErrorBanner({ 
  error, 
  onDismiss, 
  autoDismiss = false,
  autoDismissDelay = 10000 
}: ErrorBannerProps) {
  useEffect(() => {
    if (autoDismiss && error && onDismiss) {
      const timer = setTimeout(() => {
        onDismiss();
      }, autoDismissDelay);
      return () => clearTimeout(timer);
    }
  }, [error, autoDismiss, autoDismissDelay, onDismiss]);

  if (!error) return null;

  return (
    <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
      <div className="flex items-start">
        <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5 mr-3 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-red-800 dark:text-red-300 mb-1">
            {error.message || 'Error'}
          </h3>
          {error.details && (
            <p className="text-sm text-red-700 dark:text-red-400 mb-2">
              {error.details}
            </p>
          )}
          {error.suggestion && (
            <p className="text-sm text-red-600 dark:text-red-500 italic">
              💡 {error.suggestion}
            </p>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-4 text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 flex-shrink-0"
            aria-label="Dismiss error"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  );
}

