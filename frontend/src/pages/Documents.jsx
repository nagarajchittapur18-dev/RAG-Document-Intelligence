import React, { useState } from 'react';
import { Search, UploadCloud, Plus, Files, X, ArrowUpDown, Filter } from 'lucide-react';
import { useApp } from '../context/AppContext';
import DocumentCard from '../components/DocumentCard';
import DocumentUploader from '../components/DocumentUploader';
import EmptyState from '../components/EmptyState';
import api from '../services/api';

export default function Documents() {
  const { documents, fetchDocuments, showNotification } = useApp();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('newest');
  const [showUploader, setShowUploader] = useState(false);

  // Filter by search keyword and status
  const filteredDocs = documents
    .filter((doc) => {
      const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || doc.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      if (sortBy === 'newest') {
        return new Date(b.created_at || 0) - new Date(a.created_at || 0);
      }
      if (sortBy === 'oldest') {
        return new Date(a.created_at || 0) - new Date(b.created_at || 0);
      }
      if (sortBy === 'name') {
        return a.filename.localeCompare(b.filename);
      }
      if (sortBy === 'pages') {
        return (b.pages || 0) - (a.pages || 0);
      }
      if (sortBy === 'chunks') {
        return (b.chunks || 0) - (a.chunks || 0);
      }
      return 0;
    });

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
            Manage your indexed research papers and multi-document PDF knowledge bases.
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

      {/* Filter and Search Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white border border-slate-200 p-3 rounded-2xl shadow-2xs">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search documents by filename..."
            className="w-full pl-10 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
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

        <div className="flex items-center gap-2.5">
          {/* Status Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-600 bg-slate-50 border border-slate-200 px-2.5 py-1.5 rounded-xl">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent text-xs font-medium focus:outline-none cursor-pointer"
            >
              <option value="all">All Statuses</option>
              <option value="completed">Completed Only</option>
              <option value="processing">Processing Only</option>
            </select>
          </div>

          {/* Sorting */}
          <div className="flex items-center gap-1.5 text-xs text-slate-600 bg-slate-50 border border-slate-200 px-2.5 py-1.5 rounded-xl">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-transparent text-xs font-medium focus:outline-none cursor-pointer"
            >
              <option value="newest">Sort by Newest</option>
              <option value="oldest">Sort by Oldest</option>
              <option value="name">Sort by Name (A-Z)</option>
              <option value="pages">Sort by Most Pages</option>
              <option value="chunks">Sort by Most Chunks</option>
            </select>
          </div>
        </div>
      </div>

      {/* Document Grid */}
      {filteredDocs.length === 0 ? (
        <EmptyState
          icon={Files}
          title={searchTerm || statusFilter !== 'all' ? 'No matching documents' : 'No documents indexed yet'}
          description={
            searchTerm || statusFilter !== 'all'
              ? `No documents matching current filters. Try resetting search or status filter.`
              : 'Upload your first PDF document to build the semantic vector index.'
          }
          actionLabel={searchTerm || statusFilter !== 'all' ? null : 'Upload Document'}
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
