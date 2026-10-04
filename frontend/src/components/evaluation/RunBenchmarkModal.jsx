import React, { useState } from 'react';
import { Play, X, Loader2, CheckCircle2, AlertCircle, Settings2 } from 'lucide-react';
import api from '../../services/api';

export default function RunBenchmarkModal({ onClose, onBenchmarkCompleted }) {
  const [candidateK, setCandidateK] = useState(15);
  const [limit, setLimit] = useState(null); // null means all questions
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    setStatusMessage('Initializing evaluation dataset and ChromaDB collection...');

    try {
      setStatusMessage('Executing candidate retrieval and cross-encoder inference...');
      const payload = {
        candidate_k: candidateK,
        k_values: [1, 3, 5, 10],
      };
      if (limit && limit > 0) {
        payload.limit = limit;
      }

      const res = await api.runBenchmark(payload);
      setStatusMessage('Benchmark completed successfully!');
      if (onBenchmarkCompleted) {
        onBenchmarkCompleted(res);
      }
      onClose();
    } catch (err) {
      console.error('Benchmark execution error:', err);
      setError(err.response?.data?.detail || err.message || 'Benchmark execution failed.');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-fade-in">
      <div
        className="w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center gap-2">
            <Play className="w-5 h-5 text-brand-600" />
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Execute Benchmark Evaluation
              </h2>
              <p className="text-xs text-slate-500">
                Run quantitative IR scoring across the verified academic benchmark
              </p>
            </div>
          </div>
          {!running && (
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200/60 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Candidate Pool Size (Candidate K)
              </label>
              <input
                type="number"
                min={5}
                max={50}
                value={candidateK}
                disabled={running}
                onChange={(e) => setCandidateK(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Number of vector similarity candidates fetched from ChromaDB before cross-encoder reranking (Default: 15).
              </p>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Evaluation Sample Limit
              </label>
              <select
                value={limit === null ? 'all' : limit}
                disabled={running}
                onChange={(e) => {
                  const val = e.target.value;
                  setLimit(val === 'all' ? null : Number(val));
                }}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="all">Full Academic Benchmark (All 60 Questions)</option>
                <option value="5">Rapid Test (5 Questions)</option>
                <option value="10">Quick Benchmark (10 Questions)</option>
                <option value="25">Sub-Corpus Benchmark (25 Questions)</option>
              </select>
              <p className="text-[11px] text-slate-400 mt-1">
                Testing a subset takes 1–3 seconds, while all 60 questions take ~15 seconds on CPU.
              </p>
            </div>
          </div>

          {running && (
            <div className="bg-brand-50/70 border border-brand-100 rounded-xl p-4 flex items-center gap-3">
              <Loader2 className="w-5 h-5 text-brand-600 animate-spin shrink-0" />
              <div className="text-xs">
                <span className="font-bold text-brand-900 block">Benchmark in progress...</span>
                <span className="text-brand-700 text-[11px]">{statusMessage}</span>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            disabled={running}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-200 disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleRun}
            disabled={running}
            className="inline-flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-bold bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50 shadow-sm transition-colors"
          >
            {running ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Benchmarking...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Start Benchmark</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
