import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingIndicator({ text = 'Loading...', size = 'md' }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div className="flex flex-col items-center justify-center p-6 text-slate-500 gap-3">
      <Loader2 className={`${sizeClasses[size] || sizeClasses.md} animate-spin text-brand-600`} />
      {text && <p className="text-xs font-medium text-slate-600 animate-pulse">{text}</p>}
    </div>
  );
}
