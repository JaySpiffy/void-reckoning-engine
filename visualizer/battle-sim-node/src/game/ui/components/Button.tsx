import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../../lib/utils';

export type ButtonVariant = 
  | 'default' 
  | 'secondary' 
  | 'ghost' 
  | 'outline' 
  | 'danger' 
  | 'success' 
  | 'warning' 
  | 'link';

export type ButtonSize = 'default' | 'sm' | 'lg' | 'icon' | 'icon-sm' | 'icon-lg';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  default: 'bg-violet-600 text-white hover:bg-violet-500 shadow-lg shadow-violet-900/20',
  secondary: 'bg-slate-700 text-white hover:bg-slate-600',
  ghost: 'bg-transparent text-slate-300 hover:bg-slate-800 hover:text-white',
  outline: 'border-2 border-slate-600 bg-transparent text-slate-300 hover:bg-slate-800 hover:text-white',
  danger: 'bg-red-600 text-white hover:bg-red-500 shadow-lg shadow-red-900/20',
  success: 'bg-green-600 text-white hover:bg-green-500 shadow-lg shadow-green-900/20',
  warning: 'bg-amber-600 text-white hover:bg-amber-500',
  link: 'text-violet-400 underline-offset-4 hover:underline bg-transparent',
};

const sizeStyles: Record<ButtonSize, string> = {
  default: 'h-10 px-4 py-2 text-sm',
  sm: 'h-8 px-3 text-xs',
  lg: 'h-12 px-6 text-base',
  icon: 'h-10 w-10',
  'icon-sm': 'h-8 w-8',
  'icon-lg': 'h-12 w-12',
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className, 
    variant = 'default', 
    size = 'default', 
    children, 
    isLoading, 
    leftIcon, 
    rightIcon, 
    disabled, 
    ...props 
  }, ref) => {
    return (
      <button
        className={cn(
          // Base styles
          'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg font-medium',
          'transition-all duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500',
          'focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900',
          'disabled:pointer-events-none disabled:opacity-50',
          'active:scale-95',
          // Variant styles
          variantStyles[variant],
          // Size styles
          sizeStyles[size],
          // Custom classes
          className
        )}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
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
        {!isLoading && leftIcon}
        {children}
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button };
