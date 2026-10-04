import React from 'react';
import {
  FileQuestion,
  Target,
  Search,
  Award,
  Zap,
  Cpu,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
} from 'lucide-react';

export default function EvaluationKPICards({ summary }) {
  if (!summary) return null;

  const baseline = summary.baseline_vector || {};
  const reranked = summary.enhanced_reranked || {};
  const latency = summary.latency_statistics?.total || {};
  const baseLatency = summary.latency_statistics?.vector_search || {};
  const improvements = (summary.improvements || []).reduce((acc, curr) => {
    acc[curr.metric] = curr.improvement_percentage;
    return acc;
  }, {});

  const hit5Base = (baseline.metrics_by_k?.['K=5']?.hit_rate ?? 0) * 100;
  const hit5Rerank = (reranked.metrics_by_k?.['K=5']?.hit_rate ?? 0) * 100;
  const hit5Diff = improvements['Hit Rate@5'] ?? (hit5Rerank - hit5Base);

  const recall5Base = (baseline.metrics_by_k?.['K=5']?.recall ?? 0) * 100;
  const recall5Rerank = (reranked.metrics_by_k?.['K=5']?.recall ?? 0) * 100;
  const recall5Diff = improvements['Recall@5'] ?? (recall5Rerank - recall5Base);

  const mrrBase = baseline.mrr ?? 0;
  const mrrRerank = reranked.mrr ?? 0;
  const mrrDiff = improvements['MRR'] ?? (((mrrRerank - mrrBase) / (mrrBase || 1)) * 100);

  const medTotalLatency = latency.median ?? reranked.avg_total_latency_ms ?? 0;
  const medVectorLatency = baseLatency.median ?? baseline.avg_retrieval_latency_ms ?? 0;

  const renderDeltaChip = (val, suffix = '%') => {
    const isPositive = val > 0.001;
    const isNegative = val < -0.001;

    return (
      <span
        className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-xs font-semibold ${
          isPositive
            ? 'bg-emerald-100 text-emerald-800'
            : isNegative
            ? 'bg-amber-100 text-amber-800'
            : 'bg-slate-100 text-slate-700'
        }`}
      >
        {isPositive && <ArrowUpRight className="w-3 h-3 text-emerald-600" />}
        {isNegative && <ArrowDownRight className="w-3 h-3 text-amber-600" />}
        {!isPositive && !isNegative && <Minus className="w-3 h-3 text-slate-500" />}
        <span>
          {val > 0 ? `+${val.toFixed(2)}` : val.toFixed(2)}
          {suffix}
        </span>
      </span>
    );
  };

  const cards = [
    {
      title: 'Questions Evaluated',
      value: summary.questions_evaluated ?? 0,
      subvalue: `${summary.error_summary?.success ?? 0} answerable + ${summary.error_summary?.unanswerable_abstention_success ?? 0} unanswerable`,
      icon: FileQuestion,
      iconColor: 'text-indigo-600 bg-indigo-50 border-indigo-100',
      badge: 'Academic Gold Dataset',
    },
    {
      title: 'Hit Rate @ K=5',
      value: `${hit5Rerank.toFixed(1)}%`,
      subvalue: `Baseline Vector: ${hit5Base.toFixed(1)}%`,
      delta: renderDeltaChip(hit5Diff),
      icon: Target,
      iconColor: 'text-emerald-600 bg-emerald-50 border-emerald-100',
      badge: 'Target Chunk In Top-5',
    },
    {
      title: 'Recall @ K=5',
      value: `${recall5Rerank.toFixed(1)}%`,
      subvalue: `Baseline Vector: ${recall5Base.toFixed(1)}%`,
      delta: renderDeltaChip(recall5Diff),
      icon: Search,
      iconColor: 'text-teal-600 bg-teal-50 border-teal-100',
      badge: 'Ground Truth Coverage',
    },
    {
      title: 'MRR (Mean Recip. Rank)',
      value: mrrRerank.toFixed(4),
      subvalue: `Baseline Vector: ${mrrBase.toFixed(4)}`,
      delta: renderDeltaChip(mrrDiff),
      icon: Award,
      iconColor: 'text-amber-600 bg-amber-50 border-amber-100',
      badge: 'First Relevant Rank',
    },
    {
      title: 'Median Total Latency',
      value: `${medTotalLatency.toFixed(1)} ms`,
      subvalue: `Vector: ${medVectorLatency.toFixed(1)} ms | Rerank: ${(medTotalLatency - medVectorLatency).toFixed(1)} ms`,
      icon: Zap,
      iconColor: 'text-blue-600 bg-blue-50 border-blue-100',
      badge: 'CPU Inference Benchmark',
    },
    {
      title: 'Reranker Status',
      value: 'Cross-Encoder Active',
      subvalue: `Candidate Pool K=${summary.configuration?.candidate_k || 15} → Top-${summary.configuration?.k_values?.[2] || 5}`,
      icon: Cpu,
      iconColor: 'text-purple-600 bg-purple-50 border-purple-100',
      badge: 'MS-MARCO MiniLM',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className={`p-2 rounded-lg border ${card.iconColor}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
                  {card.badge}
                </span>
              </div>
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                {card.title}
              </h3>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
                  {card.value}
                </span>
                {card.delta}
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 text-[11px] text-slate-500">
              {card.subvalue}
            </div>
          </div>
        );
      })}
    </div>
  );
}
