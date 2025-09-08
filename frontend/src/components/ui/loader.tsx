'use client';

import React from 'react';

type LoaderOneProps = {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
};

const sizeToDot = {
  sm: 'w-2 h-2',
  md: 'w-3 h-3',
  lg: 'w-4 h-4',
};

export function LoaderOne({ className = '', size = 'sm' }: LoaderOneProps) {
  const dot = sizeToDot[size] || sizeToDot.sm;
  return (
    <div className={`inline-flex items-center gap-1 text-gray-600 dark:text-gray-300 ${className}`} aria-label="Loading">
      <span className={`${dot} rounded-full bg-current animate-bounce [animation-delay:-0.2s]`}></span>
      <span className={`${dot} rounded-full bg-current animate-bounce [animation-delay:-0.1s]`}></span>
      <span className={`${dot} rounded-full bg-current animate-bounce`}></span>
    </div>
  );
}

export function LoaderOneDemo() {
  return <LoaderOne />;
}


