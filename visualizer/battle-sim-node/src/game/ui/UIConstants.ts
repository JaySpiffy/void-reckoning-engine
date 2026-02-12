/**
 * UI CONSTANTS - Standardized Design System
 * 
 * Central source of truth for all UI styling to ensure consistency
 * across all components.
 */

// ============================================
// Z-INDEX LAYERS
// ============================================

export const Z_LAYERS = {
  CANVAS: 0,
  BACKGROUND: 10,
  HUD: 20,
  POPUP: 30,
  MODAL: 35,
  NOTIFICATION: 40,
  DEBUG: 50,
  TOOLTIP: 60,
  OVERLAY: 100,
} as const;

// ============================================
// COLOR PALETTE
// ============================================

export const COLORS = {
  // Primary
  PRIMARY: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',
    600: '#0284c7',
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
  },
  
  // Semantic
  SUCCESS: {
    light: '#4ade80',
    DEFAULT: '#22c55e',
    dark: '#16a34a',
  },
  WARNING: {
    light: '#fbbf24',
    DEFAULT: '#f59e0b',
    dark: '#d97706',
  },
  DANGER: {
    light: '#f87171',
    DEFAULT: '#ef4444',
    dark: '#dc2626',
  },
  INFO: {
    light: '#a78bfa',
    DEFAULT: '#8b5cf6',
    dark: '#7c3aed',
  },
  
  // Game-specific
  DNA: {
    GRASS: '#22c55e',
    VOID: '#8b5cf6',
    BEAST: '#f97316',
    ARCANE: '#06b6d4',
    FIRE: '#ef4444',
    WATER: '#3b82f6',
    POISON: '#a855f7',
    CRYSTAL: '#ec4899',
  },
  
  // UI Grays
  GRAY: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
    950: '#020617',
  },
} as const;

// ============================================
// SPACING SCALE
// ============================================

export const SPACING = {
  0: '0',
  0.5: '0.125rem',  // 2px
  1: '0.25rem',     // 4px
  2: '0.5rem',      // 8px
  3: '0.75rem',     // 12px
  4: '1rem',        // 16px
  5: '1.25rem',     // 20px
  6: '1.5rem',      // 24px
  8: '2rem',        // 32px
  10: '2.5rem',     // 40px
  12: '3rem',       // 48px
  16: '4rem',       // 64px
  20: '5rem',       // 80px
  24: '6rem',       // 96px
} as const;

// ============================================
// BORDER RADIUS
// ============================================

export const RADIUS = {
  NONE: '0',
  SM: '0.25rem',   // 4px
  DEFAULT: '0.5rem', // 8px
  MD: '0.5rem',    // 8px
  LG: '0.75rem',   // 12px
  XL: '1rem',      // 16px
  '2XL': '1.5rem', // 24px
  FULL: '9999px',
} as const;

// ============================================
// SHADOWS
// ============================================

export const SHADOWS = {
  SM: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  MD: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  LG: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  XL: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  INNER: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
  GLOW: {
    PRIMARY: '0 0 20px rgba(139, 92, 246, 0.5)',
    SUCCESS: '0 0 20px rgba(34, 197, 94, 0.5)',
    DANGER: '0 0 20px rgba(239, 68, 68, 0.5)',
  },
} as const;

// ============================================
// TRANSITIONS
// ============================================

export const TRANSITIONS = {
  FAST: '150ms',
  DEFAULT: '300ms',
  SLOW: '500ms',
  
  EASING: {
    DEFAULT: 'cubic-bezier(0.4, 0, 0.2, 1)',
    IN: 'cubic-bezier(0.4, 0, 1, 1)',
    OUT: 'cubic-bezier(0, 0, 0.2, 1)',
    BOUNCE: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  },
} as const;

// ============================================
// BUTTON VARIANTS
// ============================================

export const BUTTON_STYLES = {
  PRIMARY: 'bg-violet-600 hover:bg-violet-500 text-white border-transparent',
  SECONDARY: 'bg-slate-700 hover:bg-slate-600 text-white border-transparent',
  GHOST: 'bg-transparent hover:bg-slate-800 text-slate-300 border-slate-600',
  DANGER: 'bg-red-600 hover:bg-red-500 text-white border-transparent',
  SUCCESS: 'bg-green-600 hover:bg-green-500 text-white border-transparent',
  WARNING: 'bg-amber-600 hover:bg-amber-500 text-white border-transparent',
  
  // Size variants
  SM: 'px-2 py-1 text-xs',
  DEFAULT: 'px-3 py-2 text-sm',
  LG: 'px-4 py-3 text-base',
  
  // Base styles applied to all
  BASE: 'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-200 border focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95',
} as const;

// ============================================
// PANEL/MODAL STYLES
// ============================================

export const PANEL_STYLES = {
  BASE: 'bg-slate-900/95 backdrop-blur-md border border-slate-700 rounded-xl shadow-xl',
  HEADER: 'flex items-center justify-between px-4 py-3 border-b border-slate-700',
  TITLE: 'text-lg font-bold text-white',
  CLOSE_BUTTON: 'w-8 h-8 flex items-center justify-center rounded-full hover:bg-slate-800 text-slate-400 hover:text-white transition-colors',
  CONTENT: 'p-4',
  FOOTER: 'flex items-center justify-end gap-2 px-4 py-3 border-t border-slate-700',
} as const;

// ============================================
// INPUT STYLES
// ============================================

export const INPUT_STYLES = {
  BASE: 'w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all disabled:opacity-50 disabled:cursor-not-allowed',
  ERROR: 'border-red-500 focus:ring-red-500',
  SUCCESS: 'border-green-500 focus:ring-green-500',
} as const;

// ============================================
// TOAST/NOTIFICATION STYLES
// ============================================

export const TOAST_STYLES = {
  BASE: 'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg border',
  SUCCESS: 'bg-green-900/90 border-green-700 text-green-100',
  ERROR: 'bg-red-900/90 border-red-700 text-red-100',
  WARNING: 'bg-amber-900/90 border-amber-700 text-amber-100',
  INFO: 'bg-slate-800/90 border-slate-600 text-slate-100',
} as const;

// ============================================
// HELPER FUNCTIONS
// ============================================

export function getButtonClasses(
  variant: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success' | 'warning' = 'primary',
  size: 'sm' | 'default' | 'lg' = 'default',
  className = ''
): string {
  const variantMap: Record<typeof variant, string> = {
    primary: BUTTON_STYLES.PRIMARY,
    secondary: BUTTON_STYLES.SECONDARY,
    ghost: BUTTON_STYLES.GHOST,
    danger: BUTTON_STYLES.DANGER,
    success: BUTTON_STYLES.SUCCESS,
    warning: BUTTON_STYLES.WARNING,
  };
  
  const sizeMap: Record<typeof size, string> = {
    sm: BUTTON_STYLES.SM,
    default: BUTTON_STYLES.DEFAULT,
    lg: BUTTON_STYLES.LG,
  };
  
  return [BUTTON_STYLES.BASE, variantMap[variant], sizeMap[size], className].join(' ');
}

export function getPanelClasses(className = ''): string {
  return [PANEL_STYLES.BASE, className].join(' ');
}

export function getInputClasses(hasError = false, hasSuccess = false, className = ''): string {
  let classes = INPUT_STYLES.BASE;
  if (hasError) classes += ' ' + INPUT_STYLES.ERROR;
  if (hasSuccess) classes += ' ' + INPUT_STYLES.SUCCESS;
  if (className) classes += ' ' + className;
  return classes;
}
