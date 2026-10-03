import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Files,
  MessageSquare,
  Cpu,
  Layers,
  Sparkles,
  X,
  Database,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import { LogOut } from 'lucide-react';

export default function Sidebar({ isOpen, onClose }) {
  const { documents, systemHealth } = useApp();
  const { user, logout } = useAuth();

  const userInitials = user?.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U';

  const navItems = [
    {
      to: '/',
      label: 'Dashboard',
      icon: LayoutDashboard,
    },
    {
      to: '/documents',
      label: 'Documents',
      icon: Files,
      badge: documents.length,
    },
    {
      to: '/chat',
      label: 'AI Chat',
      icon: MessageSquare,
      highlight: true,
    },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-slate-900 text-slate-300 flex flex-col transition-transform duration-200 ease-in-out lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Mobile Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 lg:hidden">
          <div className="flex items-center gap-2 text-white font-bold text-lg">
            <span>DocuRAG</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white rounded-md hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation list */}
        <div className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Platform
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-brand-600 text-white shadow-sm'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && (
                  <span
                    className={`px-2 py-0.5 text-xs rounded-full font-semibold ${
                      item.badge > 0
                        ? 'bg-brand-700/60 text-brand-100'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
                {item.highlight && (
                  <span className="flex h-2 w-2 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                )}
              </NavLink>
            );
          })}
        </div>

        {/* Architecture & Pipeline Badge */}
        <div className="p-4 mx-4 mb-4 rounded-xl bg-slate-800/80 border border-slate-700/60 text-xs space-y-2.5">
          <div className="flex items-center gap-1.5 text-slate-200 font-semibold">
            <Cpu className="w-3.5 h-3.5 text-brand-400" />
            <span>RAG Architecture</span>
          </div>

          <div className="space-y-1.5 text-[11px] text-slate-400">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Database className="w-3 h-3 text-slate-500" /> Vector DB
              </span>
              <span className="font-mono text-slate-300">ChromaDB</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Layers className="w-3 h-3 text-slate-500" /> Embeddings
              </span>
              <span className="font-mono text-slate-300">all-MiniLM-L6</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-slate-500" /> Generator
              </span>
              <span className="font-mono text-slate-300">
                {systemHealth?.environment?.gemini_model || 'Gemini Flash'}
              </span>
            </div>
          </div>
        </div>

        {/* User Card */}
        {user && (
          <div className="px-4 py-3 mx-4 mb-3 rounded-xl bg-slate-800/50 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold text-xs flex items-center justify-center shrink-0">
                {userInitials}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-semibold text-slate-200 truncate">{user.name}</p>
                <p className="text-[11px] text-slate-400 truncate">{user.email}</p>
              </div>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-700/50 rounded-lg transition-colors ml-1"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* User / Academic footer */}
        <div className="px-5 py-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
          <span>DocuRAG v1.0</span>
          <span>Academic Edition</span>
        </div>
      </aside>
    </>
  );
}
