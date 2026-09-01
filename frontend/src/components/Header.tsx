import React from 'react';
import { Menu, Sparkles, User, Bell } from 'lucide-react';
import { PageId } from '../types';

export interface HeaderProps {
  currentPage: PageId;
  onOpenMobileSidebar?: () => void;
}

const PAGE_TITLES: Record<PageId, { title: string; subtitle: string }> = {
  dashboard: { title: 'Dashboard', subtitle: 'Overview of recent investigations and dataset insights' },
  new_analysis: { title: 'New Analysis', subtitle: 'Upload a CSV dataset and ask questions for AI investigation' },
  investigation: { title: 'Autonomous Investigation', subtitle: 'Live agent execution, statistical profiling, and hypothesis testing' },
  results: { title: 'Analysis Results', subtitle: 'Key statistical findings, correlations, and executive summaries' },
  ai_chat: { title: 'Interactive AI Analyst', subtitle: 'Ask follow-up questions about your data analysis findings' },
  report: { title: 'Executive Report', subtitle: 'Comprehensive data analysis report ready for export' },
  datasets: { title: 'Datasets Library', subtitle: 'Manage uploaded CSV files and dataset metadata' },
  analyses: { title: 'All Analyses', subtitle: 'History of autonomous investigations and sessions' },
  reports: { title: 'Saved Reports', subtitle: 'Exportable decision documents and findings' },
  login: { title: 'Authentication', subtitle: 'Sign in to Autonomous Data Scientist' },
};

export function Header({ currentPage, onOpenMobileSidebar }: HeaderProps) {
  const info = PAGE_TITLES[currentPage] || { title: 'Autonomous Data Scientist', subtitle: 'AI-Powered Data Science Engine' };

  return (
    <header className="h-16 bg-white border-b border-[#E5E7EB] px-6 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-3">
        {onOpenMobileSidebar && (
          <button
            onClick={onOpenMobileSidebar}
            className="md:hidden p-2 rounded-lg text-[#6B7280] hover:bg-[#F3F4F6] transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <div>
          <h2 className="text-base font-bold text-[#111827]">{info.title}</h2>
          <p className="text-xs text-[#6B7280] hidden sm:block">{info.subtitle}</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#F3E8FF] text-[#6D28D9] text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Local Engine Ready</span>
        </div>

        <button className="p-2 rounded-lg text-[#6B7280] hover:bg-[#F3F4F6] transition-colors relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#6D28D9]"></span>
        </button>

        <div className="flex items-center gap-2 pl-3 border-l border-[#E5E7EB]">
          <div className="w-8 h-8 rounded-full bg-[#6D28D9] text-white font-bold text-xs flex items-center justify-center shadow-xs">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
