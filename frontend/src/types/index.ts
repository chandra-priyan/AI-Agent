export type PageId =
  | 'dashboard'
  | 'new_analysis'
  | 'investigation'
  | 'results'
  | 'ai_chat'
  | 'report'
  | 'datasets'
  | 'analyses'
  | 'reports'
  | 'login';

export type JobStatus = 'CREATED' | 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface User {
  id: string;
  email: string;
  createdAt?: string;
}

export interface AuthResponse {
  token: string;
  token_type?: string;
  user: User;
}

export interface HypothesisItem {
  id?: string;
  title: string;
  description: string;
  status: 'validated' | 'refuted' | 'inconclusive' | 'pending';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  evidence?: string[];
}

export interface FindingItem {
  id?: string;
  category: string;
  title: string;
  summary: string;
  details?: string;
  chart_type?: string;
  chart_data?: any;
  confidence?: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface AnalysisSession {
  id: string;
  analysis_id?: string;
  dataset_id?: string;
  datasetName: string;
  filename?: string;
  question: string;
  status: JobStatus;
  job_stage?: string;
  stage?: string;
  job_progress?: number;
  progress?: number;
  conclusion?: string;
  confidence?: 'HIGH' | 'MEDIUM' | 'LOW';
  createdAt: string;
  created_at?: string;
  rows?: number;
  columns?: number;
  column_names?: string[];
  results?: {
    summary?: string;
    conclusion?: string;
    key_findings?: FindingItem[];
    hypotheses?: HypothesisItem[];
    charts?: any[];
    recommendations?: string[];
    metrics?: Record<string, any>;
  };
  findings?: FindingItem[];
  hypotheses?: HypothesisItem[];
  evidence?: any;
}

export interface ChatMessage {
  id: string;
  analysisId?: string;
  sender: 'user' | 'ai' | 'system';
  text: string;
  confidence?: 'HIGH' | 'MEDIUM' | 'LOW';
  timestamp: string;
}

export interface DatasetProfile {
  dataset_id: string;
  filename: string;
  rows: number;
  columns: number;
  column_names: string[];
  summary?: Record<string, any>;
  sample?: Record<string, any>[];
}
