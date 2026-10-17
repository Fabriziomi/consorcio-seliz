import React, { forwardRef } from 'react';
import { Loader2, Check } from 'lucide-react';

const variants = {
  primary:
    'bg-brand-ink text-white shadow-xs hover:bg-black active:bg-brand-ink border border-zinc-900',
  secondary:
    'border border-border/90 bg-white text-brand-ink shadow-2xs hover:border-brand-ink/80 hover:bg-surface-soft active:bg-surface-muted',
  tertiary:
    'text-brand-ink underline decoration-border-strong underline-offset-4 hover:decoration-brand-ink hover:text-black',
  ghost:
    'text-brand-ink hover:bg-surface-muted hover:text-black active:bg-surface-muted',
  danger:
    'border border-danger/30 bg-danger-soft text-danger hover:border-danger hover:bg-danger hover:text-white active:bg-danger',
  success:
    'border border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100',
};

const baseClassName =
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl font-semibold transition-all duration-500 ease-out focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-brand-ink hover:shadow-sm active:scale-[0.96] [&>svg]:transition-transform [&>svg]:duration-500 [&>svg]:ease-out hover:[&>svg]:scale-115 active:[&>svg]:scale-90 disabled:pointer-events-none disabled:opacity-50 cursor-pointer select-none';

const sizes = {
  sm: 'h-9 px-3.5 text-xs gap-2',
  md: 'h-10 sm:h-11 px-4 text-xs sm:text-sm gap-2.5',
  lg: 'h-12 px-5 text-sm sm:text-base gap-3',
  icon: 'size-10 sm:size-11 p-0 shrink-0',
  'icon-sm': 'size-9 sm:size-10 p-0 shrink-0',
  'icon-xs': 'size-8 p-0 shrink-0',
};

export const Button = forwardRef(function Button(
  {
    variant = 'primary',
    size = 'md',
    type = 'button',
    className = '',
    loading = false,
    confirmed = false,
    confirmedText = 'Confirmado',
    children,
    disabled,
    href,
    ...props
  },
  ref,
) {
  const currentVariant = confirmed ? 'success' : variant;
  const combinedClassName = `${baseClassName} ${sizes[size] ?? sizes.md} ${variants[currentVariant] ?? variants.primary} ${className}`;

  if (href) {
    return (
      <a
        ref={ref}
        href={href}
        className={combinedClassName}
        {...props}
      >
        {children}
      </a>
    );
  }

  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      className={combinedClassName}
      {...props}
    >
      {loading ? (
        <Loader2 size={size.startsWith('icon') ? 20 : 18} strokeWidth={2.2} className="animate-spin text-current shrink-0" />
      ) : confirmed ? (
        <>
          <Check size={size.startsWith('icon') ? 20 : 18} strokeWidth={2.5} className="text-emerald-700 shrink-0" />
          {!size.startsWith('icon') && <span>{confirmedText}</span>}
        </>
      ) : (
        children
      )}
    </button>
  );
});
