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

export const badgeSizes = {
  xs: 'min-h-5 px-2 py-0.5 text-[10px] gap-1',
  sm: 'min-h-6 px-2.5 py-0.5 text-[11px] gap-1.5',
  md: 'min-h-7 px-3 py-0.5 text-xs gap-1.5',
};

export function Badge({ variant = 'neutral', size = 'md', className = '', children }) {
  return (
    <span
      className={`inline-flex items-center justify-center rounded-full border font-medium leading-none tracking-tight transition-all duration-500 ease-out hover:scale-105 select-none ${badgeSizes[size] ?? badgeSizes.md} ${badgeVariants[variant] ?? badgeVariants.neutral} ${className}`}
    >
      {children}
    </span>
  );
}
