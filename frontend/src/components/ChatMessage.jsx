import React from 'react';
import { User, Sparkles, Clock, Layers, BookOpen } from 'lucide-react';
import SourceCard from './SourceCard';

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';

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
          <div className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
            {message.content}
          </div>

          {/* Sources Section */}
          {hasSources && (
            <div className="pt-3 border-t border-slate-100">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 mb-2.5">
                <BookOpen className="w-3.5 h-3.5 text-brand-600" />
                <span>Verified Source Citations ({message.sources.length})</span>
              </div>
              <div className="grid gap-2 sm:grid-cols-1">
                {message.sources.map((source, idx) => (
                  <SourceCard key={source.chunk_id || idx} source={source} index={idx} />
                ))}
              </div>
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
              {message.retrievedChunks !== undefined && (
                <span className="flex items-center gap-1 font-mono">
                  <Layers className="w-3 h-3 text-slate-400" />
                  {message.retrievedChunks} chunks retrieved
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
