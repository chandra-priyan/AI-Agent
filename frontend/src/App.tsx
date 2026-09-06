import React, { useEffect, useState } from 'react';
import { TopNavbar } from './components/TopNavbar';
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
import { MOCK_ANALYSES } from './utils/testData';

import { AnalysisSession, PageId } from './types';
import { getAnalysisHistory } from './services/analysisApi';

export function App() {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [userEmail, setUserEmail] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisSession[]>(MOCK_ANALYSES);
  const [activeSession, setActiveSession] = useState<AnalysisSession | null>(MOCK_ANALYSES[0]);

  useEffect(() => {
    localStorage.removeItem('auth_token');
  }, []);

  useEffect(() => {
    if (isLoggedIn) {
      getAnalysisHistory()
        .then((history) => {
          if (history && history.length > 0) {
            setRecentAnalyses(history);
            setActiveSession(history[0]);
          } else {
            setRecentAnalyses(MOCK_ANALYSES);
          }
        })
        .catch(() => {
          setRecentAnalyses(MOCK_ANALYSES);
        });
    }
  }, [isLoggedIn]);

  const handleLoginSuccess = (email?: string) => {
    if (email) setUserEmail(email);
    setIsLoggedIn(true);
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    setIsLoggedIn(false);
    setUserEmail('');
    setCurrentPage('login');
  };

  const handleStartInvestigation = (session: AnalysisSession) => {
    setActiveSession(session);
    setCurrentPage('investigation');
  };

  const handleInvestigationComplete = (completedSession: AnalysisSession) => {
    setActiveSession(completedSession);
    setRecentAnalyses((prev) => [completedSession, ...prev.filter((s) => s.id !== completedSession.id)]);
    setCurrentPage('results');
  };

  if (!isLoggedIn || currentPage === 'login') {
    return <LoginPage onLogin={(email) => handleLoginSuccess(email)} />;
  }

  return (
    <div className="min-h-screen bg-[#F7F7FA] text-[#111111] flex flex-col font-sans antialiased selection:bg-[#4F46E5] selection:text-white">
      {/* Top Navigation Bar */}
      <TopNavbar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        hasActiveAnalysis={!!activeSession}
        onLogout={handleLogout}
        userEmail={userEmail}
      />

      {/* Main View Area */}
      <main className="flex-1 p-4 md:p-8 max-w-[1700px] w-full mx-auto overflow-y-auto">
        {/* PAGE: DASHBOARD */}
        {currentPage === 'dashboard' && (
          <DashboardPage
            onStartNewAnalysis={() => setCurrentPage('new_analysis')}
            onSelectAnalysis={(session) => {
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
          <InvestigationPage
            session={activeSession || MOCK_ANALYSES[0]}
            onInvestigationComplete={handleInvestigationComplete}
          />
        )}

        {/* PAGE: RESULTS */}
        {currentPage === 'results' && (
          <ResultsPage
            session={activeSession || MOCK_ANALYSES[0]}
            onAskFollowUp={() => setCurrentPage('ai_chat')}
            onGenerateReport={() => setCurrentPage('report')}
          />
        )}

        {/* PAGE: AI CHAT */}
        {currentPage === 'ai_chat' && (
          <AIChatPage
            session={activeSession || MOCK_ANALYSES[0]}
            onGoToReport={() => setCurrentPage('report')}
            onStartNewAnalysis={() => setCurrentPage('new_analysis')}
          />
        )}

        {/* PAGE: REPORT */}
        {currentPage === 'report' && (
          <ReportPage
            session={activeSession || MOCK_ANALYSES[0]}
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
            onSelectAnalysis={(session) => {
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
            onSelectReport={(session) => {
              setActiveSession(session);
              setCurrentPage('report');
            }}
            onStartNewAnalysis={() => setCurrentPage('new_analysis')}
          />
        )}
      </main>
    </div>
  );
}

export default App;
