import { fetchApi } from './api';
import { AuthResponse, User } from '../types';

export async function loginApi(email: string, password: string): Promise<AuthResponse> {
  const data = await fetchApi<AuthResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (data.token) {
    localStorage.setItem('auth_token', data.token);
  }
  return data;
}

export async function registerApi(email: string, password: string): Promise<AuthResponse> {
  const data = await fetchApi<AuthResponse>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (data.token) {
    localStorage.setItem('auth_token', data.token);
  }
  return data;
}

export async function logoutApi(): Promise<void> {
  try {
    await fetchApi('/api/v1/auth/logout', { method: 'POST' });
  } finally {
    localStorage.removeItem('auth_token');
  }
}

export async function getCurrentUserApi(): Promise<User> {
  return fetchApi<User>('/api/v1/auth/me');
}
