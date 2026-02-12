import { type ReactNode } from 'react';
import { cn } from '../../../lib/utils';
import { X } from 'lucide-react';
import { Button } from './Button';

export interface PanelProps {
  children: ReactNode;
  className?: string;
  title?: string;
  onClose?: () => void;
  headerActions?: ReactNode;
  footer?: ReactNode;
  isOpen: boolean;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}

const sizeClasses = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  full: 'max-w-full mx-4',
};

export function Panel({
  children,
  className,
  title,
  onClose,
  headerActions,
  footer,
  isOpen,
  size = 'md',
}: PanelProps) {
  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className={cn(
          'w-full bg-slate-900/95 backdrop-blur-md border border-slate-700 rounded-xl shadow-2xl',
          'flex flex-col max-h-[90vh]',
          sizeClasses[size],
          className
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        {(title || onClose || headerActions) && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/50">
            {title && (
              <h2 className="text-xl font-bold text-white tracking-tight">{title}</h2>
            )}
            <div className="flex items-center gap-2 ml-auto">
              {headerActions}
              {onClose && (
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={onClose}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-700/50">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

// Simple card variant for in-game UI elements
export interface CardProps {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  icon?: ReactNode;
  onClick?: () => void;
}

export function Card({ children, className, title, subtitle, icon, onClick }: CardProps) {
  return (
    <div
      className={cn(
        'bg-slate-900/80 backdrop-blur-sm border border-slate-700 rounded-xl',
        'shadow-lg overflow-hidden',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      {(title || icon) && (
        <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-700/50 bg-slate-800/50">
          {icon && <div className="text-violet-400">{icon}</div>}
          <div>
            {title && <h3 className="font-semibold text-white">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
          </div>
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}
