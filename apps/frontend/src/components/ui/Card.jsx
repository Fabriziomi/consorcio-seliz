import React from 'react';

export function Card({ className = '', children }) {
  return (
    <section className={`rounded-lg border border-border bg-white shadow-card ${className}`}>
      {children}
    </section>
  );
}

export function CardHeader({ className = '', children }) {
  return <div className={`border-b border-border px-4 py-4 sm:px-5 ${className}`}>{children}</div>;
}

export function CardContent({ className = '', children }) {
  return <div className={`px-4 py-4 sm:px-5 sm:py-5 ${className}`}>{children}</div>;
}
