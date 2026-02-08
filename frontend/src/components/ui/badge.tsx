import * as React from 'react';

function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(' ');
}

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'outline' | 'success' | 'warning' | 'secondary';
}

const variants: Record<NonNullable<BadgeProps['variant']>, string> = {
  default: 'bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900',
  outline: 'border border-neutral-300 text-neutral-700 dark:border-neutral-600 dark:text-neutral-300',
  success: 'bg-green-600 text-white',
  warning: 'bg-amber-500 text-white',
  secondary: 'bg-neutral-200 text-neutral-800 dark:bg-neutral-700 dark:text-white',
};

export const Badge: React.FC<BadgeProps> = ({ className, variant = 'default', ...props }) => (
  <span
    className={cn(
      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
      variants[variant],
      className
    )}
    {...props}
  />
);

export default Badge;
