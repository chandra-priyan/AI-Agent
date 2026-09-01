import React from 'react';
import { Sparkles, MessageSquare, FileText, CheckCircle2, AlertCircle, BarChart2, Lightbulb, ArrowUpRight } from 'lucide-react';
import { AnalysisSession } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { MOCK_ANALYSES } from '../utils/testData';
import { EvidenceCanvas } from '../components/canvas/EvidenceCanvas';

export interface ResultsPageProps {
  session: AnalysisSession;
  onAskFollowUp: () => void;
  onGenerateReport: () => void;
}

export function ResultsPage({ session, onAskFollowUp, onGenerateReport }: ResultsPageProps) {
  const currentSession = session || MOCK_ANALYSES[0];
  const findings = currentSession.findings || currentSession.results?.key_findings || MOCK_ANALYSES[0].findings || [];
  const hypotheses = currentSession.hypotheses || currentSession.results?.hypotheses || MOCK_ANALYSES[0].hypotheses || [];
  const conclusionText = currentSession.conclusion || currentSession.results?.conclusion || MOCK_ANALYSES[0].conclusion;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Executive Summary Hero Card with Three.js Evidence Accent */}
      <div className="bg-[#111111] text-white rounded-2xl p-8 shadow-xl border border-gray-800 relative overflow-hidden">
        {/* Three.js Evidence Accent Canvas */}
        <EvidenceCanvas />

        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6 pb-6 border-b border-gray-800 relative z-10 pointer-events-auto">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="violet">Analysis Complete</Badge>
              <span className="text-xs text-gray-400 font-medium">Dataset: {currentSession.datasetName}</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight">{currentSession.question}</h1>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <Button
              variant="outline"
              size="md"
              icon={<MessageSquare className="w-4 h-4 text-purple-400" />}
              onClick={onAskFollowUp}
              className="bg-gray-900 border-gray-700 text-white hover:bg-gray-800 cursor-pointer"
            >
              Ask AI Analyst
            </Button>
            <Button
              variant="primary"
              size="md"
              icon={<FileText className="w-4 h-4" />}
              onClick={onGenerateReport}
              className="bg-[#6D28D9] hover:bg-[#5B21B6] cursor-pointer"
            >
              Generate Report
            </Button>
          </div>
        </div>

        <div className="space-y-3 bg-gray-900/60 p-5 rounded-xl border border-gray-800 relative z-10 pointer-events-auto">
          <h3 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            <span>AI Executive Conclusion</span>
          </h3>
          <p className="text-sm text-gray-200 leading-relaxed font-normal">
            {conclusionText}
          </p>
        </div>
      </div>

      {/* Grid: Findings & Hypotheses */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Key Findings Card */}
        <Card className="space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <BarChart2 className="w-5 h-5 text-[#6D28D9]" />
              <span>Verified Key Findings</span>
            </h3>
            <span className="text-xs font-semibold text-gray-400">{findings.length} Discovered</span>
          </div>

          <div className="space-y-3">
            {findings.map((finding, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-gray-50 border border-gray-200 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-purple-700 uppercase tracking-wide">{finding.category}</span>
                  {finding.confidence && (
                    <Badge variant={finding.confidence === 'HIGH' ? 'green' : 'amber'}>
                      {finding.confidence} Confidence
                    </Badge>
                  )}
                </div>
                <h4 className="font-bold text-sm text-gray-900">{finding.title}</h4>
                <p className="text-xs text-gray-600 leading-relaxed">{finding.summary}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Tested Hypotheses Card */}
        <Card className="space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-amber-500" />
              <span>Tested Statistical Hypotheses</span>
            </h3>
            <span className="text-xs font-semibold text-gray-400">{hypotheses.length} Tested</span>
          </div>

          <div className="space-y-3">
            {hypotheses.map((hyp, idx) => {
              const isValidated = hyp.status === 'validated';
              return (
                <div key={idx} className="p-4 rounded-xl bg-gray-50 border border-gray-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {isValidated ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-amber-600" />
                      )}
                      <span className="font-bold text-sm text-gray-900">{hyp.title}</span>
                    </div>
                    <Badge variant={isValidated ? 'green' : 'amber'}>
                      {hyp.status.toUpperCase()}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-600 leading-relaxed">{hyp.description}</p>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* Quick Action Footer */}
      <div className="bg-purple-50 border border-purple-200 rounded-xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h4 className="font-bold text-[#6D28D9]">Want to explore specific segments or ask follow-up questions?</h4>
          <p className="text-xs text-purple-800 mt-1">Our AI data analyst has full memory of this session's dataset statistics.</p>
        </div>
        <Button variant="primary" icon={<ArrowUpRight className="w-4 h-4" />} onClick={onAskFollowUp} className="cursor-pointer">
          Open AI Chat
        </Button>
      </div>
    </div>
  );
}

export default ResultsPage;
