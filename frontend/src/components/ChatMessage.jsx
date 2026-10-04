import React, { useState } from 'react';
import { User, Sparkles, Clock, Layers, BookOpen, ChevronDown, ChevronUp } from 'lucide-react';
import SourceCard from './SourceCard';

function renderContentWithCitations(content, messageId, onCitationClick) {
  if (!content) return null;

  // Split on bracketed citation patterns like [1] or [1, 2]
  const citationRegex = /(\[\d+(?:\s*,\s*\d+)*\])/g;
  const parts = content.split(citationRegex);

  return parts.map((part, index) => {
    const match = part.match(/^\[([\d\s,]+)\]$/);
    if (match) {
      const numbers = match[1].split(',').map((n) => parseInt(n.trim(), 10)).filter(Boolean);
      return (
        <span key={`citation-group-${index}`} className="inline-flex items-center gap-0.5 mx-0.5 align-baseline">
          {numbers.map((num) => (
            <button
              key={`cite-${num}-${index}`}
              type="button"
              onClick={() => onCitationClick(num)}
              className="inline-flex items-center justify-center px-1.5 py-0.5 rounded text-[11px] font-bold text-brand-700 bg-brand-50 hover:bg-brand-100 hover:text-brand-900 border border-brand-200/90 cursor-pointer transition-all duration-150 transform hover:scale-105 active:scale-95 shadow-2xs"
              title={`Jump to Source [${num}] Evidence`}
            >
              [{num}]
            </button>
          ))}
        </span>
      );
    }
    return <span key={`text-${index}`}>{part}</span>;
  });
}

export default function ChatMessage({ message }) {
  const [showEvidence, setShowEvidence] = useState(true);
  const isUser = message.role === 'user';
  const msgKey = message.id || 'msg';

  const handleCitationClick = (citationId) => {
    setShowEvidence(true);
    setTimeout(() => {
      const targetCard = document.getElementById(`citation-card-${msgKey}-${citationId}`);
      if (targetCard) {
        targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        targetCard.classList.add('ring-2', 'ring-brand-500', 'bg-brand-50/40');
        setTimeout(() => {
          targetCard.classList.remove('ring-2', 'ring-brand-500', 'bg-brand-50/40');
        }, 2200);
      }
    }, 60);
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="flex items-start gap-2.5 max-w-[85%] sm:max-w-[75%]">
          <div className="bg-slate-900 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm text-sm leading-relaxed">
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
          <div className="w-8 h-8 rounded-full bg-slate-800 text-slate-200 flex items-center justify-center flex-shrink-0 text-xs font-semibold shadow-sm">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    );
  }

  // AI message
  const hasSources = message.sources && message.sources.length > 0;

  return (
    <div className="flex justify-start mb-6">
      <div className="flex items-start gap-3 max-w-[95%] sm:max-w-[85%]">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-600 text-white flex items-center justify-center flex-shrink-0 shadow-sm mt-0.5">
          <Sparkles className="w-4 h-4" />
        </div>

        <div className="flex-1 bg-white border border-slate-200 rounded-2xl rounded-tl-sm p-4 sm:p-5 shadow-sm space-y-3.5">
          {/* Answer content with clickable inline citations */}
          <div className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
            {renderContentWithCitations(message.content, msgKey, handleCitationClick)}
          </div>

          {/* Sources Section - Grouped by Document */}
          {hasSources && (
            <div className="pt-3 border-t border-slate-100">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-700 mb-2.5">
                <button
                  type="button"
                  onClick={() => setShowEvidence(!showEvidence)}
                  className="flex items-center gap-1.5 hover:text-brand-600 transition-colors"
                >
                  <BookOpen className="w-3.5 h-3.5 text-brand-600" />
                  <span>Verified Source Evidence ({message.sources.length})</span>
                  {showEvidence ? (
                    <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                  )}
                </button>
                <span className="text-[11px] font-normal text-slate-500">
                  {Object.keys(
                    message.sources.reduce((acc, s) => {
                      acc[s.document_name] = true;
                      return acc;
                    }, {})
                  ).length}{' '}
                  Document(s) Cited
                </span>
              </div>

              {/* Document Groups */}
              {showEvidence && (
                <div className="space-y-3 mt-2">
                  {Object.values(
                    message.sources.reduce((acc, source) => {
                      const docName = source.document_name || 'Document';
                      if (!acc[docName]) {
                        acc[docName] = {
                          documentId: source.document_id,
                          documentName: docName,
                          items: [],
                        };
                      }
                      acc[docName].items.push(source);
                      return acc;
                    }, {})
                  ).map((group, gIdx) => (
                    <div
                      key={group.documentName + gIdx}
                      className="bg-slate-50/80 border border-slate-200/80 rounded-xl p-3 space-y-2"
                    >
                      <div className="flex items-center justify-between text-xs font-semibold text-slate-800 border-b border-slate-200/60 pb-1.5">
                        <div className="flex items-center gap-2 truncate">
                          <span className="text-base leading-none">📄</span>
                          <span className="truncate" title={group.documentName}>
                            {group.documentName}
                          </span>
                        </div>
                        <span className="text-[10px] font-medium text-slate-500 bg-slate-200/70 px-2 py-0.5 rounded-full shrink-0">
                          {group.items.length} excerpt{group.items.length > 1 ? 's' : ''}
                        </span>
                      </div>

                      <div className="grid gap-2">
                        {group.items.map((source, idx) => {
                          const citId = source.citation_id !== undefined ? source.citation_id : idx + 1;
                          return (
                            <SourceCard
                              key={source.chunk_id || idx}
                              source={source}
                              index={idx}
                              cardId={`citation-card-${msgKey}-${citId}`}
                            />
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Metadata Footer */}
          <div className="flex items-center justify-between pt-2 text-[11px] text-slate-400 border-t border-slate-50">
            <div className="flex items-center gap-3">
              {message.responseTimeMs && (
                <span className="flex items-center gap-1 font-mono">
                  <Clock className="w-3 h-3 text-slate-400" />
                  {message.responseTimeMs} ms
                </span>
              )}
              {message.documentsSearched !== undefined && (
                <span className="flex items-center gap-1 font-mono">
                  <BookOpen className="w-3 h-3 text-slate-400" />
                  {message.documentsSearched} doc{message.documentsSearched !== 1 ? 's' : ''} searched
                </span>
              )}
              {message.retrievedChunks !== undefined && (
                <span className="flex items-center gap-1 font-mono">
                  <Layers className="w-3 h-3 text-slate-400" />
                  {message.retrievedChunks} chunks
                </span>
              )}
            </div>
            <span className="text-[10px] uppercase font-semibold text-brand-600 bg-brand-50 px-2 py-0.5 rounded border border-brand-100">
              Grounded Response
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
