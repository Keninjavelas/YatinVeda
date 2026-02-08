import * as React from 'react';

function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(' ');
}

type DivProps = React.HTMLAttributes<HTMLDivElement>;

export const Card: React.FC<DivProps> = ({ className, ...props }) => (
  <div className={cn('rounded-lg border bg-white shadow-sm dark:bg-neutral-900 dark:border-neutral-800', className)} {...props} />
);

export const CardHeader: React.FC<DivProps> = ({ className, ...props }) => (
  <div className={cn('p-4 border-b dark:border-neutral-800', className)} {...props} />
);

export const CardTitle: React.FC<DivProps> = ({ className, ...props }) => (
  <h3 className={cn('text-lg font-semibold leading-none tracking-tight', className)} {...props} />
);

export const CardDescription: React.FC<DivProps> = ({ className, ...props }) => (
  <p className={cn('text-sm text-neutral-500 dark:text-neutral-400', className)} {...props} />
);

export const CardContent: React.FC<DivProps> = ({ className, ...props }) => (
  <div className={cn('p-4', className)} {...props} />
);

export const CardFooter: React.FC<DivProps> = ({ className, ...props }) => (
  <div className={cn('p-4 border-t dark:border-neutral-800', className)} {...props} />
);

export default Card;
