import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Bookmark } from 'lucide-react';

export default function SourceCard({ source, index }) {
  const [expanded, setExpanded] = useState(false);

  const scorePercent =
    source.similarity_score !== undefined && source.similarity_score !== null
      ? `${Math.round(source.similarity_score * 100)}% match`
      : null;

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-700 hover:border-brand-300 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 overflow-hidden">
          <FileText className="w-4 h-4 text-brand-600 flex-shrink-0" />
          <span className="font-semibold text-slate-800 truncate" title={source.document_name}>
            {source.document_name}
          </span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-medium bg-brand-100 text-brand-800 border border-brand-200 flex-shrink-0">
            <Bookmark className="w-2.5 h-2.5 mr-0.5" />
            Page {source.page_number}
          </span>
        </div>

        {scorePercent && (
          <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 flex-shrink-0">
            {scorePercent}
          </span>
        )}
      </div>

      {source.snippet && (
        <div className="mt-2 text-slate-600 font-sans">
          <p className="italic bg-white p-2 rounded border border-slate-100 leading-relaxed">
            "{expanded ? source.snippet : `${source.snippet.slice(0, 140)}...`}"
          </p>

          {source.snippet.length > 140 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="mt-1 inline-flex items-center gap-1 text-[11px] font-medium text-brand-600 hover:text-brand-700"
            >
              {expanded ? (
                <>
                  <ChevronUp className="w-3 h-3" /> Show less
                </>
              ) : (
                <>
                  <ChevronDown className="w-3 h-3" /> Expand excerpt
                </>
              )}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
