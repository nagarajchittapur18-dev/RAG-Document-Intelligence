import React, { useState, useMemo } from 'react';
import {
  Search,
  Filter,
  Eye,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react';
import QuestionDetailDrawer from './QuestionDetailDrawer';

export default function QuestionLevelResults({ queries = [] }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedQuery, setSelectedQuery] = useState(null);
  const pageSize = 12;

  // Filter queries locally
  const filteredQueries = useMemo(() => {
    return queries.filter((q) => {
      const matchesSearch =
        !searchTerm.trim() ||
        q.id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        q.question?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesType =
        selectedType === 'all' || q.question_type === selectedType;

      const matchesDifficulty =
        selectedDifficulty === 'all' || q.difficulty === selectedDifficulty;

      const matchesStatus =
        selectedStatus === 'all' ||
        (selectedStatus === 'success' && q.error_classification === 'success') ||
        (selectedStatus === 'abstention' &&
          q.error_classification === 'unanswerable_abstention_success') ||
        (selectedStatus === 'failure' &&
          q.error_classification !== 'success' &&
          q.error_classification !== 'unanswerable_abstention_success');

      return matchesSearch && matchesType && matchesDifficulty && matchesStatus;
    });
  }, [queries, searchTerm, selectedType, selectedDifficulty, selectedStatus]);

  const totalPages = Math.ceil(filteredQueries.length / pageSize) || 1;
  const pagedItems = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredQueries.slice(start, start + pageSize);
  }, [filteredQueries, currentPage]);

  const questionTypes = [
    { value: 'all', label: 'All Question Types' },
    { value: 'fact', label: 'Fact' },
    { value: 'methodology', label: 'Methodology' },
    { value: 'algorithm', label: 'Algorithm' },
    { value: 'results', label: 'Results' },
    { value: 'comparison', label: 'Comparison' },
    { value: 'multi_hop', label: 'Multi-hop' },
    { value: 'contextual', label: 'Contextual' },
    { value: 'out_of_domain', label: 'Out of Domain' },
  ];

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-4 p-5">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">
            Per-Query Empirical Results & Evidence Inspector
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Browse and inspect granular retrieval ranks, evidence chunks, and candidate promotions for each query
          </p>
        </div>

        <div className="text-xs font-mono text-slate-500 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 self-start md:self-auto">
          Showing {filteredQueries.length} of {queries.length} queries
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by query ID or text..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-slate-50/50"
          />
        </div>

        {/* Type Selector */}
        <div>
          <select
            value={selectedType}
            onChange={(e) => {
              setSelectedType(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-slate-50/50 text-slate-700"
          >
            {questionTypes.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        {/* Difficulty */}
        <div>
          <select
            value={selectedDifficulty}
            onChange={(e) => {
              setSelectedDifficulty(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-slate-50/50 text-slate-700"
          >
            <option value="all">All Difficulties</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>

        {/* Status */}
        <div>
          <select
            value={selectedStatus}
            onChange={(e) => {
              setSelectedStatus(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-slate-50/50 text-slate-700"
          >
            <option value="all">All Statuses</option>
            <option value="success">Success (In Top-5)</option>
            <option value="abstention">Abstention Success</option>
            <option value="failure">Any Failures</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase text-[11px]">
              <th className="py-2.5 px-3">ID</th>
              <th className="py-2.5 px-3 min-w-[240px]">Query</th>
              <th className="py-2.5 px-3">Category</th>
              <th className="py-2.5 px-3">Difficulty</th>
              <th className="py-2.5 px-3 text-center">Vector Rank</th>
              <th className="py-2.5 px-3 text-center">Reranked Rank</th>
              <th className="py-2.5 px-3 text-center">Shift</th>
              <th className="py-2.5 px-3 text-right">Latency</th>
              <th className="py-2.5 px-3 text-center">Status</th>
              <th className="py-2.5 px-3 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {pagedItems.length === 0 ? (
              <tr>
                <td colSpan="10" className="py-8 text-center text-slate-400">
                  No evaluation queries match the applied filters.
                </td>
              </tr>
            ) : (
              pagedItems.map((q) => {
                const isAbstention =
                  q.error_classification === 'unanswerable_abstention_success';
                const vRank = q.vector_rank;
                const rRank = q.reranked_rank;
                const shift = vRank && rRank ? vRank - rRank : 0;

                return (
                  <tr
                    key={q.id}
                    className="hover:bg-slate-50/80 transition-colors cursor-pointer"
                    onClick={() => setSelectedQuery(q)}
                  >
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-800">
                      {q.id}
                    </td>
                    <td className="py-2.5 px-3 text-slate-800 font-medium max-w-[320px] truncate" title={q.question}>
                      {q.question}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700 capitalize">
                        {q.question_type?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold capitalize ${
                          q.difficulty === 'easy'
                            ? 'bg-emerald-50 text-emerald-700'
                            : q.difficulty === 'medium'
                            ? 'bg-blue-50 text-blue-700'
                            : 'bg-purple-50 text-purple-700'
                        }`}
                      >
                        {q.difficulty}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono">
                      {isAbstention ? (
                        <span className="text-slate-400">—</span>
                      ) : (
                        <span className="font-semibold text-slate-700">
                          #{vRank || '>15'}
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono">
                      {isAbstention ? (
                        <span className="text-slate-400">—</span>
                      ) : (
                        <span
                          className={`font-bold ${
                            rRank === 1
                              ? 'text-emerald-700'
                              : rRank <= 5
                              ? 'text-blue-700'
                              : 'text-amber-700'
                          }`}
                        >
                          #{rRank || '>5'}
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      {isAbstention ? (
                        <span className="text-slate-400">—</span>
                      ) : shift > 0 ? (
                        <span className="inline-flex items-center gap-0.5 text-emerald-600 font-bold text-[11px]">
                          <TrendingUp className="w-3 h-3" /> +{shift}
                        </span>
                      ) : shift < 0 ? (
                        <span className="inline-flex items-center gap-0.5 text-amber-600 font-bold text-[11px]">
                          <TrendingDown className="w-3 h-3" /> {shift}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-0.5 text-slate-400 font-bold text-[11px]">
                          <Minus className="w-3 h-3" /> 0
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-slate-600">
                      {q.total_latency_ms?.toFixed(1)} ms
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      {isAbstention ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-800 border border-blue-200">
                          Abstained
                        </span>
                      ) : q.error_classification === 'success' ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                          Top-5 Match
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-50 text-red-800 border border-red-200">
                          Failure
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-center" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => setSelectedQuery(q)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-brand-50 text-brand-700 hover:bg-brand-100 transition-colors"
                        title="View Detailed Retrieval Evidence"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Evidence</span>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between pt-2 text-xs text-slate-500">
        <div>
          Page <span className="font-semibold text-slate-800">{currentPage}</span> of{' '}
          <span className="font-semibold text-slate-800">{totalPages}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
            disabled={currentPage === 1}
            className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
            disabled={currentPage === totalPages}
            className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Detail Drawer Modal */}
      {selectedQuery && (
        <QuestionDetailDrawer
          queryItem={selectedQuery}
          onClose={() => setSelectedQuery(null)}
        />
      )}
    </div>
  );
}
