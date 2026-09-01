import { fetchApi } from './api';

export async function generateReport(analysisId: string): Promise<any> {
  return fetchApi(`/api/v1/report/generate`, {
    method: 'POST',
    body: JSON.stringify({ analysis_id: analysisId }),
  });
}

export async function getReport(analysisId: string): Promise<any> {
  return fetchApi(`/api/v1/report/${analysisId}`);
}
