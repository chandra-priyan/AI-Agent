import React from 'react';

export interface SkeletonLoaderProps {
  lines?: number;
  className?: string;
}

export function SkeletonLoader({ lines = 3, className = '' }: SkeletonLoaderProps) {
  return (
    <div className={`animate-pulse space-y-3 ${className}`}>
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className="h-4 bg-[#E5E7EB] rounded-md"
          style={{ width: `${100 - index * 15}%` }}
        />
      ))}
    </div>
  );
}

export default SkeletonLoader;
