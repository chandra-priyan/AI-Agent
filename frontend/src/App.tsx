import React, { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { NewAnalysisPage } from './pages/NewAnalysisPage';
import { InvestigationPage } from './pages/InvestigationPage';
import { ResultsPage } from './pages/ResultsPage';
import { AIChatPage } from './pages/AIChatPage';
import { ReportPage } from './pages/ReportPage';
import { DatasetsPage } from './pages/DatasetsPage';
import { AnalysesPage } from './pages/AnalysesPage';
import { ReportsPage } from './pages/ReportsPage';
import { EmptyState } from './components/ui/EmptyState';
import { Plus } from 'lucide-react';

import { AnalysisSession, PageId } from './types';
import { getAnalysisHistory } from './services/analysisApi';

export function App() {
  // Requirement: "when i refesh the page on that time it need to go for login"
  // Default isLoggedIn to false on mount and clear auth token so page refresh always shows login screen
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [userEmail, setUserEmail] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisSession[]>([]);
  const [activeSession, setActiveSession] = useState<AnalysisSession | null>(null);

  useEffect(() => {
    localStorage.removeItem('auth_token');
  }, []);

  useEffect(() => {
    if (isLoggedIn) {
      getAnalysisHistory().then(history => {
        setRecentAnalyses(history);
        if (history.length > 0 && !activeSession) {
          setActiveSession(history[0]);
        }
      }).catch(console.warn);
    }
  }, [isLoggedIn]);

  const handleLoginSuccess = (email?: string) => {
    setIsLoggedIn(true);
    if (email) setUserEmail(email);
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserEmail('');
    localStorage.removeItem('auth_token');
    setCurrentPage('login');
  };

  const handleStartInvestigation = (session: AnalysisSession) => {
    setActiveSession(session);
    setCurrentPage('investigation');
  };

  const handleInvestigationComplete = (completedSession: AnalysisSession) => {
    setActiveSession(completedSession);
    setRecentAnalyses(prev => [completedSession, ...prev.filter(s => s.id !== completedSession.id)]);
    setCurrentPage('results');
  };

  if (!isLoggedIn || currentPage === 'login') {
    return <LoginPage onLogin={(email) => handleLoginSuccess(email)} />;
  }

  return (
    <div className="min-h-screen bg-[#FAFAFA] text-[#111111] flex font-sans antialiased selection:bg-[#6D28D9] selection:text-white">
      
      {/* Global Sidebar Navigation */}
      <Sidebar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        hasActiveAnalysis={!!activeSession}
        onLogout={handleLogout}
        userEmail={userEmail}
      />

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 max-h-screen overflow-hidden">
        
        {/* Header Bar */}
        <Header
          currentPage={currentPage}
        />

        {/* Main View Area */}
        <main className="flex-1 p-6 overflow-y-auto">
          
          {/* PAGE: DASHBOARD */}
          {currentPage === 'dashboard' && (
            <DashboardPage
              onStartNewAnalysis={() => setCurrentPage('new_analysis')}
              onSelectAnalysis={session => {
                setActiveSession(session);
                setCurrentPage('results');
              }}
              recentAnalyses={recentAnalyses}
            />
          )}

          {/* PAGE: NEW ANALYSIS */}
          {currentPage === 'new_analysis' && (
            <NewAnalysisPage onStartInvestigation={handleStartInvestigation} />
          )}

          {/* PAGE: INVESTIGATION */}
          {currentPage === 'investigation' && (
            activeSession ? (
              <InvestigationPage
                session={activeSession}
                onInvestigationComplete={handleInvestigationComplete}
              />
            ) : (
              <div className="max-w-2xl mx-auto py-12">
                <EmptyState
                  title="No Active Investigation"
                  description="Upload a CSV dataset and ask a question to start an autonomous data science investigation."
                  actionText="Start New Analysis"
                  actionIcon={<Plus className="w-4 h-4" />}
                  onAction={() => setCurrentPage('new_analysis')}
                />
              </div>
            )
          )}

          {/* PAGE: RESULTS */}
          {currentPage === 'results' && (
            activeSession ? (
              <ResultsPage
                session={activeSession}
                onAskFollowUp={() => setCurrentPage('ai_chat')}
                onGenerateReport={() => setCurrentPage('report')}
              />
            ) : (
              <div className="max-w-2xl mx-auto py-12">
                <EmptyState
                  title="No Analysis Selected"
                  description="Select a completed analysis from your dashboard or start a new analysis."
                  actionText="Start New Analysis"
                  actionIcon={<Plus className="w-4 h-4" />}
                  onAction={() => setCurrentPage('new_analysis')}
                />
              </div>
            )
          )}

          {/* PAGE: AI CHAT */}
          {currentPage === 'ai_chat' && (
            <AIChatPage
              session={activeSession}
              onGoToReport={() => setCurrentPage('report')}
              onStartNewAnalysis={() => setCurrentPage('new_analysis')}
            />
          )}

          {/* PAGE: REPORT */}
          {currentPage === 'report' && (
            <ReportPage
              session={activeSession}
              onStartNewAnalysis={() => setCurrentPage('new_analysis')}
            />
          )}

          {/* PAGE: DATASETS */}
          {currentPage === 'datasets' && (
            <DatasetsPage
              recentAnalyses={recentAnalyses}
              onStartNewAnalysis={() => setCurrentPage('new_analysis')}
              onSelectDatasetForAnalysis={() => setCurrentPage('new_analysis')}
            />
          )}

          {/* PAGE: ANALYSES */}
          {currentPage === 'analyses' && (
            <AnalysesPage
              recentAnalyses={recentAnalyses}
              onSelectAnalysis={session => {
                setActiveSession(session);
                setCurrentPage('results');
              }}
              onStartNewAnalysis={() => setCurrentPage('new_analysis')}
            />
          )}

          {/* PAGE: REPORTS */}
          {currentPage === 'reports' && (
            <ReportsPage
              recentAnalyses={recentAnalyses}
              onSelectReport={session => {
                setActiveSession(session);
                setCurrentPage('report');
              }}
              onStartNewAnalysis={() => setCurrentPage('new_analysis')}
            />
          )}

        </main>

      </div>

    </div>
  );
}

export default App;
