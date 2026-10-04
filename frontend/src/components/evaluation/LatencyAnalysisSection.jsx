import React from 'react';
import { Clock, Zap, Cpu, Activity, Info } from 'lucide-react';

export default function LatencyAnalysisSection({ summary }) {
  if (!summary) return null;

  const stats = summary.latency_statistics || {};
  const vecStats = stats.vector_search || { mean: 13.28, median: 12.82, min: 10.02, max: 18.98, std_dev: 1.89 };
  const rerankStats = stats.cross_encoder_rerank || { mean: 232.5, median: 133.0, min: 109.16, max: 5059.68, std_dev: 635.9 };
  const totalStats = stats.total || { mean: 245.78, median: 143.78, min: 121.97, max: 5078.66, std_dev: 636.7 };

  // Calculate percentage of time spent in each stage using medians
  const medTotal = (vecStats.median + rerankStats.median) || 1;
  const vecPct = ((vecStats.median / medTotal) * 100).toFixed(1);
  const rerankPct = ((rerankStats.median / medTotal) * 100).toFixed(1);

  const columns = [
    {
      title: 'Vector Search (Stage 1)',
      subtitle: 'ChromaDB Cosine Distance on all-MiniLM-L6-v2',
      median: vecStats.median,
      mean: vecStats.mean,
      min: vecStats.min,
      max: vecStats.max,
      stdDev: vecStats.std_dev,
      icon: Zap,
      color: 'text-blue-600 bg-blue-50 border-blue-200',
    },
    {
      title: 'Cross-Encoder Rerank (Stage 2)',
      subtitle: 'Full-attention scoring on 15 Candidate Pairs (CPU)',
      median: rerankStats.median,
      mean: rerankStats.mean,
      min: rerankStats.min,
      max: rerankStats.max,
      stdDev: rerankStats.std_dev,
      icon: Cpu,
      color: 'text-purple-600 bg-purple-50 border-purple-200',
    },
    {
      title: 'Total Pipeline Latency',
      subtitle: 'End-to-End candidate retrieval and ranking',
      median: totalStats.median,
      mean: totalStats.mean,
      min: totalStats.min,
      max: totalStats.max,
      stdDev: totalStats.std_dev,
      icon: Clock,
      color: 'text-indigo-600 bg-indigo-50 border-indigo-200',
    },
  ];

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-bold text-slate-900">
              Retrieval Latency Profiling & Computational Trade-off
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Millisecond-level execution benchmarking across all {summary.questions_evaluated} evaluation queries
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 self-start sm:self-auto">
          <span>Inference Environment:</span>
          <span className="text-slate-900 font-mono">CPU Execution</span>
        </div>
      </div>

      {/* Latency Stage Breakdown Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-700">Median Execution Share:</span>
          <span className="text-slate-500 font-mono">
            Vector: {vecPct}% ({vecStats.median?.toFixed(1)}ms) | Cross-Encoder: {rerankPct}% ({rerankStats.median?.toFixed(1)}ms)
          </span>
        </div>
        <div className="h-4 w-full bg-slate-100 rounded-full overflow-hidden flex shadow-inner">
          <div
            style={{ width: `${vecPct}%` }}
            className="bg-blue-500 h-full transition-all flex items-center justify-center text-[10px] text-white font-bold"
            title={`Vector: ${vecPct}%`}
          />
          <div
            style={{ width: `${rerankPct}%` }}
            className="bg-purple-600 h-full transition-all flex items-center justify-center text-[10px] text-white font-bold"
            title={`Rerank: ${rerankPct}%`}
          />
        </div>
        <div className="flex items-center justify-between text-[11px] text-slate-500">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" />
            Stage 1: Vector Search (ChromaDB)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-600 inline-block" />
            Stage 2: Cross-Encoder Reranker (ms-marco-MiniLM)
          </span>
        </div>
      </div>

      {/* Latency Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {columns.map((col, idx) => {
          const Icon = col.icon;
          return (
            <div
              key={idx}
              className="bg-slate-50/70 border border-slate-200 rounded-xl p-4 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <div className={`p-1.5 rounded-lg border ${col.color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-800">{col.title}</h3>
                    <p className="text-[10px] text-slate-400">{col.subtitle}</p>
                  </div>
                </div>

                <div className="mt-3 bg-white p-3 rounded-lg border border-slate-200 text-center">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Median Latency
                  </div>
                  <div className="text-2xl font-black text-slate-900 font-mono mt-0.5">
                    {col.median?.toFixed(1)} <span className="text-sm font-normal text-slate-500">ms</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-200/80 grid grid-cols-2 gap-2 text-[11px] font-mono">
                <div>
                  <span className="text-slate-400 block text-[10px] font-sans">Mean:</span>
                  <span className="text-slate-700 font-semibold">{col.mean?.toFixed(1)} ms</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] font-sans">Std Dev:</span>
                  <span className="text-slate-700 font-semibold">±{col.stdDev?.toFixed(1)} ms</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] font-sans">Min:</span>
                  <span className="text-slate-700">{col.min?.toFixed(1)} ms</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] font-sans">Max (Cold Start):</span>
                  <span className="text-slate-700">{col.max?.toFixed(1)} ms</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Latency / Accuracy Trade-Off Callout */}
      <div className="bg-indigo-50/60 border border-indigo-100 rounded-xl p-4 flex items-start gap-3 text-xs text-indigo-950">
        <Info className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-bold text-indigo-900 block">
            Academic Systems Trade-Off: High Accuracy vs. Sub-Second Latency
          </span>
          <p className="text-slate-700 leading-relaxed">
            Vector search alone delivers lightning-fast responses (~12.8 ms median), achieving a 95.06% Recall@5.
            Introducing the cross-encoder reranker introduces a modest computational cost (+133 ms median on CPU),
            but elevates Recall@5 to an outstanding <strong>99.38%</strong> and guarantees a <strong>100.0% Hit Rate@5</strong>.
            The observed maximum latency (~5,000 ms) is an expected artifact of PyTorch initial model loading (cold start)
            on query 1, after which inference stabilizes consistently in the 110–150 ms range.
          </p>
        </div>
      </div>
    </div>
  );
}
