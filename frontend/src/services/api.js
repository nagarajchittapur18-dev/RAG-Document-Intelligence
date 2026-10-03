import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60s timeout for LLM generation
});

// Response error interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
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

  /**
   * Retrieve list of all uploaded documents
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

  /**
   * Submit natural language question for grounded RAG generation
   */
  async askQuestion(question, documentIds = null, topK = null) {
    const payload = {
      question: question.trim(),
    };
    if (documentIds && documentIds.length > 0) {
      payload.document_ids = documentIds;
    }
    if (topK) {
      payload.top_k = topK;
    }

    const res = await apiClient.post('/chat/ask', payload);
    return res.data;
  },
};

export default api;
