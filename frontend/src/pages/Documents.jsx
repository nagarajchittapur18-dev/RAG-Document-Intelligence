import React, { useState } from 'react';
import { Search, UploadCloud, Plus, Files, X } from 'lucide-react';
import { useApp } from '../context/AppContext';
import DocumentCard from '../components/DocumentCard';
import DocumentUploader from '../components/DocumentUploader';
import EmptyState from '../components/EmptyState';
import api from '../services/api';

export default function Documents() {
  const { documents, fetchDocuments, showNotification } = useApp();
  const [searchTerm, setSearchTerm] = useState('');
  const [showUploader, setShowUploader] = useState(false);

  const filteredDocs = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to permanently delete "${filename}"?`)) return;
    try {
      await api.deleteDocument(docId);
      showNotification(`Deleted "${filename}" and purged its vector embeddings.`, 'success');
      fetchDocuments();
    } catch (err) {
      showNotification(err.message, 'error');
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Document Management</h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage your indexed research papers and PDF knowledge bases.
          </p>
        </div>

        <button
          onClick={() => setShowUploader(!showUploader)}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-sm transition-colors"
        >
          {showUploader ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showUploader ? 'Close Uploader' : 'Upload PDF'}
        </button>
      </div>

      {/* Collapsible Uploader */}
      {showUploader && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <DocumentUploader
            onUploadSuccess={(newDoc) => {
              showNotification(`Uploaded "${newDoc.filename}" successfully.`, 'success');
              fetchDocuments();
              setShowUploader(false);
            }}
          />
        </div>
      )}

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search documents by filename..."
          className="w-full pl-10 pr-4 py-2 text-sm bg-white border border-slate-300 rounded-xl placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 shadow-sm"
        />
        {searchTerm && (
          <button
            onClick={() => setSearchTerm('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-slate-600"
          >
            Clear
          </button>
        )}
      </div>

      {/* Document Grid */}
      {filteredDocs.length === 0 ? (
        <EmptyState
          icon={Files}
          title={searchTerm ? 'No matching documents' : 'No documents indexed yet'}
          description={
            searchTerm
              ? `No documents matching "${searchTerm}". Try a different keyword.`
              : 'Upload your first PDF document to build the semantic vector index.'
          }
          actionLabel={searchTerm ? null : 'Upload Document'}
          onAction={() => setShowUploader(true)}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredDocs.map((doc) => (
            <DocumentCard key={doc.id} document={doc} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}
