import React from 'react';
import { Plus, BarChart3, Database, Activity, Sparkles, ArrowRight, Clock } from 'lucide-react';
import { AnalysisSession } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { StatusBadge } from '../components/ui/StatusBadge';
import { MOCK_ANALYSES } from '../utils/testData';

export interface DashboardPageProps {
  onStartNewAnalysis: () => void;
  onSelectAnalysis: (session: AnalysisSession) => void;
  recentAnalyses: AnalysisSession[];
}

export function DashboardPage({ onStartNewAnalysis, onSelectAnalysis, recentAnalyses }: DashboardPageProps) {
  const displayList = recentAnalyses.length > 0 ? recentAnalyses : MOCK_ANALYSES;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Hero Quick Banner */}
      <div className="bg-gradient-to-r from-[#111111] via-[#1E1B4B] to-[#6D28D9] rounded-2xl p-8 text-white shadow-xl relative overflow-hidden flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-white text-xs font-semibold backdrop-blur-md mb-3 border border-white/10">
            <Sparkles className="w-3.5 h-3.5 text-purple-300" />
            <span>Autonomous AI Scientist</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight">
            Transform Raw Data into Verified Decision Science
          </h1>
          <p className="text-sm text-gray-300 mt-2 leading-relaxed">
            Upload CSV datasets to run automated hypothesis testing, statistical regression, correlation heatmaps, and executive AI conclusions.
          </p>
        </div>
        <div className="relative z-10 shrink-0">
          <Button
            variant="primary"
            size="lg"
            icon={<Plus className="w-5 h-5" />}
            onClick={onStartNewAnalysis}
            className="bg-white text-[#6D28D9] hover:bg-gray-100 shadow-lg font-bold"
          >
            Start New Investigation
          </Button>
        </div>
      </div>

      {/* Overview Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-purple-100 text-[#6D28D9] flex items-center justify-center font-bold">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total Analyses</p>
            <p className="text-2xl font-bold text-gray-900">{displayList.length}</p>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Completed Jobs</p>
            <p className="text-2xl font-bold text-gray-900">
              {displayList.filter(s => s.status === 'COMPLETED').length}
            </p>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center font-bold">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Active Datasets</p>
            <p className="text-2xl font-bold text-gray-900">{displayList.length}</p>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center font-bold">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">AI Confidence</p>
            <p className="text-2xl font-bold text-gray-900">High (98%)</p>
          </div>
        </Card>
      </div>

      {/* Recent Investigations List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <Clock className="w-5 h-5 text-[#6D28D9]" />
            <span>Recent Data Investigations</span>
          </h2>
          <Button variant="ghost" size="sm" onClick={onStartNewAnalysis}>
            Create New <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Button>
        </div>

        <div className="grid grid-cols-1 gap-3">
          {displayList.map((session) => (
            <Card
              key={session.id}
              hoverable
              onClick={() => onSelectAnalysis(session)}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-base text-gray-900">{session.datasetName}</span>
                  <StatusBadge status={session.status} />
                </div>
                <p className="text-sm text-gray-600 line-clamp-1">{session.question}</p>
                {session.conclusion && (
                  <p className="text-xs text-gray-500 italic line-clamp-1">"{session.conclusion}"</p>
                )}
              </div>

              <div className="flex items-center gap-4 shrink-0 border-t sm:border-t-0 pt-3 sm:pt-0 border-gray-100">
                <div className="text-right hidden sm:block">
                  <p className="text-xs text-gray-400">Created</p>
                  <p className="text-xs font-semibold text-gray-700">{session.createdAt}</p>
                </div>
                <Button variant="outline" size="sm" icon={<ArrowRight className="w-3.5 h-3.5" />}>
                  View Findings
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
