import React, { forwardRef } from 'react';

const variants = {
  primary:
    'bg-brand-ink bg-[image:var(--gradient-action-primary)] text-white shadow-card hover:bg-brand-ink-elevated hover:bg-[image:var(--gradient-action-primary-hover)] hover:text-white hover:shadow-card-hover active:bg-brand-ink',
  secondary:
    'border border-border bg-white text-brand-ink hover:border-brand-ink hover:bg-surface-muted hover:text-brand-ink hover:shadow-sm active:bg-surface-muted',
  tertiary:
    'text-brand-ink underline decoration-border-strong underline-offset-4 hover:decoration-brand-ink hover:text-black',
  ghost:
    'text-brand-ink hover:bg-surface-muted hover:text-black active:bg-surface-muted',
  danger:
    'border border-danger/30 bg-danger-soft text-danger hover:border-danger hover:bg-danger hover:text-white hover:shadow-sm active:bg-danger',
};

const baseClassName =
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-base font-semibold transition-all duration-150 ease-out focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-brand-ink active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50 cursor-pointer select-none';

const sizes = {
  sm: 'h-9 px-3 text-xs gap-1.5',
  md: 'min-h-11 px-4 text-sm gap-2',
  icon: 'size-11 p-0 text-sm',
  'icon-sm': 'size-9 p-0 text-xs',
};

export const Button = forwardRef(function Button(
  { variant = 'primary', size = 'md', type = 'button', className = '', href, ...props },
  ref,
) {
  const combinedClassName = `${baseClassName} ${sizes[size] ?? sizes.md} ${variants[variant] ?? variants.primary} ${className}`;

  if (href) {
    return (
      <a
        ref={ref}
        href={href}
        className={combinedClassName}
        {...props}
      />
    );
  }

  return (
    <button
      ref={ref}
      type={type}
      className={combinedClassName}
      {...props}
    />
  );
});
