import React from 'react';
import { spacing } from '@/theme/tokens';

/**
 * Card Component
 * 
 * A flexible container component for grouping related content.
 * Provides consistent styling with white backgrounds, borders, and optional elevation.
 * 
 * @example
 * // Default card with standard padding
 * <Card>
 *   <h2>Session Details</h2>
 *   <p>Started 5 minutes ago</p>
 * </Card>
 * 
 * @example
 * // Elevated card with shadow
 * <Card variant="elevated">
 *   <h3>Root Gap Found</h3>
 *   <p>Functions and recursion</p>
 * </Card>
 * 
 * @example
 * // Navy card for high-contrast sections
 * <Card variant="navy" padding="xl">
 *   <h1 className="text-text-inverse">Welcome to RootLearn</h1>
 * </Card>
 * 
 * @example
 * // Custom padding
 * <Card padding="md">
 *   <div>Compact content</div>
 * </Card>
 * 
 * @example
 * // With custom classes
 * <Card className="max-w-2xl mx-auto">
 *   <p>Centered card with max width</p>
 * </Card>
 */
export interface CardProps {
  /**
   * Visual style variant of the card
   * 
   * - `default`: White background, gray border - standard content cards
   * - `elevated`: White background with subtle shadow - emphasized content
   * - `navy`: Dark navy background with inverse text - hero sections, highlights
   * 
   * @default 'default'
   */
  variant?: 'default' | 'elevated' | 'navy';
  
  /**
   * Internal padding size using design system spacing scale
   * 
   * Common values:
   * - `sm` (8px): Compact UI elements
   * - `md` (16px): Medium content
   * - `lg` (24px): Standard cards (default)
   * - `xl` (32px): Spacious layouts
   * 
   * @default 'lg'
   */
  padding?: keyof typeof spacing;
  
  /**
   * Additional CSS classes to apply
   */
  className?: string;
  
  /**
   * Card content
   */
  children: React.ReactNode;
  
  /**
   * ARIA role for accessibility
   * Use when the card represents a specific semantic element
   * 
   * @example role="article"
   * @example role="region"
   */
  role?: string;
}

/**
 * Card Component Implementation
 * 
 * Renders a styled container with consistent border radius, spacing, and optional shadows.
 * Uses design system tokens for all styling values.
 */
export const Card: React.FC<CardProps> = ({
  variant = 'default',
  padding = 'lg',
  className = '',
  children,
  role,
}) => {
  const baseStyles = 'rounded-xl';
  
  const variantStyles = {
    default: 'bg-bg-card border border-border-default',
    elevated: 'bg-bg-card border border-border-default shadow-subtle',
    navy: 'bg-brand-navy text-text-inverse',
  };
  
  const paddingMap: Record<keyof typeof spacing, string> = {
    xs: 'p-1',
    sm: 'p-2',
    md: 'p-4',
    lg: 'p-6',
    xl: 'p-8',
    '2xl': 'p-12',
    '3xl': 'p-16',
  };
  
  const paddingClass = paddingMap[padding];
  
  return (
    <div className={`${baseStyles} ${variantStyles[variant]} ${paddingClass} ${className}`} role={role}>
      {children}
    </div>
  );
};
