import React from 'react';
import { Plus, FileSpreadsheet, ArrowRight, Database } from 'lucide-react';
import { AnalysisSession } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { MOCK_ANALYSES } from '../utils/testData';
import { DatasetGridCanvas } from '../components/canvas/DatasetGridCanvas';

export interface DatasetsPageProps {
  recentAnalyses: AnalysisSession[];
  onStartNewAnalysis: () => void;
  onSelectDatasetForAnalysis: (dataset: any) => void;
}

export function DatasetsPage({ recentAnalyses, onStartNewAnalysis }: DatasetsPageProps) {
  const displayList = recentAnalyses.length > 0 ? recentAnalyses : MOCK_ANALYSES;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header Banner with Three.js Dataset Grid Canvas */}
      <div className="bg-[#111115] rounded-2xl p-6 text-white shadow-xl relative overflow-hidden flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border border-gray-800">
        {/* Three.js Grid Canvas Layer */}
        <DatasetGridCanvas />

        <div className="relative z-10 pointer-events-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-purple-300 text-xs font-semibold backdrop-blur-md mb-2 border border-white/10">
            <Database className="w-3.5 h-3.5" />
            <span>Structured Data Network</span>
          </div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">Datasets Library</h1>
          <p className="text-xs text-gray-400 mt-1">Manage and launch statistical investigations on structured CSV datasets.</p>
        </div>

        <div className="relative z-10 shrink-0 pointer-events-auto">
          <Button
            variant="primary"
            icon={<Plus className="w-4 h-4" />}
            onClick={onStartNewAnalysis}
            className="bg-[#4F46E5] hover:bg-[#4338CA] text-white font-bold cursor-pointer"
          >
            Upload New CSV
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {displayList.map((item) => (
          <Card key={item.id} hoverable className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-purple-100 text-[#4F46E5] flex items-center justify-center font-bold">
                <FileSpreadsheet className="w-5 h-5" />
              </div>
              <div className="overflow-hidden">
                <h3 className="font-bold text-gray-900 text-sm truncate">{item.datasetName}</h3>
                <p className="text-xs text-gray-400">Uploaded {item.createdAt}</p>
              </div>
            </div>

            <div className="bg-gray-50 p-3 rounded-lg flex items-center justify-between text-xs text-gray-600">
              <span>Rows: {item.rows || 1540}</span>
              <span>Cols: {item.columns || 12}</span>
              <span className="font-semibold text-emerald-600">Active</span>
            </div>

            <Button
              variant="outline"
              size="sm"
              className="w-full cursor-pointer"
              icon={<ArrowRight className="w-3.5 h-3.5" />}
              onClick={onStartNewAnalysis}
            >
              Analyze Dataset
            </Button>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default DatasetsPage;
