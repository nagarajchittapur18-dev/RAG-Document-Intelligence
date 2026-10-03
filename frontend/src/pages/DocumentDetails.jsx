import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  FileText,
  MessageSquare,
  Trash2,
  ArrowLeft,
  Calendar,
  Layers,
  HardDrive,
  FileCheck,
  CheckCircle2,
} from 'lucide-react';
import api from '../services/api';
import { formatBytes, formatDate } from '../utils/helpers';
import { useApp } from '../context/AppContext';
import LoadingIndicator from '../components/LoadingIndicator';
import ErrorMessage from '../components/ErrorMessage';

export default function DocumentDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { setSelectedDocIds, showNotification, fetchDocuments } = useApp();

  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadDoc() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getDocument(id);
        setDocument(data);
      } catch (err) {
        setError(err.message || 'Failed to load document details.');
      } finally {
        setLoading(false);
      }
    }
    loadDoc();
  }, [id]);

  const handleStartChat = () => {
    if (document) {
      setSelectedDocIds([document.id]);
      navigate('/chat');
    }
  };

  const handleDelete = async () => {
    if (!document) return;
    if (!window.confirm(`Permanently delete "${document.filename}" and its vector embeddings?`))
      return;

    try {
      await api.deleteDocument(document.id);
      showNotification(`Deleted "${document.filename}".`, 'success');
      fetchDocuments();
      navigate('/documents');
    } catch (err) {
      showNotification(err.message, 'error');
    }
  };

  if (loading) {
    return <LoadingIndicator text="Loading document details..." />;
  }

  if (error || !document) {
    return (
      <div className="max-w-2xl mx-auto space-y-4">
        <Link
          to="/documents"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Documents
        </Link>
        <ErrorMessage message={error || 'Document not found.'} />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <Link
          to="/documents"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Documents
        </Link>
      </div>

      {/* Main Details Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-6 border-b border-slate-100">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center flex-shrink-0 border border-brand-100 shadow-sm">
              <FileText className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-slate-900">{document.filename}</h1>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Processed
                </span>
              </div>
              <p className="text-xs font-mono text-slate-400 mt-1">ID: {document.id}</p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={handleStartChat}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-sm transition-colors"
            >
              <MessageSquare className="w-4 h-4" />
              Ask Questions
            </button>
            <button
              onClick={handleDelete}
              className="p-2.5 rounded-xl text-slate-400 hover:text-red-600 hover:bg-red-50 border border-slate-200 transition-colors"
              title="Delete Document"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 text-xs font-medium">
              <FileCheck className="w-4 h-4 text-brand-600" />
              <span>Page Count</span>
            </div>
            <p className="text-xl font-bold text-slate-900 mt-1">{document.pages}</p>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 text-xs font-medium">
              <Layers className="w-4 h-4 text-indigo-600" />
              <span>Chroma Chunks</span>
            </div>
            <p className="text-xl font-bold text-slate-900 mt-1">{document.chunks}</p>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 text-xs font-medium">
              <HardDrive className="w-4 h-4 text-teal-600" />
              <span>File Size</span>
            </div>
            <p className="text-xl font-bold text-slate-900 mt-1">
              {formatBytes(document.file_size)}
            </p>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 text-xs font-medium">
              <Calendar className="w-4 h-4 text-slate-500" />
              <span>Upload Date</span>
            </div>
            <p className="text-xs font-semibold text-slate-800 mt-2 truncate">
              {formatDate(document.created_at)}
            </p>
          </div>
        </div>

        {/* System & Storage details */}
        <div className="space-y-3 pt-2 text-xs">
          <h3 className="font-semibold text-slate-900">Storage Information</h3>
          <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 font-mono text-[11px] text-slate-600 break-all">
            {document.file_path}
          </div>
        </div>
      </div>
    </div>
  );
}
