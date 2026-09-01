import React from 'react';
import { Button } from './Button';

export interface EmptyStateProps {
  title: string;
  description: string;
  actionText?: string;
  actionIcon?: React.ReactNode;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  title,
  description,
  actionText,
  actionIcon,
  onAction,
  className = '',
}: EmptyStateProps) {
  return (
    <div className={`bg-white border border-[#E5E7EB] rounded-2xl p-10 text-center flex flex-col items-center justify-center shadow-xs ${className}`}>
      <div className="w-16 h-16 rounded-2xl bg-[#F3E8FF] text-[#6D28D9] flex items-center justify-center mb-4 text-2xl font-bold">
        📊
      </div>
      <h3 className="text-lg font-bold text-[#111827] mb-2">{title}</h3>
      <p className="text-sm text-[#6B7280] max-w-md mb-6">{description}</p>
      {actionText && onAction && (
        <Button variant="primary" icon={actionIcon} onClick={onAction}>
          {actionText}
        </Button>
      )}
    </div>
  );
}

export default EmptyState;
