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
            setActiveSession(MOCK_ANALYSES[0]);
          }
        })
        .catch(() => {
          setRecentAnalyses(MOCK_ANALYSES);
          setActiveSession(MOCK_ANALYSES[0]);
        });
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
    setRecentAnalyses((prev) => [completedSession, ...prev.filter((s) => s.id !== completedSession.id)]);
    setCurrentPage('results');
  };

  if (!isLoggedIn || currentPage === 'login') {
    return <LoginPage onLogin={(email) => handleLoginSuccess(email)} />;
  }

  return (
    <div className="min-h-screen bg-[#FAFAFA] text-[#111111] flex font-sans antialiased selection:bg-[#4F46E5] selection:text-white">
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
        <Header currentPage={currentPage} />

        {/* Main View Area */}
        <main className="flex-1 p-6 overflow-y-auto">
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
    </div>
  );
}

export default App;
