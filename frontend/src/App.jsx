import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppProvider, useApp } from './context/AppContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import DocumentDetails from './pages/DocumentDetails';
import Chat from './pages/Chat';
import Evaluation from './pages/Evaluation';
import Login from './pages/Login';
import Register from './pages/Register';
import { CheckCircle2, AlertCircle, Info } from 'lucide-react';

function NotificationBanner() {
  const { notification } = useApp();
  if (!notification) return null;

  const isSuccess = notification.type === 'success';
  const isError = notification.type === 'error';

  return (
    <div
      className={`fixed bottom-5 right-5 z-50 flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-lg border text-xs font-medium transition-all transform animate-fade-in ${
        isSuccess
          ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
          : isError
          ? 'bg-red-50 text-red-900 border-red-200'
          : 'bg-brand-50 text-brand-900 border-brand-200'
      }`}
    >
      {isSuccess && <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />}
      {isError && <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />}
      {!isSuccess && !isError && <Info className="w-4 h-4 text-brand-600 flex-shrink-0" />}
      <span>{notification.message}</span>
    </div>
  );
}

function PublicOnlyRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  return children;
}

function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Navbar onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/documents/:id" element={<DocumentDetails />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/evaluation" element={<Evaluation />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>

      <NotificationBanner />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Auth Routes */}
          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <Login />
              </PublicOnlyRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicOnlyRoute>
                <Register />
              </PublicOnlyRoute>
            }
          />

          {/* Protected Application Routes */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppProvider>
                  <MainLayout />
                </AppProvider>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
