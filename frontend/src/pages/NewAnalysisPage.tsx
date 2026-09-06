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
      const uploadRes = await uploadDataset(file);
      const analysisId = uploadRes.analysis_id || uploadRes.dataset_id;

      try {
        await startInvestigation(analysisId, finalQuestion);
      } catch (invErr: any) {
        console.warn('Backend investigation auto-trigger warning:', invErr);
      }

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
      setError(err?.message || 'Failed to upload CSV dataset to backend server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header Banner Card with Subtle Three.js Background Canvas */}
      <div className="bg-gradient-to-r from-[#111115] via-[#1E1B4B] to-[#4F46E5] rounded-2xl p-6 text-white shadow-xl relative overflow-hidden flex items-center justify-between border border-gray-800">
        <DataIntakeCanvas />
        <div className="relative z-10 pointer-events-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-purple-200 text-xs font-semibold backdrop-blur-md mb-2 border border-white/10">
            <Sparkles className="w-3.5 h-3.5 text-purple-300" />
            <span>Autonomous Data Intake & Analysis</span>
          </div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">Launch New Data Investigation</h1>
          <p className="text-xs text-gray-300 mt-1 max-w-xl">
            Upload your CSV dataset and specify a target research query. The AI agent will profile the dataset, test hypotheses, and output verified statistical findings.
          </p>
        </div>
      </div>

      {/* Main Intake Form Card */}
      <Card className="p-8">
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-3">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* File Upload Dropzone */}
          <div>
            <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wider">1. Select CSV Dataset File</label>
            <div className="border-2 border-dashed border-gray-300 hover:border-[#4F46E5] bg-gray-50/70 hover:bg-purple-50/20 rounded-2xl p-8 text-center transition-all cursor-pointer relative">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              />
              <div className="flex flex-col items-center justify-center pointer-events-none">
                <div className="w-14 h-14 rounded-2xl bg-purple-100 text-[#4F46E5] flex items-center justify-center mb-3 shadow-xs">
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
            <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wider">2. Define Business / Statistical Query</label>
            <textarea
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., What are the main drivers of quarterly sales volume variance?"
              className="w-full p-4 border border-gray-300 rounded-xl text-sm focus:outline-none focus:border-[#4F46E5] focus:ring-1 focus:ring-[#4F46E5] bg-white shadow-xs"
            />
          </div>

          {/* Suggested Queries */}
          <div>
            <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Or select a suggested analytical query:</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {SUGGESTED_QUESTIONS.map((q, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setQuestion(q)}
                  className={`text-left p-3 rounded-xl text-xs transition-all border cursor-pointer flex items-start gap-2 ${
                    question === q
                      ? 'border-[#4F46E5] bg-purple-50/80 text-[#4F46E5] font-semibold shadow-xs'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5 text-gray-400 shrink-0 mt-0.5" />
                  <span>{q}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-gray-100 flex justify-end">
            <Button
              type="submit"
              size="lg"
              disabled={loading || !file}
              icon={<ArrowRight className="w-4 h-4" />}
              className="w-full sm:w-auto font-bold bg-[#4F46E5] hover:bg-[#4338CA] text-white px-8 py-3 rounded-xl cursor-pointer shadow-md"
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
