import React from 'react';
import { Button } from './Button';
import { TimelineFlowCanvas } from '../canvas/TimelineFlowCanvas';

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
    <div className={`bg-white border border-[#E5E7EB] rounded-2xl p-10 text-center flex flex-col items-center justify-center shadow-sm relative overflow-hidden ${className}`}>
      {/* Subtle Background Three.js Motion Canvas */}
      <TimelineFlowCanvas />

      <div className="w-16 h-16 rounded-2xl bg-[#F3E8FF] text-[#4F46E5] flex items-center justify-center mb-4 text-2xl font-bold relative z-10 shadow-xs">
        📊
      </div>
      <h3 className="text-lg font-bold text-[#111827] mb-2 relative z-10">{title}</h3>
      <p className="text-sm text-[#6B7280] max-w-md mb-6 relative z-10">{description}</p>
      {actionText && onAction && (
        <Button variant="primary" icon={actionIcon} onClick={onAction} className="relative z-10 font-bold bg-[#4F46E5] hover:bg-[#4338CA] text-white cursor-pointer">
          {actionText}
        </Button>
      )}
    </div>
  );
}

export default EmptyState;
