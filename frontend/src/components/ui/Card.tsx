import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export function Card({ children, className = '', onClick, hoverable = false }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl border border-[#E5E7EB] shadow-xs p-6 ${
        hoverable ? 'hover:border-[#6D28D9]/40 hover:shadow-md transition-all duration-200 cursor-pointer' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
}

export default Card;
