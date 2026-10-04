/**
 * DocuRAG Centralized API Configuration
 * Supports dynamic environment injection across local development and production cloud hosting.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const API_CONFIG = {
  baseURL: API_BASE_URL,
  timeoutMs: 60000,
  endpoints: {
    health: '/health',
    auth: {
      login: '/auth/login',
      register: '/auth/register',
      me: '/auth/me',
    },
    documents: {
      base: '/documents',
      upload: '/documents/upload',
    },
    chat: {
      query: '/chat',
      sessions: '/chat/sessions',
    },
    evaluation: {
      summary: '/evaluation/summary',
      run: '/evaluation/run-benchmark',
      compare: '/evaluation/compare',
    },
  },
};
