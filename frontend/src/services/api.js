import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60s timeout for LLM generation
});

// Request interceptor: Inject Bearer JWT token if present
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('ragmate_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Extract message and handle 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    if (status === 401) {
      localStorage.removeItem('ragmate_token');
      localStorage.removeItem('ragmate_user');
      const currentPath = window.location.pathname;
      if (currentPath !== '/login' && currentPath !== '/register') {
        window.location.href = '/login';
      }
    }

    let message = 'Unable to connect to DocuRAG backend. Please verify the server is running.';
    if (error.response?.data?.detail) {
      message = error.response.data.detail;
    } else if (error.message) {
      message = error.message;
    }
    return Promise.reject(new Error(message));
  }
);

export const api = {
  /**
   * Health check
   */
  async checkHealth() {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // ==========================================
  // AUTHENTICATION APIS
  // ==========================================

  /**
   * Register a new user account
   */
  async register(name, email, password) {
    const res = await apiClient.post('/auth/register', { name, email, password });
    return res.data;
  },

  /**
   * Log in user and receive JWT access token
   */
  async login(email, password) {
    const res = await apiClient.post('/auth/login', { email, password });
    return res.data;
  },

  /**
   * Fetch current authenticated user profile
   */
  async getMe() {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },

  // ==========================================
  // DOCUMENT MANAGEMENT APIS
  // ==========================================

  /**
   * Retrieve list of all uploaded documents for authenticated user
   */
  async getDocuments() {
    const res = await apiClient.get('/documents');
    return res.data.documents || [];
  },

  /**
   * Retrieve specific document details
   */
  async getDocument(documentId) {
    const res = await apiClient.get(`/documents/${documentId}`);
    return res.data;
  },

  /**
   * Upload and process a PDF document
   */
  async uploadDocument(file, onUploadProgress) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percent);
        }
      },
    });
    return res.data;
  },

  /**
   * Delete a document and its ChromaDB vector entries
   */
  async deleteDocument(documentId) {
    const res = await apiClient.delete(`/documents/${documentId}`);
    return res.data;
  },

  // ==========================================
  // CHAT & SESSIONS APIS
  // ==========================================

  /**
   * Submit natural language question for grounded RAG generation
   */
  async askQuestion(question, documentIds = null, topK = null, sessionId = null) {
    const payload = {
      question: question.trim(),
    };
    if (documentIds && documentIds.length > 0) {
      payload.document_ids = documentIds;
    }
    if (topK) {
      payload.top_k = topK;
    }
    if (sessionId) {
      payload.session_id = sessionId;
    }

    const res = await apiClient.post('/chat/ask', payload);
    return res.data;
  },

  /**
   * Create a new chat session
   */
  async createSession(title = 'New Conversation', documentIds = null) {
    const payload = { title };
    if (documentIds && documentIds.length > 0) {
      payload.document_ids = documentIds;
    }
    const res = await apiClient.post('/chat/sessions', payload);
    return res.data;
  },

  /**
   * List chat sessions for current user
   */
  async getSessions() {
    const res = await apiClient.get('/chat/sessions');
    return res.data.sessions || [];
  },

  /**
   * Get messages and details for a session
   */
  async getSession(sessionId) {
    const res = await apiClient.get(`/chat/sessions/${sessionId}`);
    return res.data;
  },

  /**
   * Rename a chat session
   */
  async renameSession(sessionId, title) {
    const res = await apiClient.patch(`/chat/sessions/${sessionId}`, { title });
    return res.data;
  },

  /**
   * Delete a chat session
   */
  async deleteSession(sessionId) {
    const res = await apiClient.delete(`/chat/sessions/${sessionId}`);
    return res.data;
  },

  /**
   * Submit follow-up question to an active session
   */
  async sendSessionMessage(sessionId, question, topK = null) {
    const payload = { question: question.trim() };
    if (topK) {
      payload.top_k = topK;
    }
    const res = await apiClient.post(`/chat/sessions/${sessionId}/messages`, payload);
    return res.data;
  },
};

export default api;
