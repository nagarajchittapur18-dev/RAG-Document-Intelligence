import React, { useState, useEffect } from 'react';
import { X, ArrowRightLeft, Award, Target, Search, Clock, CheckCircle2 } from 'lucide-react';
import api from '../../services/api';

export default function ExperimentCompareModal({ experiments = [], defaultExpId, onClose }) {
  const [expAId, setExpAId] = useState(defaultExpId || experiments[0]?.experiment_id || '');
  const [expBId, setExpBId] = useState(experiments[1]?.experiment_id || experiments[0]?.experiment_id || '');
  const [dataA, setDataA] = useState(null);
  const [dataB, setDataB] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!expAId || !expBId) return;
    let isMounted = true;

    async function loadBoth() {
      setLoading(true);
      try {
        const [resA, resB] = await Promise.all([
          api.getExperimentDetail(expAId),
          api.getExperimentDetail(expBId),
        ]);
        if (isMounted) {
          setDataA(resA);
          setDataB(resB);
        }
      } catch (err) {
        console.error('Failed to load experiment comparison:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadBoth();
    return () => {
      isMounted = false;
    };
  }, [expAId, expBId]);

  const renderMetricRow = (label, valA, valB, format = (v) => v, isHigherBetter = true) => {
    const diff = (valB ?? 0) - (valA ?? 0);
    const hasDiff = Math.abs(diff) > 0.0001;
    const isImproved = isHigherBetter ? diff > 0 : diff < 0;

    return (
      <tr className="hover:bg-slate-50 border-b border-slate-100 text-xs">
        <td className="py-2.5 px-4 font-medium text-slate-700">{label}</td>
        <td className="py-2.5 px-4 font-mono font-semibold text-slate-800">
          {valA !== undefined ? format(valA) : '—'}
        </td>
        <td className="py-2.5 px-4 font-mono font-semibold text-slate-800">
          {valB !== undefined ? format(valB) : '—'}
        </td>
        <td className="py-2.5 px-4 font-mono text-right">
          {hasDiff ? (
            <span
              className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold ${
                isImproved
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'bg-amber-100 text-amber-800'
              }`}
            >
              {diff > 0 ? `+${format(diff)}` : format(diff)}
            </span>
          ) : (
            <span className="text-slate-400 font-normal">Identical</span>
          )}
        </td>
      </tr>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-fade-in">
      <div
        className="w-full max-w-4xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center gap-2">
            <ArrowRightLeft className="w-5 h-5 text-indigo-600" />
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Comparative Experiment Diff & Longitudinal Analysis
              </h2>
              <p className="text-xs text-slate-500">
                Direct side-by-side evaluation between two recorded benchmark runs
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Experiment Selectors */}
        <div className="p-5 border-b border-slate-100 grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-50/30">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
              Baseline Experiment (A)
            </label>
            <select
              value={expAId}
              onChange={(e) => setExpAId(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
            >
              {experiments.map((e) => (
                <option key={e.experiment_id} value={e.experiment_id}>
                  {e.experiment_id} ({e.questions_evaluated} queries — {new Date(e.timestamp).toLocaleDateString()})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
              Comparison Experiment (B)
            </label>
            <select
              value={expBId}
              onChange={(e) => setExpBId(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
            >
              {experiments.map((e) => (
                <option key={e.experiment_id} value={e.experiment_id}>
                  {e.experiment_id} ({e.questions_evaluated} queries — {new Date(e.timestamp).toLocaleDateString()})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {loading ? (
            <div className="py-12 text-center text-xs text-slate-500">
              Loading experiment metrics for comparison...
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 text-slate-600 uppercase font-semibold text-[11px] border-b border-slate-200">
                    <th className="py-2.5 px-4">Evaluation Metric</th>
                    <th className="py-2.5 px-4">Experiment A</th>
                    <th className="py-2.5 px-4">Experiment B</th>
                    <th className="py-2.5 px-4 text-right">Differential (B − A)</th>
                  </tr>
                </thead>
                <tbody>
                  {renderMetricRow('Questions Evaluated', dataA?.questions_evaluated, dataB?.questions_evaluated, (v) => `${v}`)}
                  {renderMetricRow(
                    'Reranked Hit Rate @ 5',
                    (dataA?.enhanced_reranked?.metrics_by_k?.['K=5']?.hit_rate ?? 0) * 100,
                    (dataB?.enhanced_reranked?.metrics_by_k?.['K=5']?.hit_rate ?? 0) * 100,
                    (v) => `${v.toFixed(2)}%`
                  )}
                  {renderMetricRow(
                    'Reranked Recall @ 5',
                    (dataA?.enhanced_reranked?.metrics_by_k?.['K=5']?.recall ?? 0) * 100,
                    (dataB?.enhanced_reranked?.metrics_by_k?.['K=5']?.recall ?? 0) * 100,
                    (v) => `${v.toFixed(2)}%`
                  )}
                  {renderMetricRow(
                    'Reranked Precision @ 5',
                    (dataA?.enhanced_reranked?.metrics_by_k?.['K=5']?.precision ?? 0) * 100,
                    (dataB?.enhanced_reranked?.metrics_by_k?.['K=5']?.precision ?? 0) * 100,
                    (v) => `${v.toFixed(2)}%`
                  )}
                  {renderMetricRow(
                    'Reranked MRR',
                    dataA?.enhanced_reranked?.mrr,
                    dataB?.enhanced_reranked?.mrr,
                    (v) => v.toFixed(4)
                  )}
                  {renderMetricRow(
                    'Baseline Vector MRR',
                    dataA?.baseline_vector?.mrr,
                    dataB?.baseline_vector?.mrr,
                    (v) => v.toFixed(4)
                  )}
                  {renderMetricRow(
                    'Abstention Accuracy',
                    (dataA?.enhanced_reranked?.abstention_accuracy ?? 1.0) * 100,
                    (dataB?.enhanced_reranked?.abstention_accuracy ?? 1.0) * 100,
                    (v) => `${v.toFixed(1)}%`
                  )}
                  {renderMetricRow(
                    'Median Total Latency',
                    dataA?.latency_statistics?.total?.median,
                    dataB?.latency_statistics?.total?.median,
                    (v) => `${v.toFixed(1)} ms`,
                    false // lower latency is better
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-white hover:bg-slate-900 transition-colors"
          >
            Close Diff View
          </button>
        </div>
      </div>
    </div>
  );
}
