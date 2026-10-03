import React from 'react';
import { FolderOpen } from 'lucide-react';

export default function EmptyState({
  icon: Icon = FolderOpen,
  title = 'No items found',
  description = 'There are no records to display at this time.',
  actionLabel,
  onAction,
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-white rounded-xl border border-dashed border-slate-300">
      <div className="flex items-center justify-center w-12 h-12 mb-3 rounded-full bg-slate-100 text-slate-500">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <p className="mt-1 text-xs text-slate-500 max-w-sm">{description}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="mt-4 inline-flex items-center px-3.5 py-2 rounded-lg text-xs font-semibold bg-brand-600 text-white shadow-sm hover:bg-brand-700 transition-colors focus:ring-2 focus:ring-brand-500"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
