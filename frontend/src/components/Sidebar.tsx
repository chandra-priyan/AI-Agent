import React from 'react';
import {
  LayoutDashboard,
  PlusCircle,
  Activity,
  BarChart3,
  MessageSquare,
  FileText,
  Database,
  History,
  LogOut,
  Sparkles,
  User,
} from 'lucide-react';
import { PageId } from '../types';

export interface SidebarProps {
  currentPage: PageId;
  setCurrentPage: (page: PageId) => void;
  hasActiveAnalysis: boolean;
  onLogout: () => void;
  userEmail?: string;
}

export function Sidebar({ currentPage, setCurrentPage, hasActiveAnalysis, onLogout, userEmail }: SidebarProps) {
  const mainNav = [
    { id: 'dashboard' as PageId, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'new_analysis' as PageId, label: 'New Analysis', icon: PlusCircle },
    { id: 'investigation' as PageId, label: 'Investigation', icon: Activity, badge: hasActiveAnalysis ? 'Active' : undefined },
    { id: 'results' as PageId, label: 'Results', icon: BarChart3 },
    { id: 'ai_chat' as PageId, label: 'AI Chat Analyst', icon: MessageSquare },
    { id: 'report' as PageId, label: 'Executive Report', icon: FileText },
  ];

  const libraryNav = [
    { id: 'datasets' as PageId, label: 'Datasets', icon: Database },
    { id: 'analyses' as PageId, label: 'All Analyses', icon: History },
    { id: 'reports' as PageId, label: 'Saved Reports', icon: FileText },
  ];

  const displayEmail = userEmail || 'analyst@datascientist.ai';

  return (
    <aside className="w-64 bg-[#0F0F12] text-white flex flex-col h-screen shrink-0 border-r border-gray-800/80 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-gray-800/80 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#6D28D9] to-[#8B5CF6] flex items-center justify-center shadow-lg shadow-[#6D28D9]/30">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-sm text-white tracking-wide">DataScientist.AI</h1>
          <p className="text-[10px] text-gray-400 font-medium">Autonomous Analytics Engine</p>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        <div>
          <div className="px-3 mb-2 text-[10px] font-bold tracking-wider text-gray-500 uppercase">
            Workspace
          </div>
          <nav className="space-y-1">
            {mainNav.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentPage(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                    isActive
                      ? 'bg-[#6D28D9] text-white font-semibold shadow-md shadow-[#6D28D9]/25'
                      : 'text-gray-400 hover:bg-gray-800/60 hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-gray-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        <div>
          <div className="px-3 mb-2 text-[10px] font-bold tracking-wider text-gray-500 uppercase">
            Library
          </div>
          <nav className="space-y-1">
            {libraryNav.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentPage(item.id)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                    isActive
                      ? 'bg-[#6D28D9] text-white font-semibold shadow-md shadow-[#6D28D9]/25'
                      : 'text-gray-400 hover:bg-gray-800/60 hover:text-white'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-gray-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Professional Footer / User Profile Card */}
      <div className="p-3 border-t border-gray-800/80">
        <div className="bg-[#18181C] border border-gray-800/80 rounded-xl p-3 flex items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="relative">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-[#6D28D9] to-[#8B5CF6] text-white font-bold text-xs flex items-center justify-center shrink-0">
                <User className="w-4 h-4" />
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-[#18181C]" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold text-gray-200 truncate">{displayEmail}</p>
              <p className="text-[10px] text-gray-500 font-medium">Lead AI Analyst</p>
            </div>
          </div>

          <button
            onClick={onLogout}
            title="Log Out of Workspace"
            className="p-2 rounded-lg text-gray-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors shrink-0 cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
