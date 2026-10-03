import React from 'react';
import { Link } from 'react-router-dom';
import {
  Files,
  Layers,
  FileCheck,
  CheckCircle2,
  MessageSquare,
  ArrowRight,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import DocumentUploader from '../components/DocumentUploader';
import DocumentCard from '../components/DocumentCard';
import api from '../services/api';

export default function Dashboard() {
  const { documents, fetchDocuments, showNotification, systemHealth } = useApp();

  const totalPages = documents.reduce((sum, d) => sum + (d.pages || 0), 0);
  const totalChunks = documents.reduce((sum, d) => sum + (d.chunks || 0), 0);

  const stats = [
    {
      label: 'Documents',
      value: documents.length,
      icon: Files,
      color: 'text-brand-600 bg-brand-50 border-brand-100',
    },
    {
      label: 'Pages Indexed',
      value: totalPages,
      icon: FileCheck,
      color: 'text-indigo-600 bg-indigo-50 border-indigo-100',
    },
    {
      label: 'Chroma Chunks',
      value: totalChunks,
      icon: Layers,
      color: 'text-teal-600 bg-teal-50 border-teal-100',
    },
    {
      label: 'RAG Pipeline',
      value: systemHealth?.status === 'ok' ? 'Active' : 'Standby',
      icon: CheckCircle2,
      color: 'text-emerald-600 bg-emerald-50 border-emerald-100',
    },
  ];

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) return;
    try {
      await api.deleteDocument(docId);
      showNotification(`Deleted "${filename}" successfully.`, 'success');
      fetchDocuments();
    } catch (err) {
      showNotification(err.message, 'error');
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Hero Welcome Banner */}
      <div className="relative overflow-hidden bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white rounded-2xl p-6 sm:p-8 shadow-sm">
        <div className="relative z-10 max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-brand-200 backdrop-blur-sm border border-white/10">
            <Sparkles className="w-3.5 h-3.5 text-brand-300" />
            <span>Academic Retrieval-Augmented Generation</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Intelligent Document Question Answering
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Upload PDF research papers, technical manuals, or reports. DocuRAG extracts page-by-page
            text, generates dense semantic embeddings in ChromaDB, and delivers factually grounded
            answers with verified page citations via Google Gemini.
          </p>
          <div className="pt-2 flex flex-wrap items-center gap-3">
            <Link
              to="/chat"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-brand-600 hover:bg-brand-500 text-white shadow-sm transition-colors"
            >
              <MessageSquare className="w-4 h-4" />
              Open AI Chat
            </Link>
            <Link
              to="/documents"
              className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold bg-white/10 hover:bg-white/15 text-white transition-colors border border-white/10"
            >
              Browse All Documents
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, idx) => {
          const Icon = s.icon;
          return (
            <div
              key={idx}
              className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex items-center justify-between"
            >
              <div>
                <p className="text-xs font-medium text-slate-500">{s.label}</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{s.value}</p>
              </div>
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center border ${s.color}`}
              >
                <Icon className="w-6 h-6" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Upload Component */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Upload New Document</h2>
            <p className="text-xs text-slate-500">
              PDFs are automatically chunked, embedded, and added to the ChromaDB index.
            </p>
          </div>
        </div>
        <DocumentUploader
          onUploadSuccess={(newDoc) => {
            showNotification(`Indexed "${newDoc.filename}" (${newDoc.chunks} chunks).`, 'success');
            fetchDocuments();
          }}
        />
      </div>

      {/* Recent Documents */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Recently Indexed Documents</h2>
            <p className="text-xs text-slate-500">
              Knowledge base files ready for semantic retrieval and question answering.
            </p>
          </div>
          {documents.length > 3 && (
            <Link
              to="/documents"
              className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1"
            >
              View all ({documents.length}) <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          )}
        </div>

        {documents.length === 0 ? (
          <div className="p-8 text-center bg-white border border-dashed border-slate-300 rounded-2xl text-slate-500 text-xs">
            No documents uploaded yet. Drag and drop your first PDF above to begin.
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {documents.slice(0, 3).map((doc) => (
              <DocumentCard key={doc.id} document={doc} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
