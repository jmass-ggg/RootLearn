/**
 * Design System Tokens
 * 
 * Core design tokens for the RootLearn UI/UX redesign.
 * Includes colors, spacing, typography, and border radius values.
 * 
 * @see frontend/src/theme/README.md for detailed usage guide
 */

/**
 * Color Palette
 * 
 * The color system is organized into semantic groups for consistent usage:
 * - Brand: Core brand identity colors
 * - Background: Surface colors for different contexts
 * - Text: Typography colors for various content types
 * - Mastery: Semantic colors representing learning progress states
 * - Utility: Border and shadow colors
 */
export const colors = {
  /**
   * Brand Colors
   * 
   * Primary brand identity colors used for:
   * - Navy: Primary navigation surfaces, hero sections, high-contrast backgrounds
   * - Blue: Interactive elements, primary buttons, links, target concept highlighting
   * - Lime: High-emphasis actions, root gap highlighting, achievement celebrations
   * 
   * @example
   * // Use navy for hero sections
   * <div className="bg-brand-navy">
   * 
   * // Use blue for primary actions
   * <Button variant="primary"> // Uses brand-blue
   * 
   * // Use lime for high-emphasis elements
   * <Button variant="lime"> // Uses brand-lime
   */
  brand: {
    navy: '#052F4E',  // Deep navy - primary brand color
    blue: '#1463FF',  // Electric blue - interactive elements
    lime: '#D2E90D',  // Lime accent - high emphasis
  },
  
  /**
   * Background Colors
   * 
   * Surface colors for different contexts:
   * - workspace: Light neutral background for main content areas
   * - card: White background for elevated content cards
   * - navy: Dark navy for hero sections and navigation
   * 
   * @example
   * // Workspace background
   * <main className="bg-bg-workspace">
   * 
   * // White card on workspace
   * <Card variant="default"> // Uses bg-card
   */
  background: {
    workspace: '#F4F7FB',  // Light gray - main workspace background
    card: '#FFFFFF',       // White - card and elevated surfaces
    navy: '#052F4E',       // Navy - matches brand.navy
  },
  
  /**
   * Typography Colors
   * 
   * Text colors for various content hierarchy:
   * - heading: Dark ink for headings and emphasis
   * - body: Medium slate for body text
   * - muted: Light slate for secondary text
   * - inverse: White text for dark backgrounds
   * 
   * @example
   * // Heading text
   * <h1 className="text-text-heading">
   * 
   * // Body text
   * <p className="text-text-body">
   * 
   * // Muted secondary text
   * <span className="text-text-muted">
   */
  text: {
    heading: '#10213D',  // Dark ink - headings
    body: '#64748B',     // Slate - body text
    muted: '#94A3B8',    // Light slate - secondary text
    inverse: '#FFFFFF',  // White - text on dark backgrounds
  },
  
  /**
   * Semantic Mastery Colors
   * 
   * Colors representing learner understanding states in the knowledge graph:
   * - unknown: Not yet assessed (neutral gray)
   * - locked: Prerequisite not met (muted gray)
   * - weak: Poor understanding (red - needs attention)
   * - learning: Partial understanding (amber - in progress)
   * - understood: Good understanding (light green - sufficient)
   * - mastered: Complete understanding (dark green - excellent)
   * - rootGap: Identified foundational gap (lime - start here)
   * - target: Learning goal (blue - destination)
   * 
   * Usage: Apply to knowledge graph nodes based on concept mastery state
   * 
   * @example
   * // In KnowledgeGraph component
   * const nodeColor = colors.mastery[concept.status];
   * 
   * // Root gap node gets special highlighting
   * if (concept.is_root_gap) {
   *   backgroundColor = colors.mastery.rootGap;
   * }
   */
  mastery: {
    unknown: '#CBD5E1',   // Neutral gray - not assessed
    locked: '#94A3B8',    // Muted gray - prerequisites not met
    weak: '#EF4444',      // Red - poor understanding
    learning: '#F59E0B',  // Amber - partial understanding
    understood: '#86EFAC', // Light green - good understanding
    mastered: '#10B981',  // Dark green - complete mastery
    rootGap: '#D2E90D',   // Lime - foundational gap identified
    target: '#1463FF',    // Blue - learning target
  },
  
  /**
   * Utility Colors
   * 
   * Supporting colors for borders and shadows:
   * - border: Cool gray borders for cards and separators
   * - shadow: Subtle shadow for elevated components
   * 
   * @example
   * // Card with border
   * <div className="border border-border-default">
   * 
   * // Elevated card with shadow
   * <Card variant="elevated"> // Uses shadow
   */
  border: '#E2E8F0',              // Cool gray - borders
  shadow: 'rgba(0, 0, 0, 0.05)',  // Subtle shadow - elevated surfaces
};

/**
 * Spacing Scale
 * 
 * Consistent spacing values for padding, margins, and gaps.
 * Based on 4px base unit for mathematical consistency.
 * 
 * Usage:
 * - xs/sm: Tight spacing within components (4-8px)
 * - md/lg: Standard component spacing (16-24px)
 * - xl/2xl: Section spacing (32-48px)
 * - 3xl: Large section breaks (64px)
 * 
 * @example
 * // Small padding in Card
 * <Card padding="sm">
 * 
 * // Standard padding in Card (default)
 * <Card padding="lg">
 * 
 * // Tight gap in Button
 * <div className="flex gap-2"> // 8px gap (sm)
 */
export const spacing = {
  xs: '4px',    // Extra small - tight inline spacing
  sm: '8px',    // Small - inline component spacing
  md: '16px',   // Medium - component internal spacing
  lg: '24px',   // Large - standard card padding
  xl: '32px',   // Extra large - section padding
  '2xl': '48px', // 2X large - major section breaks
  '3xl': '64px', // 3X large - page-level spacing
};

/**
 * Border Radius Scale
 * 
 * Rounded corner values for different component sizes.
 * Creates visual hierarchy through border radius.
 * 
 * Usage:
 * - sm: Small components (buttons, badges)
 * - md: Medium components (inputs, small cards)
 * - lg: Large components (cards, dialogs)
 * - xl: Extra large components (hero sections)
 * 
 * @example
 * // Small radius for buttons
 * <button className="rounded-md"> // 12px
 * 
 * // Large radius for cards (default)
 * <Card> // Uses rounded-xl (20px)
 */
export const borderRadius = {
  sm: '8px',   // Small - buttons, badges
  md: '12px',  // Medium - inputs, chips
  lg: '16px',  // Large - small cards
  xl: '20px',  // Extra large - main cards, modals
};

/**
 * Typography System
 * 
 * Font sizes, weights, and families for consistent text hierarchy.
 * 
 * Font Sizes:
 * - xs/sm: Small UI text (12-14px)
 * - base/lg: Body and button text (16-18px)
 * - xl/2xl: Subheadings (20-24px)
 * - 3xl/4xl: Main headings (30-36px)
 * 
 * Font Weights:
 * - normal (400): Body text
 * - medium (500): Button text
 * - semibold (600): Subheadings
 * - bold (700): Main headings
 * 
 * @example
 * // Heading hierarchy
 * <h1 className="text-4xl font-bold">Main Heading</h1>
 * <h2 className="text-2xl font-semibold">Subheading</h2>
 * <p className="text-base font-normal">Body text</p>
 */
export const typography = {
  fontFamily: {
    sans: 'var(--font-sans)', // System sans-serif stack
  },
  fontSize: {
    xs: '12px',    // Extra small - captions, labels
    sm: '14px',    // Small - secondary UI text
    base: '16px',  // Base - body text
    lg: '18px',    // Large - emphasized body text
    xl: '20px',    // Extra large - small headings
    '2xl': '24px', // 2X large - medium headings
    '3xl': '30px', // 3X large - section headings
    '4xl': '36px', // 4X large - page headings
  },
  fontWeight: {
    normal: '400',   // Regular - body text
    medium: '500',   // Medium - UI elements
    semibold: '600', // Semibold - subheadings
    bold: '700',     // Bold - main headings
  },
};
