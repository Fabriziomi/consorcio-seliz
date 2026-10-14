import React from 'react';

const variants = {
  success: 'border-success/30 bg-success-soft text-success',
  warning: 'border-warning/30 bg-warning-soft text-warning',
  danger: 'border-danger/30 bg-danger-soft text-danger',
  info: 'border-info/30 bg-info-soft text-info',
  neutral: 'border-border bg-surface-muted text-secondary',
  brand: 'border-brand-ink/20 bg-brand-ink text-white',
};

export function Badge({ variant = 'neutral', className = '', children }) {
  return (
    <span
      className={`inline-flex min-h-5 sm:min-h-5.5 items-center rounded-full border px-2 py-0.5 text-[10px] sm:text-[11px] font-medium leading-none ${variants[variant] ?? variants.neutral} ${className}`}
    >
      {children}
    </span>
  );
}
