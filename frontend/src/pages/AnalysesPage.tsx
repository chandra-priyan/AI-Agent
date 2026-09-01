import React from 'react';
import { History, Plus, ArrowRight } from 'lucide-react';
import { AnalysisSession } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { StatusBadge } from '../components/ui/StatusBadge';
import { MOCK_ANALYSES } from '../utils/testData';

export interface AnalysesPageProps {
  recentAnalyses: AnalysisSession[];
  onSelectAnalysis: (session: AnalysisSession) => void;
  onStartNewAnalysis: () => void;
}

export function AnalysesPage({ recentAnalyses, onSelectAnalysis, onStartNewAnalysis }: AnalysesPageProps) {
  const displayList = recentAnalyses.length > 0 ? recentAnalyses : MOCK_ANALYSES;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <PageHeader
        title="All Autonomous Analyses"
        subtitle="Historical catalog of AI investigation sessions and findings"
        action={
          <Button variant="primary" icon={<Plus className="w-4 h-4" />} onClick={onStartNewAnalysis}>
            Start New Investigation
          </Button>
        }
      />

      <div className="space-y-3">
        {displayList.map((session) => (
          <Card
            key={session.id}
            hoverable
            onClick={() => onSelectAnalysis(session)}
            className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5"
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
