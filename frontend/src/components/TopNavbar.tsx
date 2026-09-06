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
  Menu,
  X,
  Calendar,
  Zap,
} from 'lucide-react';
import { PageId } from '../types';
import { getFormattedDate } from '../utils/dateUtils';

export interface TopNavbarProps {
  currentPage: PageId;
  setCurrentPage: (page: PageId) => void;
  hasActiveAnalysis: boolean;
  onLogout: () => void;
  userEmail?: string;
}

export function TopNavbar({
  currentPage,
  setCurrentPage,
  hasActiveAnalysis,
  onLogout,
  userEmail,
}: TopNavbarProps) {
  const [showHelpModal, setShowHelpModal] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const rawEmail = userEmail || 'chandra@dataagent.ai';
  const namePart = rawEmail.split('@')[0];
  const userName = namePart.charAt(0).toUpperCase() + namePart.slice(1);
  const todayFormatted = getFormattedDate();

  const mainNav = [
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
    setMobileMenuOpen(false);
  };

  return (
    <header className="w-full bg-[#0F1115] text-[#F4F4F5] border-b border-[#272B33] select-none font-sans sticky top-0 z-40">
      <div className="max-w-[1700px] mx-auto px-4 h-16 flex items-center justify-between gap-4">
        {/* BRAND LOGO AREA */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-[#161A21] border border-[#272B33] flex items-center justify-center shrink-0 shadow-xs">
            <Sparkles className="w-4 h-4 text-[#7C3AED]" strokeWidth={2} />
          </div>
          <div>
            <h1 className="text-sm md:text-[15px] font-bold text-[#F4F4F5] leading-tight tracking-tight">
              DataAgent.AI
            </h1>
            <p className="text-[10px] md:text-[11px] text-[#A1A1AA] font-normal">
              Analytics Engine
            </p>
          </div>
        </div>

        {/* DESKTOP MAIN HORIZONTAL NAVIGATION */}
        <nav className="hidden lg:flex items-center gap-1 overflow-x-auto py-1 scrollbar-none">
          {mainNav.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`relative flex items-center gap-2 h-9 px-3 rounded-lg text-xs md:text-sm font-medium transition-all whitespace-nowrap cursor-pointer ${
                  isActive
                    ? 'bg-[#241A3A] text-white shadow-xs'
                    : 'text-[#A1A1AA] hover:bg-[#161A21] hover:text-[#F4F4F5]'
                }`}
              >
                {isActive && (
                  <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-[#7C3AED] rounded-t-full" />
                )}
                <Icon
                  className={`w-4 h-4 ${isActive ? 'text-white' : 'text-[#A1A1AA]'}`}
                  strokeWidth={1.75}
                />
                <span>{item.label}</span>
                {item.hasActive && (
                  <span
                    className="w-1.5 h-1.5 rounded-full bg-[#F59E0B]"
                    title="Active Investigation Running"
                  />
                )}
              </button>
            );
          })}

          <div className="h-4 w-px bg-[#272B33] mx-1" />

          {libraryNav.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`relative flex items-center gap-2 h-9 px-3 rounded-lg text-xs md:text-sm font-medium transition-all whitespace-nowrap cursor-pointer ${
                  isActive
                    ? 'bg-[#241A3A] text-white shadow-xs'
                    : 'text-[#A1A1AA] hover:bg-[#161A21] hover:text-[#F4F4F5]'
                }`}
              >
                {isActive && (
                  <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-[#7C3AED] rounded-t-full" />
                )}
                <Icon
                  className={`w-4 h-4 ${isActive ? 'text-white' : 'text-[#A1A1AA]'}`}
                  strokeWidth={1.75}
                />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* RIGHT ACTION & USER PROFILE AREA */}
        <div className="flex items-center gap-2.5 shrink-0">
          {/* Status Badge */}
          <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#161A21] border border-[#272B33] text-[11px] font-medium text-[#A1A1AA]">
            <Zap className="w-3.5 h-3.5 text-[#7C3AED]" />
            <span className="text-[#22C55E]">Local Engine Active</span>
          </div>

          {/* Date Badge */}
          <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#161A21] border border-[#272B33] text-[11px] font-medium text-[#A1A1AA]">
            <Calendar className="w-3.5 h-3.5 text-[#71717A]" />
            <span>{todayFormatted}</span>
          </div>

          {/* Settings Button */}
          <button
            onClick={() => handleNavClick('settings')}
            title="Settings"
            className={`p-2 rounded-lg transition-colors cursor-pointer ${
              currentPage === 'settings'
                ? 'bg-[#241A3A] text-white border border-[#7C3AED]/40'
                : 'text-[#A1A1AA] hover:text-[#F4F4F5] hover:bg-[#161A21]'
            }`}
          >
            <Settings className="w-4 h-4" strokeWidth={1.75} />
          </button>

          {/* Help Button */}
          <button
            onClick={() => setShowHelpModal(true)}
            title="Help & Support"
            className="p-2 rounded-lg text-[#A1A1AA] hover:text-[#F4F4F5] hover:bg-[#161A21] transition-colors cursor-pointer"
          >
            <HelpCircle className="w-4 h-4" strokeWidth={1.75} />
          </button>

          {/* User Profile Card */}
          <div className="flex items-center gap-2 bg-[#161A21] border border-[#272B33] rounded-lg p-1.5 pl-2">
            <div className="relative shrink-0">
              <div className="w-7 h-7 rounded-md bg-[#7C3AED] text-white font-semibold text-xs flex items-center justify-center">
                {userName.charAt(0)}
              </div>
              <span
                className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-[#22C55E] border border-[#161A21]"
                title="Online"
              />
            </div>

            <div className="hidden sm:block min-w-0 pr-1">
              <p className="text-xs font-semibold text-[#F4F4F5] truncate leading-tight">
                {userName}
              </p>
              <p className="text-[10px] text-[#A1A1AA] truncate leading-tight">
                Lead AI Analyst
              </p>
            </div>

            <button
              onClick={onLogout}
              title="Log Out"
              aria-label="Log Out"
              className="p-1 rounded-md text-[#A1A1AA] hover:text-[#EF4444] hover:bg-[#272B33] transition-colors cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" strokeWidth={1.75} />
            </button>
          </div>

          {/* Mobile Hamburger Toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-lg text-[#A1A1AA] hover:text-[#F4F4F5] hover:bg-[#161A21] cursor-pointer"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* MOBILE EXPANDED MENU DRAWER */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-[#0F1115] border-t border-[#272B33] px-4 py-3 space-y-4">
          <div>
            <div className="px-2 mb-2 text-[10px] font-semibold tracking-wider text-[#71717A] uppercase">
              Workspace Navigation
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {mainNav.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavClick(item.id)}
                    className={`flex items-center gap-2.5 h-9 px-3 rounded-lg text-xs font-medium ${
                      isActive
                        ? 'bg-[#241A3A] text-white'
                        : 'text-[#A1A1AA] hover:bg-[#161A21] hover:text-[#F4F4F5]'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <div className="px-2 mb-2 text-[10px] font-semibold tracking-wider text-[#71717A] uppercase">
              Library & Settings
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {libraryNav.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavClick(item.id)}
                    className={`flex items-center gap-2.5 h-9 px-3 rounded-lg text-xs font-medium ${
                      isActive
                        ? 'bg-[#241A3A] text-white'
                        : 'text-[#A1A1AA] hover:bg-[#161A21] hover:text-[#F4F4F5]'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </button>
                );
              })}

              <button
                onClick={() => handleNavClick('settings')}
                className={`flex items-center gap-2.5 h-9 px-3 rounded-lg text-xs font-medium ${
                  currentPage === 'settings'
                    ? 'bg-[#241A3A] text-white'
                    : 'text-[#A1A1AA] hover:bg-[#161A21] hover:text-[#F4F4F5]'
                }`}
              >
                <Settings className="w-4 h-4" />
                <span>Settings</span>
              </button>
            </div>
          </div>
        </div>
      )}

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
                <strong className="text-white">DataAgent.AI Engine v2.5</strong>
              </p>
              <p>
                Data analytics pipeline powered by local statistical engines (Pandas/SciPy) and AI agent reasoning.
              </p>

              <div className="bg-[#0F1115] border border-[#272B33] rounded-lg p-3 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-[#71717A]">Documentation</span>
                  <span className="text-[#7C3AED] font-semibold">docs.dataagent.ai</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#71717A]">Support Email</span>
                  <span className="text-white font-medium">support@dataagent.ai</span>
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
    </header>
  );
}

export default TopNavbar;
