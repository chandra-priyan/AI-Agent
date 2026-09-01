import React from 'react';
import { History, Plus, ArrowRight } from 'lucide-react';
import { AnalysisSession } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { StatusBadge } from '../components/ui/StatusBadge';
import { MOCK_ANALYSES } from '../utils/testData';
import { TimelineFlowCanvas } from '../components/canvas/TimelineFlowCanvas';

export interface AnalysesPageProps {
  recentAnalyses: AnalysisSession[];
  onSelectAnalysis: (session: AnalysisSession) => void;
  onStartNewAnalysis: () => void;
}

export function AnalysesPage({ recentAnalyses, onSelectAnalysis, onStartNewAnalysis }: AnalysesPageProps) {
  const displayList = recentAnalyses.length > 0 ? recentAnalyses : MOCK_ANALYSES;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header Banner with Three.js Timeline Flow Canvas */}
      <div className="bg-[#111115] rounded-2xl p-6 text-white shadow-xl relative overflow-hidden flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border border-gray-800">
        {/* Three.js Timeline Canvas Layer */}
        <TimelineFlowCanvas />

        <div className="relative z-10 pointer-events-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-purple-300 text-xs font-semibold backdrop-blur-md mb-2 border border-white/10">
            <History className="w-3.5 h-3.5" />
            <span>Timeline Data Flow</span>
          </div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">All Autonomous Analyses</h1>
          <p className="text-xs text-gray-400 mt-1">Historical catalog of AI investigation sessions, hypotheses, and conclusions.</p>
        </div>

        <div className="relative z-10 shrink-0 pointer-events-auto">
          <Button
            variant="primary"
            icon={<Plus className="w-4 h-4" />}
            onClick={onStartNewAnalysis}
            className="bg-[#4F46E5] hover:bg-[#4338CA] text-white font-bold cursor-pointer"
          >
            Start New Investigation
          </Button>
        </div>
      </div>

      <div className="space-y-3">
        {displayList.map((session) => (
          <Card
            key={session.id}
            hoverable
            onClick={() => onSelectAnalysis(session)}
            className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 cursor-pointer"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-3">
                <span className="font-bold text-[#111827]">{session.datasetName}</span>
                <StatusBadge status={session.status} />
              </div>
              <p className="text-sm text-gray-600 font-medium">{session.question}</p>
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
                Open Session
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default AnalysesPage;
