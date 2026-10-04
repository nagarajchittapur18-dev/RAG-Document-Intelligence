import React, { useState, useEffect } from 'react';
import {
  X,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ArrowRight,
  Clock,
  Layers,
  FileText,
  FileCheck,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react';
import api from '../../services/api';

export default function QuestionDetailDrawer({ queryItem, onClose }) {
  const [questionDetail, setQuestionDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!queryItem?.id) return;
    let isMounted = true;

    async function fetchMetadata() {
      try {
        setLoading(true);
        const data = await api.getEvaluationQuestion(queryItem.id);
        if (isMounted) setQuestionDetail(data);
      } catch (err) {
        console.warn('Could not load detailed question metadata:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    fetchMetadata();
    return () => {
      isMounted = false;
    };
  }, [queryItem?.id]);

  if (!queryItem) return null;

  const isAbstention = queryItem.error_classification === 'unanswerable_abstention_success';
  const rankDelta =
    queryItem.vector_rank && queryItem.reranked_rank
      ? queryItem.vector_rank - queryItem.reranked_rank
      : 0;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs transition-opacity animate-fade-in">
      <div
        className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col overflow-hidden animate-slide-left border-l border-slate-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div className="p-5 border-b border-slate-100 flex items-start justify-between gap-4 bg-slate-50/80">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-brand-100 text-brand-800 border border-brand-200">
                {queryItem.id}
              </span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 capitalize">
                {queryItem.question_type?.replace('_', ' ')}
              </span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 capitalize">
                {queryItem.difficulty}
              </span>
            </div>
            <h2 className="text-sm font-bold text-slate-900 leading-snug">
              {queryItem.question}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Status & Latency Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-xs">
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Status</span>
              <span className="font-bold text-emerald-700 flex items-center gap-1 mt-0.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                {isAbstention ? 'Abstained Correctly' : 'Ground Truth Found'}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Vector Rank</span>
              <span className="font-mono font-bold text-slate-800 mt-0.5 block">
                {queryItem.vector_rank ? `#${queryItem.vector_rank}` : 'None'} (MRR: {queryItem.vector_mrr?.toFixed(2)})
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Reranked Rank</span>
              <span className="font-mono font-bold text-slate-800 mt-0.5 block">
                {queryItem.reranked_rank ? `#${queryItem.reranked_rank}` : 'None'} (MRR: {queryItem.reranked_mrr?.toFixed(2)})
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Total Latency</span>
              <span className="font-mono font-bold text-indigo-700 mt-0.5 flex items-center gap-1">
                <Clock className="w-3 h-3 text-indigo-500" />
                {queryItem.total_latency_ms?.toFixed(1)} ms
              </span>
            </div>
          </div>

          {/* Reference Ground Truth */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-700">
              <FileCheck className="w-4 h-4 text-emerald-600" />
              <span>Ground Truth Reference Answer & Target Metadata</span>
            </div>
            <div className="bg-emerald-50/40 border border-emerald-100 rounded-xl p-4 space-y-3 text-xs">
              <div>
                <span className="text-emerald-900 font-semibold block text-[11px] mb-1">
                  Expected Reference Answer:
                </span>
                <p className="text-slate-800 leading-relaxed italic bg-white/70 p-3 rounded-lg border border-emerald-100/60 font-sans">
                  "{questionDetail?.reference_answer || queryItem.reference_answer || (isAbstention ? 'Question is out-of-domain and unanswerable from the ingested academic corpus.' : 'Referenced in corpus chunk.')}"
                </p>
              </div>

              {!isAbstention && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] font-mono pt-1 text-slate-600">
                  <div className="bg-white p-2 rounded border border-emerald-100/60">
                    <span className="text-slate-400 block text-[10px] font-sans">Target Document:</span>
                    <span className="font-semibold text-slate-800 truncate block" title={questionDetail?.target_document || queryItem.target_document}>
                      {questionDetail?.target_document || queryItem.target_document || 'N/A'}
                    </span>
                  </div>
                  <div className="bg-white p-2 rounded border border-emerald-100/60">
                    <span className="text-slate-400 block text-[10px] font-sans">Target Page:</span>
                    <span className="font-semibold text-slate-800">
                      Page {questionDetail?.target_page || queryItem.target_page || 'N/A'}
                    </span>
                  </div>
                  <div className="bg-white p-2 rounded border border-emerald-100/60">
                    <span className="text-slate-400 block text-[10px] font-sans">Expected Chunk ID:</span>
                    <span className="font-semibold text-slate-800 truncate block" title={questionDetail?.expected_chunk_ids?.[0] || queryItem.expected_chunk_ids?.[0]}>
                      {questionDetail?.expected_chunk_ids?.[0] || queryItem.expected_chunk_ids?.[0] || 'N/A'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Retrieval Comparison (Vector Candidates vs Reranked Candidates) */}
          {!isAbstention && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-700">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-brand-600" />
                  <span>Two-Stage Retrieval Comparison</span>
                </div>
                {rankDelta !== 0 && (
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold ${
                      rankDelta > 0
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {rankDelta > 0 ? (
                      <>
                        <TrendingUp className="w-3 h-3 text-emerald-600" /> Reranker promoted target by +{rankDelta} positions
                      </>
                    ) : (
                      <>
                        <TrendingDown className="w-3 h-3 text-amber-600" /> Reranker shifted target by {rankDelta} positions
                      </>
                    )}
                  </span>
                )}
              </div>

              {/* Reranked Candidate List */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-slate-600 flex items-center justify-between">
                  <span>Stage 2: Cross-Encoder Top Candidates</span>
                  <span className="text-[11px] text-slate-400">Rerank Latency: {queryItem.rerank_latency_ms?.toFixed(1)} ms</span>
                </span>
                <div className="space-y-2">
                  {(queryItem.reranked_chunks || []).slice(0, 5).map((chunk, idx) => {
                    const isTarget = (queryItem.expected_chunk_ids || []).includes(chunk.chunk_id) ||
                                     (chunk.chunk_id === queryItem.target_chunk_id);
                    return (
                      <div
                        key={idx}
                        className={`p-3 rounded-lg border text-xs transition-all ${
                          isTarget
                            ? 'bg-emerald-50/70 border-emerald-300 ring-1 ring-emerald-200'
                            : 'bg-white border-slate-200'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-slate-900 text-white font-mono text-[10px] font-bold flex items-center justify-center">
                              #{idx + 1}
                            </span>
                            <span className="font-mono text-slate-700 font-semibold truncate max-w-[200px]" title={chunk.chunk_id}>
                              {chunk.chunk_id}
                            </span>
                            {isTarget && (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                                Target Ground Truth
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-3 font-mono text-[11px] text-slate-500">
                            {chunk.score !== undefined && (
                              <span>Score: {Number(chunk.score).toFixed(4)}</span>
                            )}
                            <span>Page {chunk.page_number || 'N/A'}</span>
                          </div>
                        </div>
                        {chunk.content && (
                          <p className="text-slate-600 text-[11px] leading-relaxed line-clamp-2 italic">
                            "{chunk.content}"
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Vector Baseline Candidate List */}
              <div className="space-y-2 pt-2">
                <span className="text-xs font-semibold text-slate-600 flex items-center justify-between">
                  <span>Stage 1: Vector-Only Top Candidates</span>
                  <span className="text-[11px] text-slate-400">Search Latency: {queryItem.vector_latency_ms?.toFixed(1)} ms</span>
                </span>
                <div className="space-y-2">
                  {(queryItem.vector_chunks || []).slice(0, 3).map((chunk, idx) => {
                    const isTarget = (queryItem.expected_chunk_ids || []).includes(chunk.chunk_id) ||
                                     (chunk.chunk_id === queryItem.target_chunk_id);
                    return (
                      <div
                        key={idx}
                        className={`p-2.5 rounded-lg border text-xs opacity-90 ${
                          isTarget
                            ? 'bg-blue-50/60 border-blue-300'
                            : 'bg-slate-50 border-slate-200'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="w-4 h-4 rounded-full bg-slate-400 text-white font-mono text-[9px] font-bold flex items-center justify-center">
                              #{idx + 1}
                            </span>
                            <span className="font-mono text-slate-700 text-[11px] truncate max-w-[200px]">
                              {chunk.chunk_id}
                            </span>
                            {isTarget && (
                              <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-blue-100 text-blue-800">
                                Target
                              </span>
                            )}
                          </div>
                          <span className="font-mono text-[10px] text-slate-500">
                            Sim: {Number(chunk.score || chunk.similarity_score || 0).toFixed(4)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/60 flex items-center justify-between text-xs text-slate-500">
          <span className="font-mono text-[11px]">DocuRAG Ground Truth Benchmark</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-200 text-slate-700 font-semibold hover:bg-slate-300 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
