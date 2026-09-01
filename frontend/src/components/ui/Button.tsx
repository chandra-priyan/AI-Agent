import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  icon?: React.ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  icon,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none rounded-lg cursor-pointer';
  
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-xs font-semibold gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-6 py-3 text-base font-semibold gap-2.5',
  };

  const variantStyles = {
    primary: 'bg-[#6D28D9] text-white hover:bg-[#5B21B6] focus:ring-[#6D28D9] shadow-sm',
    secondary: 'bg-[#F3F4F6] text-[#1F2937] hover:bg-[#E5E7EB] focus:ring-[#9CA3AF]',
    outline: 'border border-[#E5E7EB] bg-white text-[#374151] hover:bg-[#F9FAFB] focus:ring-[#6D28D9]',
    ghost: 'text-[#4B5563] hover:bg-[#F3F4F6] hover:text-[#111827]',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </button>
  );
}

export default Button;
