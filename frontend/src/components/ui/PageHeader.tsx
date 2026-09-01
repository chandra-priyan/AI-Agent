import React from 'react';

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export function PageHeader({ title, subtitle, action }: PageHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-[#E5E7EB]">
      <div>
        <h1 className="text-2xl font-bold text-[#111827] tracking-tight">{title}</h1>
        {subtitle && <p className="text-sm text-[#6B7280] mt-1">{subtitle}</p>}
      </div>
      {action && <div className="flex items-center gap-3 shrink-0">{action}</div>}
    </div>
  );
}

export default PageHeader;
