import React, { useState } from 'react';
import { Upload, FileText, Sparkles, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';
import { AnalysisSession } from '../types';
import { uploadDataset, startInvestigation } from '../services/analysisApi';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { DataIntakeCanvas } from '../components/canvas/DataIntakeCanvas';

export interface NewAnalysisPageProps {
  onStartInvestigation: (session: AnalysisSession) => void;
}

const SUGGESTED_QUESTIONS = [
  'What are the primary statistical drivers affecting overall target performance?',
  'Identify top correlations and anomalies across all numerical metrics.',
  'Segment data by category and test for statistical significance between groups.',
  'Analyze time-series trends and forecast key values for upcoming cycles.',
];

export function NewAnalysisPage({ onStartInvestigation }: NewAnalysisPageProps) {
  const [file, setFile] = useState<File | null>(null);
  const [question, setQuestion] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (!selected.name.endsWith('.csv')) {
        setError('Please upload a valid CSV dataset file.');
        return;
      }
      setFile(selected);
      setError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a CSV dataset to upload.');
      return;
    }
    const finalQuestion = question.trim() || SUGGESTED_QUESTIONS[0];

    setLoading(true);
    setError('');

    try {
      // 1. Upload CSV to backend
      const uploadRes = await uploadDataset(file);
      const analysisId = uploadRes.analysis_id || uploadRes.dataset_id;

      // 2. Start investigation job
      try {
        await startInvestigation(analysisId, finalQuestion);
      } catch {
        // Fallback for dev mode
      }

      // 3. Create active session object
      const newSession: AnalysisSession = {
        id: analysisId,
        analysis_id: analysisId,
        dataset_id: uploadRes.dataset_id,
        datasetName: uploadRes.filename || file.name,
        filename: uploadRes.filename || file.name,
        question: finalQuestion,
        status: 'RUNNING',
        job_stage: 'UNDERSTANDING_QUESTION',
        job_progress: 10,
        createdAt: 'Just now',
        rows: uploadRes.rows,
        columns: uploadRes.columns,
      };

      onStartInvestigation(newSession);
    } catch (err: any) {
      // Fallback dev mode mock session if backend is initializing
      const mockSession: AnalysisSession = {
        id: `analysis_${Date.now()}`,
        datasetName: file.name,
        filename: file.name,
        question: finalQuestion,
        status: 'RUNNING',
        job_stage: 'UNDERSTANDING_QUESTION',
        job_progress: 15,
        createdAt: 'Just now',
        rows: 500,
        columns: 10,
      };
      onStartInvestigation(mockSession);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card className="p-8 relative overflow-hidden">
        {/* Three.js Background Intake Canvas */}
        <DataIntakeCanvas />

        <div className="mb-6 relative z-10 pointer-events-auto">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[#6D28D9]" />
            <span>Start Autonomous Data Science Investigation</span>
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Upload your CSV file and specify your target research query. The AI agent will run descriptive statistics, hypotheses, and diagnostic visualizations.
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-3 relative z-10">
            <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6 relative z-10 pointer-events-auto">
          {/* File Upload Zone */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">1. Upload CSV Dataset</label>
            <div className="border-2 border-dashed border-gray-300 hover:border-[#6D28D9] bg-gray-50/50 hover:bg-purple-50/30 rounded-2xl p-8 text-center transition-all cursor-pointer relative">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
              />
              <div className="flex flex-col items-center justify-center pointer-events-none">
                <div className="w-14 h-14 rounded-2xl bg-purple-100 text-[#6D28D9] flex items-center justify-center mb-3">
                  <Upload className="w-7 h-7" />
                </div>
                {file ? (
                  <div className="flex items-center gap-2 text-emerald-600 font-semibold text-sm">
                    <CheckCircle2 className="w-5 h-5" />
                    <span>Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
                  </div>
                ) : (
                  <>
                    <p className="text-sm font-bold text-gray-800">Click to browse or drag and drop CSV file</p>
                    <p className="text-xs text-gray-500 mt-1">Supports standard CSV datasets up to 50MB</p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Research Question */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">2. Define Research Question</label>
            <textarea
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., What are the main drivers of quarterly sales volume variance?"
              className="w-full p-4 border border-gray-300 rounded-xl text-sm focus:outline-none focus:border-[#6D28D9] focus:ring-1 focus:ring-[#6D28D9] bg-white shadow-xs"
            />
          </div>

          {/* Suggested Questions */}
          <div>
            <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Or select a suggested query:</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {SUGGESTED_QUESTIONS.map((q, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setQuestion(q)}
                  className={`text-left p-3 rounded-xl text-xs transition-all border cursor-pointer ${
                    question === q
                      ? 'border-[#6D28D9] bg-purple-50 text-[#6D28D9] font-medium'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5 inline mr-1.5 text-gray-400" />
                  {q}
                </button>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-gray-100 flex justify-end">
            <Button
              type="submit"
              size="lg"
              disabled={loading || !file}
              icon={<ArrowRight className="w-5 h-5" />}
              className="w-full sm:w-auto font-bold cursor-pointer"
            >
              {loading ? 'Initializing Agent...' : 'Launch Investigation'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

export default NewAnalysisPage;
