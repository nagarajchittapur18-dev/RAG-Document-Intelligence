import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export default function ErrorMessage({ message, onRetry }) {
  if (!message) return null;

  return (
    <div className="flex items-start gap-3 p-4 my-3 text-red-800 bg-red-50 border border-red-200 rounded-xl">
      <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-600 mt-0.5" />
      <div className="flex-1 text-xs">
        <p className="font-semibold text-red-900">Application Notice</p>
        <p className="mt-0.5 text-red-700">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-red-700 bg-white border border-red-300 rounded-md shadow-sm hover:bg-red-50"
        >
          <RefreshCw className="w-3 h-3" />
          Retry
        </button>
      )}
    </div>
  );
}
