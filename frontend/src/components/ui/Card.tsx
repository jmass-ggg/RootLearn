import React from 'react';
import { spacing } from '@/theme/tokens';

export interface CardProps {
  variant?: 'default' | 'elevated' | 'navy';
  padding?: keyof typeof spacing;
  className?: string;
  children: React.ReactNode;
  role?: string;
}

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
