import type { Config } from "tailwindcss";
import { colors, spacing, borderRadius } from "./src/theme/tokens";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        // Brand colors
        'brand-navy': colors.brand.navy,
        'brand-blue': colors.brand.blue,
        'brand-lime': colors.brand.lime,
        // Background colors
        'bg-workspace': colors.background.workspace,
        'bg-card': colors.background.card,
        'bg-navy': colors.background.navy,
        // Text colors
        'text-heading': colors.text.heading,
        'text-body': colors.text.body,
        'text-muted': colors.text.muted,
        'text-inverse': colors.text.inverse,
        // Mastery colors
        'mastery-unknown': colors.mastery.unknown,
        'mastery-locked': colors.mastery.locked,
        'mastery-weak': colors.mastery.weak,
        'mastery-learning': colors.mastery.learning,
        'mastery-understood': colors.mastery.understood,
        'mastery-mastered': colors.mastery.mastered,
        'mastery-root-gap': colors.mastery.rootGap,
        'mastery-target': colors.mastery.target,
        // Utility colors
        'border-default': colors.border,
      },
      spacing: {
        'xs': spacing.xs,
        'sm': spacing.sm,
        'md': spacing.md,
        'lg': spacing.lg,
        'xl': spacing.xl,
        '2xl': spacing['2xl'],
        '3xl': spacing['3xl'],
      },
      borderRadius: {
        'sm': borderRadius.sm,
        'md': borderRadius.md,
        'lg': borderRadius.lg,
        'xl': borderRadius.xl,
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
      },
      fontWeight: {
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
      },
      boxShadow: {
        'subtle': `0 2px 8px ${colors.shadow}`,
      },
    },
  },
  plugins: [],
};
export default config;
