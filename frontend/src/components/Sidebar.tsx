import React, { useState } from 'react';
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
  Settings,
  HelpCircle,
  X,
  ChevronRight,
} from 'lucide-react';
import { PageId } from '../types';

export interface SidebarProps {
  currentPage: PageId;
  setCurrentPage: (page: PageId) => void;
  hasActiveAnalysis: boolean;
  onLogout: () => void;
  userEmail?: string;
  isOpenMobile?: boolean;
  onCloseMobile?: () => void;
}

export function Sidebar({
  currentPage,
  setCurrentPage,
  hasActiveAnalysis,
  onLogout,
  userEmail,
  isOpenMobile,
  onCloseMobile,
}: SidebarProps) {
  const [showHelpModal, setShowHelpModal] = useState(false);

  // Format user display name from email or default to Chandra
  const rawEmail = userEmail || 'chandra@datascientist.ai';
  const namePart = rawEmail.split('@')[0];
  const userName = namePart.charAt(0).toUpperCase() + namePart.slice(1);

  const workspaceNav = [
    { id: 'dashboard' as PageId, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'new_analysis' as PageId, label: 'New Analysis', icon: PlusCircle },
    {
      id: 'investigation' as PageId,
      label: 'Investigation',
      icon: Activity,
      hasActive: hasActiveAnalysis,
    },
    { id: 'results' as PageId, label: 'Results', icon: BarChart3 },
    { id: 'ai_chat' as PageId, label: 'AI Chat', icon: MessageSquare },
    { id: 'report' as PageId, label: 'Executive Report', icon: FileText },
  ];

  const libraryNav = [
    { id: 'datasets' as PageId, label: 'Datasets', icon: Database },
    { id: 'analyses' as PageId, label: 'All Analyses', icon: History },
    { id: 'reports' as PageId, label: 'Saved Reports', icon: FileText },
  ];

  const handleNavClick = (pageId: PageId) => {
    setCurrentPage(pageId);
    if (onCloseMobile) onCloseMobile();
  };

  const sidebarContent = (
    <aside className="w-[260px] bg-[#0F1115] text-[#F4F4F5] flex flex-col h-screen shrink-0 border-r border-[#272B33] select-none font-sans">
      {/* 1. USER PROFILE — VERY TOP */}
      <div className="p-3 border-b border-[#272B33]">
        <div className="bg-[#161A21] border border-[#272B33] rounded-lg p-2.5 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="relative shrink-0">
              <div className="w-9 h-9 rounded-md bg-[#7C3AED] text-white font-semibold text-sm flex items-center justify-center shadow-xs">
                {userName.charAt(0)}
              </div>
              <span
                className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-[#22C55E] border-2 border-[#161A21]"
                title="Online"
              />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-[#F4F4F5] truncate leading-snug">
                {userName}
              </p>
              <p className="text-[11px] text-[#A1A1AA] font-normal truncate">
                Lead AI Analyst
              </p>
            </div>
          </div>

          <button
            onClick={onLogout}
            title="Log Out of Workspace"
            aria-label="Log Out"
            className="p-1.5 rounded-md text-[#A1A1AA] hover:text-[#EF4444] hover:bg-[#272B33] transition-colors shrink-0 cursor-pointer"
          >
            <LogOut className="w-4 h-4" strokeWidth={1.75} />
          </button>
        </div>
      </div>

      {/* 2. BRANDING AREA */}
      <div className="p-4 border-b border-[#272B33] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-[#161A21] border border-[#272B33] flex items-center justify-center shrink-0">
            <Sparkles className="w-4 h-4 text-[#7C3AED]" strokeWidth={2} />
          </div>
          <div>
            <h1 className="text-[15px] font-bold text-[#F4F4F5] leading-tight tracking-tight">
              DataScientist.AI
            </h1>
            <p className="text-[11px] text-[#A1A1AA] font-normal">
              Autonomous Analytics Engine
            </p>
          </div>
        </div>

        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            aria-label="Close sidebar"
            className="md:hidden text-[#A1A1AA] hover:text-[#F4F4F5] p-1 rounded-md"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* 3. TOP SECONDARY NAVIGATION: SETTINGS & HELP */}
      <div className="px-3 py-2.5 border-b border-[#272B33] space-y-1">
        <button
          onClick={() => handleNavClick('settings')}
          className={`w-full relative flex items-center gap-2.5 h-9 px-3 rounded-[7px] text-sm font-medium transition-all cursor-pointer ${
            currentPage === 'settings'
              ? 'bg-[#241A3A] text-white'
              : 'text-[#A1A1AA] hover:bg-[#161A21] hover:text-[#F4F4F5]'
          }`}
        >
          {currentPage === 'settings' && (
            <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r bg-[#7C3AED]" />
          )}
          <Settings
            className={`w-[18px] h-[18px] pl-1 ${
              currentPage === 'settings' ? 'text-white' : 'text-[#A1A1AA]'
            }`}
            strokeWidth={1.75}
          />
          <span>Settings</span>
        </button>

        <button
          onClick={() => setShowHelpModal(true)}
          className="w-full flex items-center justify-between h-9 px-3 rounded-[7px] text-sm font-medium text-[#A1A1AA] hover:bg-[#161A21] hover:text-[#F4F4F5] transition-all cursor-pointer"
        >
          <div className="flex items-center gap-2.5 pl-1">
            <HelpCircle className="w-[18px] h-[18px] text-[#A1A1AA]" strokeWidth={1.75} />
            <span>Help & Support</span>
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-[#71717A]" />
        </button>
      </div>

      {/* 4. NAVIGATION SECTIONS */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {/* WORKSPACE */}
        <div>
          <div className="px-2 mb-2 text-[11px] font-semibold tracking-[0.08em] text-[#71717A] uppercase">
            WORKSPACE
          </div>
          <nav className="space-y-1">
            {workspaceNav.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  className={`w-full relative flex items-center justify-between h-10 px-3 rounded-[7px] text-sm font-medium transition-all cursor-pointer ${
                    isActive
                      ? 'bg-[#241A3A] text-white'
                      : 'text-[#A1A1AA] hover:bg-[#161A21] hover:text-[#F4F4F5]'
                  }`}
                >
                  {/* Active Indicator Line */}
                  {isActive && (
                    <span className="absolute left-0 top-2 bottom-2 w-1 rounded-r bg-[#7C3AED]" />
                  )}

                  <div className="flex items-center gap-2.5 pl-1">
                    <Icon
                      className={`w-[18px] h-[18px] ${
                        isActive ? 'text-white' : 'text-[#A1A1AA]'
                      }`}
                      strokeWidth={1.75}
                    />
                    <span>{item.label}</span>
                  </div>

                  {/* Status Indicator for Investigation */}
                  {item.hasActive && (
                    <span
                      className="w-2 h-2 rounded-full bg-[#F59E0B]"
                      title="Active Investigation Running"
                    />
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* LIBRARY */}
        <div>
          <div className="px-2 mb-2 text-[11px] font-semibold tracking-[0.08em] text-[#71717A] uppercase">
            LIBRARY
          </div>
          <nav className="space-y-1">
            {libraryNav.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  className={`w-full relative flex items-center gap-2.5 h-10 px-3 rounded-[7px] text-sm font-medium transition-all cursor-pointer ${
                    isActive
                      ? 'bg-[#241A3A] text-white'
                      : 'text-[#A1A1AA] hover:bg-[#161A21] hover:text-[#F4F4F5]'
                  }`}
                >
                  {isActive && (
                    <span className="absolute left-0 top-2 bottom-2 w-1 rounded-r bg-[#7C3AED]" />
                  )}
                  <Icon
                    className={`w-[18px] h-[18px] pl-1 ${
                      isActive ? 'text-white' : 'text-[#A1A1AA]'
                    }`}
                    strokeWidth={1.75}
                  />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* HELP & SUPPORT MODAL */}
      {showHelpModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#161A21] border border-[#272B33] text-[#F4F4F5] rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#272B33] pb-3">
              <div className="flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-[#7C3AED]" />
                <h3 className="text-base font-bold">Help & Support</h3>
              </div>
              <button
                onClick={() => setShowHelpModal(false)}
                className="text-[#A1A1AA] hover:text-white p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-sm text-[#A1A1AA]">
              <p>
                <strong className="text-white">DataScientist.AI Engine v2.4</strong>
              </p>
              <p>
                Autonomous data analytics pipeline powered by local statistical engines (Pandas/SciPy) and AI agent reasoning.
              </p>

              <div className="bg-[#0F1115] border border-[#272B33] rounded-lg p-3 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-[#71717A]">Documentation</span>
                  <span className="text-[#7C3AED] font-semibold">docs.datascientist.ai</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#71717A]">Support Email</span>
                  <span className="text-white font-medium">support@datascientist.ai</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#71717A]">Engine Status</span>
                  <span className="text-[#22C55E] font-medium">● Local Ollama Active</span>
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowHelpModal(false)}
                className="px-4 py-2 bg-[#7C3AED] hover:bg-[#8B5CF6] text-white text-xs font-semibold rounded-lg transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <div className="hidden md:block">{sidebarContent}</div>

      {/* Mobile Drawer Sidebar */}
      {isOpenMobile && (
        <div className="fixed inset-0 z-40 flex md:hidden">
          <div
            className="fixed inset-0 bg-black/60"
            onClick={onCloseMobile}
          />
          <div className="relative z-50">{sidebarContent}</div>
        </div>
      )}
    </>
  );
}

export default Sidebar;
