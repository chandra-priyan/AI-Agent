export interface LLMResponseContract {
  summary: string;
  key_findings: Array<{
    title: string;
    category: string;
    summary: string;
    confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  }>;
  hypotheses: Array<{
    title: string;
    description: string;
    status: 'validated' | 'refuted' | 'inconclusive';
    confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  }>;
  conclusion: string;
}

export function validateLLMResponse(data: any): boolean {
  return typeof data === 'object' && data !== null && typeof data.summary === 'string';
}
