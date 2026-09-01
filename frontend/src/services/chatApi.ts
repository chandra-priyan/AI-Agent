import { fetchApi } from './api';
import { ChatMessage } from '../types';

export async function sendChatMessage(analysisId: string, message: string): Promise<ChatMessage> {
  const data = await fetchApi<any>(`/api/v1/analysis/${analysisId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ user_message: message }),
  });
  return {
    id: data.id || `msg_${Date.now()}`,
    analysisId,
    sender: 'ai',
    text: data.text || data.reply || 'Analysis query response received.',
    confidence: data.confidence || 'HIGH',
    timestamp: data.timestamp || 'Just now',
  };
}

export async function getChatHistory(analysisId: string): Promise<ChatMessage[]> {
  try {
    const rawHistory = await fetchApi<any[]>(`/api/v1/analysis/${analysisId}/chat/history`);
    return rawHistory.map(item => ({
      id: item.id || `msg_${Date.now()}`,
      analysisId,
      sender: item.role === 'user' ? 'user' : 'ai',
      text: item.text || item.content || '',
      confidence: item.confidence || 'HIGH',
      timestamp: item.timestamp || item.created_at || 'Recent',
    }));
  } catch {
    return [];
  }
}
