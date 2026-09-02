/**
 * Design System Tokens
 * 
 * Core design tokens for the RootLearn UI/UX redesign.
 * Includes colors, spacing, typography, and border radius values.
 */

export const colors = {
  // Brand colors
  brand: {
    navy: '#052F4E',
    blue: '#1463FF',
    lime: '#D2E90D',
  },
  
  // Workspace colors
  background: {
    workspace: '#F4F7FB',
    card: '#FFFFFF',
    navy: '#052F4E',
  },
  
  // Typography colors
  text: {
    heading: '#10213D',
    body: '#64748B',
    muted: '#94A3B8',
    inverse: '#FFFFFF',
  },
  
  // Semantic mastery colors
  mastery: {
    unknown: '#CBD5E1',
    locked: '#94A3B8',
    weak: '#EF4444',
    learning: '#F59E0B',
    understood: '#86EFAC',
    mastered: '#10B981',
    rootGap: '#D2E90D',
    target: '#1463FF',
  },
  
  // Utility colors
  border: '#E2E8F0',
  shadow: 'rgba(0, 0, 0, 0.05)',
};

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  '2xl': '48px',
  '3xl': '64px',
};

export const borderRadius = {
  sm: '8px',
  md: '12px',
  lg: '16px',
  xl: '20px',
};

export const typography = {
  fontFamily: {
    sans: 'var(--font-sans)',
  },
  fontSize: {
    xs: '12px',
    sm: '14px',
    base: '16px',
    lg: '18px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '30px',
    '4xl': '36px',
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
};
