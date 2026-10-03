import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [documents, setDocuments] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]); // Empty = all documents
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [systemHealth, setSystemHealth] = useState(null);
  const [notification, setNotification] = useState(null);

  const showNotification = useCallback((message, type = 'info') => {
    setNotification({ message, type, id: Date.now() });
    setTimeout(() => {
      setNotification((curr) => (curr?.message === message ? null : curr));
    }, 5000);
  }, []);

  const fetchDocuments = useCallback(async () => {
    try {
      setLoadingDocs(true);
      const docs = await api.getDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const health = await api.checkHealth();
      setSystemHealth(health);
    } catch (err) {
      console.warn('System health check failed:', err.message);
      setSystemHealth({ status: 'offline', message: err.message });
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
    checkHealth();
  }, [fetchDocuments, checkHealth]);

  return (
    <AppContext.Provider
      value={{
        documents,
        setDocuments,
        selectedDocIds,
        setSelectedDocIds,
        loadingDocs,
        fetchDocuments,
        systemHealth,
        checkHealth,
        notification,
        showNotification,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
