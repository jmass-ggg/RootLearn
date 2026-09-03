import React from 'react';

/**
 * Button Component
 * 
 * A versatile button component with multiple variants, sizes, and states.
 * Follows the RootLearn design system with consistent styling and accessibility.
 * 
 * @example
 * // Primary action button (default)
 * <Button variant="primary" onClick={handleSubmit}>
 *   Submit Answer
 * </Button>
 * 
 * @example
 * // Secondary action button
 * <Button variant="secondary" onClick={handleCancel}>
 *   Cancel
 * </Button>
 * 
 * @example
 * // High-emphasis lime button
 * <Button variant="lime" size="lg" onClick={handleStartLearning}>
 *   Start Guided Learning
 * </Button>
 * 
 * @example
 * // Ghost button for subtle actions
 * <Button variant="ghost" size="sm" onClick={handleEdit}>
 *   Edit
 * </Button>
 * 
 * @example
 * // Loading state
 * <Button variant="primary" isLoading={isSubmitting}>
 *   Submitting...
 * </Button>
 * 
 * @example
 * // Form submit button
 * <Button type="submit" isDisabled={!isValid}>
 *   Create Session
 * </Button>
 */
export interface ButtonProps {
  /**
   * Visual style variant of the button
   * 
   * - `primary`: Blue background, white text - for primary actions
   * - `secondary`: White background, blue border - for secondary actions
   * - `ghost`: Transparent background, blue text - for tertiary actions
   * - `lime`: Lime background, dark text - for high-emphasis moments
   * 
   * @default 'primary'
   */
  variant?: 'primary' | 'secondary' | 'ghost' | 'lime';
  
  /**
   * Size of the button
   * 
   * - `sm`: Small (compact UI elements)
   * - `md`: Medium (default, most buttons)
   * - `lg`: Large (primary CTAs, hero sections)
   * 
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg';
  
  /**
   * Shows a spinner and disables the button
   * Use during async operations
   * 
   * @default false
   */
  isLoading?: boolean;
  
  /**
   * Disables the button and reduces opacity
   * Use when action is not available
   * 
   * @default false
   */
  isDisabled?: boolean;
  
  /**
   * Click handler for the button
   */
  onClick?: () => void;
  
  /**
   * HTML button type attribute
   * 
   * @default 'button'
   */
  type?: 'button' | 'submit' | 'reset';
  
  /**
   * Button content (text, icons, or both)
   */
  children: React.ReactNode;
  
  /**
   * Additional CSS classes to apply
   */
  className?: string;
}

/**
 * Button Component Implementation
 * 
 * Renders a styled button with consistent design system tokens.
 * Handles loading and disabled states automatically.
 * Includes keyboard accessibility and ARIA attributes.
 */
export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  isDisabled = false,
  onClick,
  type = 'button',
  children,
  className = '',
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-offset-2';
  
  const variantStyles = {
    primary: 'bg-brand-blue text-text-inverse hover:bg-blue-600 focus:ring-brand-blue focus-visible:ring-brand-blue',
    secondary: 'bg-bg-card text-brand-blue border-2 border-brand-blue hover:bg-blue-50 focus:ring-brand-blue focus-visible:ring-brand-blue',
    ghost: 'bg-transparent text-brand-blue hover:bg-blue-50 focus:ring-brand-blue focus-visible:ring-brand-blue',
    lime: 'bg-brand-lime text-text-heading hover:bg-lime-400 focus:ring-brand-lime focus-visible:ring-brand-lime',
  };
  
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm rounded-md gap-1.5',
    md: 'px-4 py-2 text-base rounded-lg gap-2',
    lg: 'px-6 py-3 text-lg rounded-xl gap-2.5',
  };
  
  const disabled = isDisabled || isLoading;
  
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      aria-disabled={disabled}
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {isLoading && (
        <svg
          className="animate-spin h-4 w-4"
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
      )}
      {children}
    </button>
  );
};
