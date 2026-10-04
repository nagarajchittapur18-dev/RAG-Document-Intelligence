import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Bookmark, ExternalLink, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import api from '../services/api';

export default function SourceCard({ source, index, cardId }) {
  const [expandedSnippet, setExpandedSnippet] = useState(false);
  const [showPageViewer, setShowPageViewer] = useState(false);
  const [pageLoading, setPageLoading] = useState(false);
  const [pageData, setPageData] = useState(null);
  const [pageError, setPageError] = useState(null);

  const citationId = source.citation_id !== undefined ? source.citation_id : index + 1;
  const rawScore = source.relevance_score !== undefined && source.relevance_score !== null
    ? source.relevance_score
    : source.similarity_score;

  const scorePercent = rawScore !== undefined && rawScore !== null
    ? Math.round(rawScore * 100)
    : null;

  const handleTogglePageViewer = async () => {
    if (showPageViewer) {
      setShowPageViewer(false);
      return;
    }

    setShowPageViewer(true);
    if (!pageData && source.document_id && source.page_number) {
      setPageLoading(true);
      setPageError(null);
      try {
        const data = await api.getDocumentPage(source.document_id, source.page_number);
        setPageData(data);
      } catch (err) {
        setPageError(err.message || 'Unable to load page content.');
      } finally {
        setPageLoading(false);
      }
    }
  };

  return (
    <div
      id={cardId || `citation-card-${citationId}`}
      className="bg-white border border-slate-200/90 rounded-xl p-3.5 text-xs text-slate-700 shadow-xs hover:border-brand-300 transition-all duration-200 target:ring-2 target:ring-brand-500 target:border-brand-500"
    >
      {/* Header Row */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 overflow-hidden flex-1">
          {/* Citation ID Pill */}
          <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-md text-[11px] font-bold bg-brand-600 text-white shadow-xs shrink-0">
            [{citationId}]
          </span>

          <div className="flex items-center gap-1.5 min-w-0">
            <FileText className="w-3.5 h-3.5 text-brand-600 shrink-0" />
            <span className="font-semibold text-slate-800 truncate" title={source.document_name}>
              {source.document_name}
            </span>
          </div>

          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-200/60 shrink-0">
            <Bookmark className="w-2.5 h-2.5 mr-0.5" />
            Page {source.page_number}
          </span>
        </div>

        {/* Relevance Score Pill */}
        {scorePercent !== null && (
          <span
            className={`text-[10px] font-mono font-medium px-2 py-0.5 rounded-full shrink-0 border ${
              scorePercent >= 75
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : scorePercent >= 50
                ? 'bg-blue-50 text-blue-700 border-blue-200'
                : 'bg-slate-100 text-slate-600 border-slate-200'
            }`}
          >
            Relevance: {scorePercent}%
          </span>
        )}
      </div>

      {/* Chunk ID subheader */}
      {source.chunk_id && (
        <div className="mt-1 flex items-center gap-2 text-[10px] text-slate-400 font-mono">
          <span>ID: {source.chunk_id}</span>
        </div>
      )}

      {/* Snippet Body */}
      {source.snippet && (
        <div className="mt-2.5 text-slate-600 font-sans">
          <div className="relative bg-slate-50 border border-slate-200/70 rounded-lg p-2.5 text-[11px] leading-relaxed">
            <p className="whitespace-pre-wrap text-slate-700 font-serif">
              "{expandedSnippet || source.snippet.length <= 160 ? source.snippet : `${source.snippet.slice(0, 160)}...`}"
            </p>
          </div>

          <div className="mt-1.5 flex items-center justify-between">
            {source.snippet.length > 160 ? (
              <button
                type="button"
                aria-expanded={expandedSnippet}
                aria-label={expandedSnippet ? `Collapse excerpt for [${citationId}]` : `Expand full excerpt for [${citationId}]`}
                onClick={() => setExpandedSnippet(!expandedSnippet)}
                className="inline-flex items-center gap-1 text-[11px] font-medium text-brand-600 hover:text-brand-700 focus:outline-hidden focus:ring-2 focus:ring-brand-500 rounded transition-colors"
              >
                {expandedSnippet ? (
                  <>
                    <ChevronUp className="w-3 h-3" /> Show excerpt summary
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-3 h-3" /> View full chunk excerpt
                  </>
                )}
              </button>
            ) : <span />}

            {/* View Full Page Text Verification Button */}
            <button
              type="button"
              aria-expanded={showPageViewer}
              aria-label={`Verify page ${source.page_number} text for ${source.document_name}`}
              onClick={handleTogglePageViewer}
              className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded border focus:outline-hidden focus:ring-2 focus:ring-brand-500 transition-colors ${
                showPageViewer
                  ? 'bg-brand-50 text-brand-700 border-brand-200'
                  : 'bg-white text-slate-600 hover:text-brand-600 border-slate-200 hover:border-brand-200'
              }`}
            >
              <ExternalLink className="w-3 h-3" />
              {showPageViewer ? 'Hide Page Text' : 'Verify Page Text'}
            </button>
          </div>
        </div>
      )}

      {/* Page Text Preview Drawer */}
      {showPageViewer && (
        <div className="mt-3 pt-3 border-t border-slate-200/80">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-800">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Full Page {source.page_number} Extracted Text</span>
            </div>
            {pageData && (
              <span className="text-[10px] text-slate-400 font-mono">
                {pageData.total_pages ? `Page ${pageData.page_number} of ${pageData.total_pages}` : ''}
              </span>
            )}
          </div>

          {pageLoading && (
            <div className="py-4 flex items-center justify-center gap-2 text-slate-500 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
              <span>Loading page extraction from document...</span>
            </div>
          )}

          {pageError && (
            <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{pageError}</span>
            </div>
          )}

          {pageData && !pageLoading && (
            <div className="max-h-60 overflow-y-auto bg-slate-50/90 rounded-lg p-3 border border-slate-200 text-[11px] font-sans leading-relaxed text-slate-800 whitespace-pre-wrap font-mono">
              {pageData.text || '(No extractable text on this page)'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
