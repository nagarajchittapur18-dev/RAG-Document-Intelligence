import React from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Menu, Sparkles, Activity } from 'lucide-react';
import { useApp } from '../context/AppContext';

export default function Navbar({ onToggleSidebar }) {
  const { systemHealth, documents } = useApp();
  const isHealthy = systemHealth?.status === 'ok';

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200 shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleSidebar}
            className="p-2 text-slate-500 rounded-lg lg:hidden hover:bg-slate-100 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
            aria-label="Toggle Navigation"
          >
            <Menu className="w-5 h-5" />
          </button>

          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex items-center justify-center w-9 h-9 bg-brand-600 text-white rounded-lg shadow-sm">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5 font-bold text-slate-900 tracking-tight text-lg leading-tight">
                DocuRAG
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-brand-50 text-brand-700 border border-brand-200">
                  <Sparkles className="w-2.5 h-2.5 mr-0.5 text-brand-600" />
                  RAG
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                Intelligent Document Question Answering
              </p>
            </div>
          </Link>
        </div>

        <div className="flex items-center gap-3">
          {/* Health indicator */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
              isHealthy
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-amber-50 text-amber-700 border-amber-200'
            }`}
            title={
              isHealthy
                ? `FastAPI Online | Model: ${systemHealth?.environment?.gemini_model || 'Gemini'}`
                : 'Backend Disconnected'
            }
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
              }`}
            />
            <span className="hidden md:inline">
              {isHealthy ? 'Backend Connected' : 'Connecting to API...'}
            </span>
          </div>

          <div className="hidden sm:flex items-center text-xs text-slate-500 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
            <span className="font-semibold text-slate-700 mr-1">{documents.length}</span>
            <span>PDFs Indexed</span>
          </div>
        </div>
      </div>
    </header>
  );
}
