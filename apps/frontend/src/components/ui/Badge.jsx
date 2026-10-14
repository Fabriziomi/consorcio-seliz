import React from 'react';

/**
 * Variantes de estado suaves y "apagadas" (muted / matte tinted).
 * Conservan un matiz sutil del color original sobre fondo tenue y bordes delicados,
 * integrándose de forma armónica en una estética monocromática sin saturación agresiva.
 */
export const badgeVariants = {
  success: 'border-emerald-300/35 bg-emerald-50/40 text-emerald-700/80',
  warning: 'border-amber-300/35 bg-amber-50/40 text-amber-700/80',
  danger: 'border-rose-300/35 bg-rose-50/40 text-rose-700/80',
  info: 'border-slate-300/40 bg-slate-100/50 text-slate-600',
  neutral: 'border-zinc-200/70 bg-zinc-100/60 text-zinc-600',
  brand: 'border-zinc-200 bg-zinc-800 text-white',
};

const variants = badgeVariants;

export function Badge({ variant = 'neutral', className = '', children }) {
  return (
    <span
      className={`inline-flex min-h-7 items-center justify-center rounded-full border px-3 py-0.5 text-xs font-medium leading-none tracking-tight transition-colors ${variants[variant] ?? variants.neutral} ${className}`}
    >
      {children}
    </span>
  );
}
