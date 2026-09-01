import { fetchApi } from './api';
import { AnalysisSession } from '../types';

export async function uploadDataset(file: File): Promise<{
  analysis_id: string;
  dataset_id: string;
  filename: string;
  rows: number;
  columns: number;
  status: string;
}> {
  const formData = new FormData();
  formData.append('file', file);
  return fetchApi('/api/v1/analysis/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function startInvestigation(analysisId: string, userQuestion: string): Promise<{
  analysis_id: string;
  status: string;
  stage: string;
  progress: number;
  message: string;
}> {
  return fetchApi(`/api/v1/analysis/${analysisId}/start`, {
    method: 'POST',
    body: JSON.stringify({ user_question: userQuestion }),
  });
}

export async function getInvestigationStatus(analysisId: string): Promise<{
  analysis_id: string;
  status: string;
  stage?: string;
  job_stage?: string;
  progress?: number;
  job_progress?: number;
  message?: string;
}> {
  return fetchApi(`/api/v1/analysis/${analysisId}/status`);
}

export async function getAnalysisResults(analysisId: string): Promise<any> {
  return fetchApi(`/api/v1/analysis/${analysisId}/results`);
}

export async function getAnalysisHistory(): Promise<AnalysisSession[]> {
  try {
    const rawData = await fetchApi<any[]>('/api/v1/analysis/history');
    return rawData.map(item => ({
      id: item.id || item.analysis_id,
      analysis_id: item.analysis_id || item.id,
      dataset_id: item.dataset_id || item.id,
      datasetName: item.datasetName || item.filename || 'Dataset',
      filename: item.filename || item.datasetName || 'Dataset.csv',
      question: item.question || 'Data Analysis Investigation',
      status: item.status || 'COMPLETED',
      job_stage: item.job_stage || item.stage || 'DONE',
      job_progress: item.job_progress ?? item.progress ?? 100,
      conclusion: item.conclusion || '',
      confidence: item.confidence || 'HIGH',
      createdAt: item.createdAt || item.created_at || 'Recent',
      created_at: item.created_at || item.createdAt || 'Recent'
    }));
  } catch {
    return [];
  }
}

export async function retryInvestigation(analysisId: string): Promise<any> {
  return fetchApi(`/api/v1/analysis/${analysisId}/retry`, { method: 'POST' });
}

export async function cancelInvestigation(analysisId: string): Promise<any> {
  return fetchApi(`/api/v1/analysis/${analysisId}/cancel`, { method: 'POST' });
}

export async function deleteAnalysis(analysisId: string): Promise<any> {
  return fetchApi(`/api/v1/analysis/${analysisId}`, { method: 'DELETE' });
}
