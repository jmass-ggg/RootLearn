'use client';

import { ReactNode, useEffect, useState } from 'react';

/**
 * FadeTransition component for smooth state changes
 * Requirements: 15.3, 15.4, 15.5, 15.8
 * 
 * Provides fade in/out transitions when content changes
 * Respects prefers-reduced-motion via CSS
 */

interface FadeTransitionProps {
  children: ReactNode;
  /**
   * Key to trigger transition when changed
   * When key changes, component will fade out then fade in with new content
   */
  transitionKey: string | number;
  /**
   * Duration of fade animation in milliseconds
   * @default 250
   */
  duration?: number;
  /**
   * Additional CSS classes
   */
  className?: string;
}

export function FadeTransition({
  children,
  transitionKey,
  duration = 250,
  className = '',
}: FadeTransitionProps) {
  const [displayedKey, setDisplayedKey] = useState(transitionKey);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (transitionKey !== displayedKey) {
      // Fade out
      setIsVisible(false);

      // After fade out completes, update content and fade in
      const timer = setTimeout(() => {
        setDisplayedKey(transitionKey);
        // Small delay before fading in to ensure smooth transition
        requestAnimationFrame(() => {
          setIsVisible(true);
        });
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [transitionKey, displayedKey, duration]);

  return (
    <div
      className={`state-transition ${className}`}
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(8px)',
        transition: `opacity ${duration}ms ease-in-out, transform ${duration}ms ease-out`,
        // prefers-reduced-motion is handled by CSS media query in animations.css
      }}
    >
      {children}
    </div>
  );
}

/**
 * Simple fade-in wrapper for initial page load
 */
export function FadeIn({
  children,
  delay = 0,
  duration = 300,
  className = '',
}: {
  children: ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
}) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={className}
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(10px)',
        transition: `opacity ${duration}ms ease-out, transform ${duration}ms ease-out`,
      }}
    >
      {children}
    </div>
  );
}

/**
 * Slide up animation for content reveal
 */
export function SlideUp({
  children,
  delay = 0,
  className = '',
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <FadeIn delay={delay} duration={300} className={className}>
      {children}
    </FadeIn>
  );
}
