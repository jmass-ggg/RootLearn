import React from 'react';
import { Button } from './Button';

export interface StateDisplayProps {
  variant: 'loading' | 'empty' | 'error';
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const StateDisplay: React.FC<StateDisplayProps> = ({
  variant,
  title,
  description,
  action,
}) => {
  const renderIcon = () => {
    switch (variant) {
      case 'loading':
        return (
          <svg
            className="animate-spin h-12 w-12 text-brand-blue"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        );
      case 'empty':
        return (
          <svg
            className="h-12 w-12 text-text-muted"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
        );
      case 'error':
        return (
          <svg
            className="h-12 w-12 text-mastery-weak"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        );
    }
  };

  // Determine aria-live politeness based on variant
  const ariaLive = variant === 'error' ? 'assertive' : 'polite';

  return (
    <div 
      className="flex flex-col items-center justify-center text-center py-12 px-6"
      role={variant === 'error' ? 'alert' : 'status'}
      aria-live={ariaLive}
      aria-atomic="true"
    >
      <div className="mb-4">
        {renderIcon()}
      </div>
      <h2 className="text-xl font-semibold text-text-heading mb-2">
        {title}
      </h2>
      {description && (
        <p className="text-base text-text-body mb-6 max-w-md">
          {description}
        </p>
      )}
      {action && (
        <Button
          variant="primary"
          onClick={action.onClick}
          aria-label={action.label}
        >
          {action.label}
        </Button>
      )}
    </div>
  );
};
