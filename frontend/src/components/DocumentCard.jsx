import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FileText, Trash2, MessageSquare, ExternalLink, CheckCircle2, Clock } from 'lucide-react';
import { formatBytes, formatDate } from '../utils/helpers';
import { useApp } from '../context/AppContext';

export default function DocumentCard({ document, onDelete }) {
  const navigate = useNavigate();
  const { setSelectedDocIds } = useApp();

  const handleStartChat = () => {
    setSelectedDocIds([document.id]);
    navigate('/chat');
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md hover:border-slate-300 transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center flex-shrink-0 border border-brand-100">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h4
                className="font-semibold text-slate-900 text-sm hover:text-brand-600 transition-colors line-clamp-1"
                title={document.filename}
              >
                <Link to={`/documents/${document.id}`}>{document.filename}</Link>
              </h4>
              <p className="text-xs text-slate-500 mt-0.5">
                {document.pages} {document.pages === 1 ? 'page' : 'pages'} • {document.chunks} chunks
                {document.file_size > 0 && ` • ${formatBytes(document.file_size)}`}
              </p>
            </div>
          </div>

          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 flex-shrink-0">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            Processed
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-4">
          <Clock className="w-3.5 h-3.5" />
          <span>Uploaded {formatDate(document.created_at)}</span>
        </div>
      </div>

      <div className="flex items-center justify-between gap-2 pt-4 mt-4 border-t border-slate-100">
        <button
          onClick={handleStartChat}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-50 text-brand-700 hover:bg-brand-100 border border-brand-200 transition-colors"
        >
          <MessageSquare className="w-3.5 h-3.5" />
          Ask AI
        </button>

        <div className="flex items-center gap-1">
          <Link
            to={`/documents/${document.id}`}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
            title="View Details"
          >
            <ExternalLink className="w-4 h-4" />
          </Link>
          <button
            onClick={() => onDelete(document.id, document.filename)}
            className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors"
            title="Delete Document"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
