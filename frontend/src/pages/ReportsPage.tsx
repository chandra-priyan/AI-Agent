import React from 'react';
import { FileText, Plus, ArrowRight, Download } from 'lucide-react';
import { AnalysisSession } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { MOCK_ANALYSES } from '../utils/testData';

export interface ReportsPageProps {
  recentAnalyses: AnalysisSession[];
  onSelectReport: (session: AnalysisSession) => void;
  onStartNewAnalysis: () => void;
}

export function ReportsPage({ recentAnalyses, onSelectReport, onStartNewAnalysis }: ReportsPageProps) {
  const displayList = recentAnalyses.length > 0 ? recentAnalyses : MOCK_ANALYSES;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <PageHeader
        title="Saved Executive Reports"
        subtitle="Exportable analytical decision documents and summary briefs"
        action={
          <Button variant="primary" icon={<Plus className="w-4 h-4" />} onClick={onStartNewAnalysis}>
            Generate New Report
          </Button>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {displayList.map((session) => (
          <Card key={session.id} className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-purple-100 text-[#6D28D9] flex items-center justify-center font-bold">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900 text-sm">Executive Brief: {session.datasetName}</h3>
                <p className="text-xs text-gray-400">Generated {session.createdAt}</p>
              </div>
            </div>

            <p className="text-xs text-gray-600 line-clamp-2 bg-gray-50 p-3 rounded-lg border border-gray-100">
              {session.conclusion || 'Empirical data science investigation report detailing statistical metrics and hypotheses.'}
            </p>

            <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                icon={<ArrowRight className="w-3.5 h-3.5" />}
                onClick={() => onSelectReport(session)}
              >
                View Document
              </Button>
              <Button
                variant="secondary"
                size="sm"
                icon={<Download className="w-3.5 h-3.5" />}
                onClick={() => onSelectReport(session)}
              >
                Export
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default ReportsPage;
