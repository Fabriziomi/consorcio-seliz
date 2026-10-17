import React from 'react';

export function Card({ className = '', children }) {
  return (
    <section className={`rounded-base border border-border/80 bg-white shadow-subtle transition-all duration-500 ease-out ${className}`}>
      {children}
    </section>
  );
}

export function CardHeader({ className = '', children }) {
  return <div className={`border-b border-border/70 px-3.5 py-2.5 sm:px-4 sm:py-3 ${className}`}>{children}</div>;
}

export function CardContent({ className = '', children }) {
  return <div className={`px-3 py-3 sm:px-4 sm:py-3.5 ${className}`}>{children}</div>;
}
