import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'violet' | 'gray' | 'green' | 'amber' | 'red' | 'blue';
  className?: string;
}

export function Badge({ children, variant = 'violet', className = '' }: BadgeProps) {
  const styles = {
    violet: 'bg-[#F3E8FF] text-[#6D28D9] border-[#DDD6FE]',
    gray: 'bg-gray-100 text-gray-700 border-gray-200',
    green: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    red: 'bg-rose-50 text-rose-700 border-rose-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles[variant]} ${className}`}>
      {children}
    </span>
  );
}

export default Badge;
