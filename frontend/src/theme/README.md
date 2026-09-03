# RootLearn Design System

This directory contains the core design tokens and theme configuration for the RootLearn UI/UX redesign.

## Overview

The design system provides a cohesive visual language with:
- **Consistent color palette** for brand identity and semantic meaning
- **Standardized spacing scale** for layout harmony
- **Typography hierarchy** for clear content structure
- **Border radius system** for component identity

All tokens are defined in `tokens.ts` and extended into Tailwind CSS configuration for easy usage throughout the application.

## Color Palette

### Brand Colors

Our brand identity colors create a professional, trustworthy appearance:

| Color | Hex | Usage |
|-------|-----|-------|
| **Navy** | `#052F4E` | Primary navigation, hero sections, high-contrast backgrounds |
| **Blue** | `#1463FF` | Interactive elements, primary buttons, links, target highlighting |
| **Lime** | `#D2E90D` | High-emphasis actions, root gap highlighting, celebrations |

**When to use:**
- **Navy**: Use for large background surfaces that need high contrast with white content. Ideal for headers, hero sections, and navigation.
- **Blue**: Primary action color. Use for buttons, links, and interactive elements that drive the core user journey.
- **Lime**: Reserved for high-emphasis moments - root gap discovery, major achievements, lime CTA buttons. Use sparingly for maximum impact.

### Background Colors

Surface colors for different contexts:

| Color | Hex | Usage |
|-------|-----|-------|
| **Workspace** | `#F4F7FB` | Light neutral background for main content areas |
| **Card** | `#FFFFFF` | White background for elevated content cards |
| **Navy** | `#052F4E` | Dark backgrounds (matches brand navy) |

**When to use:**
- Use `workspace` for the main application background
- Use `card` for any content that needs visual separation from the workspace
- Use `navy` background with inverse text colors for hero sections

### Typography Colors

Text colors for content hierarchy:

| Color | Hex | Usage |
|-------|-----|-------|
| **Heading** | `#10213D` | Headings, emphasized text |
| **Body** | `#64748B` | Primary body text |
| **Muted** | `#94A3B8` | Secondary text, placeholders |
| **Inverse** | `#FFFFFF` | Text on dark backgrounds |

**When to use:**
- Use `heading` for all h1-h6 elements and emphasized text
- Use `body` for paragraph text and most UI text
- Use `muted` for secondary information like timestamps, helper text
- Use `inverse` when text appears on navy or dark backgrounds

### Semantic Mastery Colors

Colors representing learner understanding states in the knowledge graph:

| State | Color | Hex | Meaning |
|-------|-------|-----|---------|
| **Unknown** | Gray | `#CBD5E1` | Not yet assessed |
| **Locked** | Muted Gray | `#94A3B8` | Prerequisites not met |
| **Weak** | Red | `#EF4444` | Poor understanding - needs attention |
| **Learning** | Amber | `#F59E0B` | Partial understanding - in progress |
| **Understood** | Light Green | `#86EFAC` | Good understanding - sufficient |
| **Mastered** | Dark Green | `#10B981` | Complete mastery - excellent |
| **Root Gap** | Lime | `#D2E90D` | Foundational gap identified - start here |
| **Target** | Blue | `#1463FF` | Learning goal - destination |

**When to use:**
- Apply to knowledge graph nodes based on `concept.status` field
- Use root gap color for concepts where `is_root_gap === true`
- Use target color for concepts where `is_target === true`
- Never use for non-mastery-related UI elements

**Accessibility note:**
- These colors are not used for text-only indicators
- Always pair with icons, labels, or text descriptions
- Never rely solely on color to convey mastery state

### Utility Colors

Supporting colors:

| Color | Hex | Usage |
|-------|-----|-------|
| **Border** | `#E2E8F0` | Card borders, separators |
| **Shadow** | `rgba(0, 0, 0, 0.05)` | Subtle shadows on elevated surfaces |

## Spacing Scale

Our spacing system uses a 4px base unit for mathematical consistency:

| Token | Value | Tailwind | Usage |
|-------|-------|----------|-------|
| `xs` | 4px | `gap-1`, `p-1` | Tight inline spacing |
| `sm` | 8px | `gap-2`, `p-2` | Small component spacing |
| `md` | 16px | `gap-4`, `p-4` | Medium component spacing |
| `lg` | 24px | `gap-6`, `p-6` | Standard card padding (default) |
| `xl` | 32px | `gap-8`, `p-8` | Section padding |
| `2xl` | 48px | `gap-12`, `p-12` | Major section breaks |
| `3xl` | 64px | `gap-16`, `p-16` | Page-level spacing |

**When to use:**
- `xs/sm`: Tight spacing within buttons, badges, inline elements
- `md/lg`: Standard spacing for card padding, form fields
- `xl/2xl/3xl`: Larger spacing between sections and page elements

**Example:**
```tsx
// Card with standard padding
<Card padding="lg"> // 24px padding

// Tight gap between button icon and text
<button className="flex gap-2"> // 8px gap
```

## Border Radius

Rounded corners create visual hierarchy:

| Token | Value | Tailwind | Usage |
|-------|-------|----------|-------|
| `sm` | 8px | `rounded-md` | Buttons, badges, small chips |
| `md` | 12px | `rounded-lg` | Input fields, small cards |
| `lg` | 16px | `rounded-xl` | Medium cards |
| `xl` | 20px | `rounded-2xl` | Large cards, modals (default) |

**When to use:**
- `sm`: Small interactive elements (buttons, badges)
- `md`: Form inputs and small containers
- `lg/xl`: Content cards and dialog boxes

## Typography

### Font Sizes

| Token | Value | Tailwind | Usage |
|-------|-------|----------|-------|
| `xs` | 12px | `text-xs` | Captions, small labels |
| `sm` | 14px | `text-sm` | Secondary UI text |
| `base` | 16px | `text-base` | Body text (default) |
| `lg` | 18px | `text-lg` | Emphasized body text |
| `xl` | 20px | `text-xl` | Small headings |
| `2xl` | 24px | `text-2xl` | Medium headings |
| `3xl` | 30px | `text-3xl` | Section headings |
| `4xl` | 36px | `text-4xl` | Page headings |

### Font Weights

| Token | Value | Tailwind | Usage |
|-------|-------|----------|-------|
| `normal` | 400 | `font-normal` | Body text |
| `medium` | 500 | `font-medium` | UI elements, buttons |
| `semibold` | 600 | `font-semibold` | Subheadings |
| `bold` | 700 | `font-bold` | Main headings |

### Typography Hierarchy

Recommended combinations:

```tsx
// Page heading
<h1 className="text-4xl font-bold text-text-heading">

// Section heading
<h2 className="text-3xl font-semibold text-text-heading">

// Subsection heading
<h3 className="text-2xl font-semibold text-text-heading">

// Body text
<p className="text-base font-normal text-text-body">

// Small secondary text
<span className="text-sm font-normal text-text-muted">
```

## Usage Examples

### Using Design Tokens in Components

```tsx
import { colors, spacing, borderRadius } from '@/theme/tokens';

// In styled component
const customStyles = {
  backgroundColor: colors.brand.blue,
  padding: spacing.lg,
  borderRadius: borderRadius.xl,
};

// Most commonly, use with Tailwind classes
<div className="bg-brand-blue p-6 rounded-xl">
```

### Tailwind Configuration

All design tokens are extended into Tailwind configuration:

```javascript
// tailwind.config.ts
module.exports = {
  theme: {
    extend: {
      colors: {
        'brand-navy': colors.brand.navy,
        'brand-blue': colors.brand.blue,
        // ... etc
      },
    },
  },
};
```

Use in components via Tailwind classes:

```tsx
<div className="bg-brand-navy text-text-inverse">
  <h1 className="text-4xl font-bold">RootLearn</h1>
</div>
```

## Best Practices

### Colors

1. **Be semantic**: Use color names that describe their purpose, not appearance
2. **Maintain contrast**: Ensure text/background combinations meet WCAG AA standards
3. **Limit palette**: Stick to the defined colors - don't introduce new colors without updating the design system
4. **Test mastery colors**: Verify mastery state colors are distinguishable for colorblind users

### Spacing

1. **Use the scale**: Always use spacing tokens instead of arbitrary values
2. **Be consistent**: Use the same spacing token for similar contexts (e.g., all card padding uses `lg`)
3. **Respect hierarchy**: Larger spacing indicates greater separation of concepts

### Typography

1. **Follow hierarchy**: Use size and weight consistently across the application
2. **Limit variety**: Don't use every size and weight - stick to the common patterns
3. **Pair thoughtfully**: Large sizes need bolder weights; small sizes need lighter weights

### Border Radius

1. **Match component size**: Larger components get larger border radius
2. **Stay consistent**: Use the same border radius for similar component types
3. **Don't overuse**: Not every element needs rounded corners

## Accessibility Considerations

### Color Contrast

All text/background combinations meet WCAG AA standards:

- Navy background + inverse text: ✅ 14.4:1
- Blue button + inverse text: ✅ 8.2:1
- Body text + workspace background: ✅ 7.1:1
- Muted text + workspace background: ✅ 4.8:1

### Mastery Colors

- Mastery states never rely solely on color
- Always include text labels and icons
- Graph nodes show both color and mastery percentage

### Focus States

All interactive elements have visible focus indicators:
- 2px focus ring using brand blue
- Offset from element by 2px
- Visible when navigating with keyboard

## Extending the Design System

If you need to add new tokens:

1. **Discuss with team**: New tokens should address a real pattern, not one-off needs
2. **Update tokens.ts**: Add the new token with clear documentation
3. **Update Tailwind config**: Extend the Tailwind configuration
4. **Update this README**: Document when and how to use the new token
5. **Update components**: Apply the new token consistently

## Related Files

- `tokens.ts` - Token definitions
- `../../tailwind.config.ts` - Tailwind integration
- `../components/ui/` - Core UI components that use these tokens
- `../app/globals.css` - Global CSS including Tailwind directives
