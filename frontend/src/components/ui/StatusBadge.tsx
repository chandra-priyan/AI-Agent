import React from 'react';
import { Badge } from './Badge';

export interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const normalized = (status || '').toUpperCase();

  switch (normalized) {
    case 'COMPLETED':
    case 'SUCCESS':
      return <Badge variant="green" className={className}>Completed</Badge>;
    case 'RUNNING':
    case 'IN_PROGRESS':
      return <Badge variant="violet" className={className}>Running</Badge>;
    case 'QUEUED':
    case 'CREATED':
    case 'PENDING':
      return <Badge variant="amber" className={className}>Queued</Badge>;
    case 'FAILED':
    case 'ERROR':
      return <Badge variant="red" className={className}>Failed</Badge>;
    case 'CANCELLED':
      return <Badge variant="gray" className={className}>Cancelled</Badge>;
    default:
      return <Badge variant="gray" className={className}>{status}</Badge>;
  }
}

export default StatusBadge;
