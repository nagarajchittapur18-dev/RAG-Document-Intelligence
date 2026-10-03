import React, { useState, useRef, useEffect } from 'react';
import {
  MessageSquare,
  Sparkles,
  Layers,
  Trash2,
  Filter,
  Check,
  ChevronDown,
  ChevronUp,
  Info,
  BookOpen,
  Plus,
  Clock,
  History,
  CheckSquare,
  Square,
  FileText,
  HelpCircle,
  Scale,
  MoreVertical,
  Edit3,
  AlertTriangle,
  Menu,
  X,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import ErrorMessage from '../components/ErrorMessage';
import api from '../services/api';

/**
 * Converts ISO date string into human-readable relative time string.
 */
function formatTimeAgo(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  const now = new Date();
  const diffSec = Math.floor((now - date) / 1000);
  if (diffSec < 45) return 'Just now';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export default function Chat() {
  const { documents, selectedDocIds, setSelectedDocIds } = useApp();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [knowledgePanelExpanded, setKnowledgePanelExpanded] = useState(false);

  // Chat sessions state
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [activeSessionDetail, setActiveSessionDetail] = useState(null);
  const [unavailableDocsWarning, setUnavailableDocsWarning] = useState(null);

  // Mobile drawer state
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // Action menu & modal states
  const [activeMenuSessionId, setActiveMenuSessionId] = useState(null);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [sessionToRename, setSessionToRename] = useState(null);
  const [renameInput, setRenameInput] = useState('');

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load chat sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data);
    } catch (err) {
      console.error('Failed to load chat sessions:', err);
    }
  };

  const handleSelectSession = async (sessionId) => {
    try {
      setLoading(true);
      setError(null);
      setActiveMenuSessionId(null);
      setMobileSidebarOpen(false);

      const data = await api.getSession(sessionId);
      setCurrentSessionId(sessionId);
      setActiveSessionDetail(data.session);

      // Handle missing / deleted documents warning
      if (data.unavailable_documents_count > 0 || data.warning_message) {
        setUnavailableDocsWarning(
          data.warning_message ||
            `${data.unavailable_documents_count} document(s) previously used in this conversation are no longer available.`
        );
      } else {
        setUnavailableDocsWarning(null);
      }

      // Restore session document scope if available
      if (data.session?.document_ids && data.session.document_ids.length > 0) {
        setSelectedDocIds(data.session.document_ids);
      }

      // Format messages
      const formatted = (data.messages || []).map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        sources: m.sources || [],
        timestamp: m.created_at,
      }));
      setMessages(formatted);
    } catch (err) {
      setError('Failed to load conversation history.');
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setActiveSessionDetail(null);
    setMessages([]);
    setError(null);
    setUnavailableDocsWarning(null);
    setActiveMenuSessionId(null);
    setMobileSidebarOpen(false);
  };

  const handleConfirmDelete = async () => {
    if (!sessionToDelete) return;
    try {
      await api.deleteSession(sessionToDelete.id);
      setSessions((prev) => prev.filter((s) => s.id !== sessionToDelete.id));
      if (currentSessionId === sessionToDelete.id) {
        handleNewChat();
      }
      setSessionToDelete(null);
    } catch (err) {
      console.error('Failed to delete chat session:', err);
      setError('Failed to delete chat session.');
    }
  };

  const handleConfirmRename = async (e) => {
    e.preventDefault();
    if (!sessionToRename || !renameInput.trim()) return;
    try {
      const updated = await api.renameSession(sessionToRename.id, renameInput.trim());
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionToRename.id ? { ...s, title: updated.title } : s))
      );
      if (currentSessionId === sessionToRename.id) {
        setActiveSessionDetail((prev) => (prev ? { ...prev, title: updated.title } : prev));
      }
      setSessionToRename(null);
      setRenameInput('');
    } catch (err) {
      console.error('Failed to rename session:', err);
      setError('Failed to rename conversation.');
    }
  };

  // Only allow completed documents to be selected
  const completedDocs = documents.filter((d) => d.status === 'completed');

  const handleToggleDoc = (docId) => {
    setSelectedDocIds((prev) => {
      if (prev.includes(docId)) {
        return prev.filter((id) => id !== docId);
      } else {
        return [...prev, docId];
      }
    });
  };

  const handleSelectAll = () => {
    setSelectedDocIds(completedDocs.map((d) => d.id));
  };

  const handleClearSelection = () => {
    setSelectedDocIds([]); // Empty array represents searching across all documents
  };

  const handleSendMessage = async (questionText) => {
    setError(null);
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: questionText,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      let activeSession = currentSessionId;
      const docScope = selectedDocIds.length > 0 ? selectedDocIds : null;

      // If no active session, create one with the current document scope
      if (!activeSession) {
        const newSession = await api.createSession('New Conversation', docScope);
        activeSession = newSession.id;
        setCurrentSessionId(activeSession);
        setActiveSessionDetail(newSession);
        setSessions((prev) => [newSession, ...prev]);
      }

      // Submit message to active session
      const response = await api.sendSessionMessage(activeSession, questionText);

      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
        retrievedChunks: response.retrieved_chunks,
        documentsSearched: response.documents_searched,
        responseTimeMs: response.response_time_ms,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, aiMessage]);
      loadSessions(); // refresh session titles and timestamps
    } catch (err) {
      setError(err.message || 'Failed to generate answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Scope status summary label
  const getScopeBadge = () => {
    if (selectedDocIds.length === 0) {
      return {
        label: `All Documents (${completedDocs.length})`,
        detail: 'Searching all your documents',
        isComparison: completedDocs.length > 1,
        color: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      };
    }
    if (selectedDocIds.length === 1) {
      const doc = completedDocs.find((d) => d.id === selectedDocIds[0]);
      return {
        label: doc ? doc.filename : '1 Document',
        detail: 'Single document focus',
        isComparison: false,
        color: 'bg-slate-100 text-slate-700 border-slate-300',
      };
    }
    return {
      label: `${selectedDocIds.length} Documents Selected`,
      detail: 'Multi-document comparison mode',
      isComparison: true,
      color: 'bg-emerald-50 text-emerald-800 border-emerald-300',
    };
  };

  const scopeBadge = getScopeBadge();

  const activeSessionTitle = currentSessionId
    ? sessions.find((s) => s.id === currentSessionId)?.title || activeSessionDetail?.title || 'Active Session'
    : 'New Conversation';

  // Render Sidebar Component (reused for desktop & mobile drawer)
  const renderSidebarContent = () => (
    <div className="flex flex-col h-full bg-white border-r border-slate-200">
      {/* Sidebar Header & New Chat Button */}
      <div className="p-4 border-b border-slate-200/80 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center font-bold text-xs border border-brand-100">
              RAG
            </div>
            <span className="font-bold text-slate-900 text-sm">Conversations</span>
          </div>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold">
            {sessions.length}
          </span>
        </div>

        <button
          onClick={handleNewChat}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-xs transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sessions.length === 0 ? (
          <div className="p-6 text-center text-slate-400 text-xs space-y-2">
            <History className="w-8 h-8 mx-auto text-slate-300" />
            <p className="font-medium">No conversations yet</p>
            <p className="text-[11px] text-slate-400">Ask a question to start your first chat session.</p>
          </div>
        ) : (
          sessions.map((s) => {
            const isSelected = currentSessionId === s.id;
            const isMenuOpen = activeMenuSessionId === s.id;
            return (
              <div
                key={s.id}
                onClick={() => handleSelectSession(s.id)}
                className={`group relative flex items-start justify-between p-2.5 rounded-xl cursor-pointer transition-all border ${
                  isSelected
                    ? 'bg-brand-50/70 border-brand-300 text-brand-950 font-semibold shadow-2xs'
                    : 'bg-white border-transparent hover:bg-slate-50 hover:border-slate-200 text-slate-700'
                }`}
              >
                <div className="overflow-hidden flex-1 pr-2">
                  <p className="text-xs truncate font-medium">{s.title || 'Untitled Chat'}</p>
                  <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-1">
                    <span>{formatTimeAgo(s.updated_at)}</span>
                    {s.document_count > 0 && (
                      <>
                        <span>•</span>
                        <span className="flex items-center gap-0.5 text-slate-500 font-medium">
                          <BookOpen className="w-2.5 h-2.5" />
                          {s.document_count} doc{s.document_count > 1 ? 's' : ''}
                        </span>
                      </>
                    )}
                    {s.message_count > 0 && (
                      <>
                        <span>•</span>
                        <span>{s.message_count} msg{s.message_count > 1 ? 's' : ''}</span>
                      </>
                    )}
                  </div>
                </div>

                {/* 3-Dot Action Menu Button */}
                <div className="relative" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => setActiveMenuSessionId(isMenuOpen ? null : s.id)}
                    className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
                    title="Conversation Options"
                  >
                    <MoreVertical className="w-3.5 h-3.5" />
                  </button>

                  {/* Dropdown Menu */}
                  {isMenuOpen && (
                    <>
                      <div
                        className="fixed inset-0 z-30"
                        onClick={() => setActiveMenuSessionId(null)}
                      />
                      <div className="absolute right-0 mt-1 w-36 bg-white border border-slate-200 rounded-xl shadow-lg z-40 p-1 text-xs">
                        <button
                          onClick={() => {
                            setActiveMenuSessionId(null);
                            setSessionToRename(s);
                            setRenameInput(s.title);
                          }}
                          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-slate-700 hover:bg-slate-100 text-left transition-colors"
                        >
                          <Edit3 className="w-3.5 h-3.5 text-slate-500" />
                          <span>Rename</span>
                        </button>
                        <button
                          onClick={() => {
                            setActiveMenuSessionId(null);
                            setSessionToDelete(s);
                          }}
                          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-red-600 hover:bg-red-50 text-left transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5 text-red-500" />
                          <span>Delete</span>
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );

  return (
    <div className="flex h-[calc(100vh-6.5rem)] max-w-7xl mx-auto bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden relative">
      {/* Desktop Persistent Sidebar (w-72) */}
      <div className="hidden md:block w-72 h-full flex-shrink-0">
        {renderSidebarContent()}
      </div>

      {/* Mobile Slide-Over Drawer */}
      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <div className="relative w-72 max-w-[80vw] h-full z-10 shadow-2xl">
            <button
              onClick={() => setMobileSidebarOpen(false)}
              className="absolute top-3 right-3 p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 z-20"
            >
              <X className="w-4 h-4" />
            </button>
            {renderSidebarContent()}
          </div>
        </div>
      )}

      {/* Main Chat Interface */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50/50">
        {/* Top Header Bar */}
        <div className="bg-white border-b border-slate-200 p-3 sm:p-4 flex flex-wrap items-center justify-between gap-3 relative z-20 shadow-2xs">
          <div className="flex items-center gap-2.5">
            {/* Mobile Hamburger Toggle */}
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="md:hidden p-1.5 rounded-lg text-slate-600 hover:bg-slate-100 border border-slate-300"
              title="View Conversations"
            >
              <Menu className="w-4 h-4" />
            </button>

            <div className="w-8 h-8 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center border border-brand-100 flex-shrink-0">
              <Sparkles className="w-4 h-4" />
            </div>

            <div className="overflow-hidden">
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-slate-900 text-sm truncate max-w-[180px] sm:max-w-xs md:max-w-sm">
                  {activeSessionTitle}
                </h2>
                {currentSessionId && (
                  <button
                    onClick={() => {
                      const cur = sessions.find((s) => s.id === currentSessionId);
                      if (cur) {
                        setSessionToRename(cur);
                        setRenameInput(cur.title);
                      }
                    }}
                    className="text-slate-400 hover:text-slate-700 p-0.5 rounded transition-colors"
                    title="Rename Conversation"
                  >
                    <Edit3 className="w-3 h-3" />
                  </button>
                )}
              </div>
              <p className="text-[11px] text-slate-500 hidden sm:block">
                Conversational Memory & Document-Grounded Q&A
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Toggle Knowledge Sources Drawer Button */}
            <button
              onClick={() => setKnowledgePanelExpanded(!knowledgePanelExpanded)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-colors shadow-2xs ${scopeBadge.color}`}
            >
              {scopeBadge.isComparison ? (
                <Scale className="w-3.5 h-3.5" />
              ) : (
                <BookOpen className="w-3.5 h-3.5" />
              )}
              <span className="max-w-[140px] sm:max-w-[180px] truncate">{scopeBadge.label}</span>
              {knowledgePanelExpanded ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        </div>

        {/* Deleted / Unavailable Documents Warning Alert */}
        {unavailableDocsWarning && (
          <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-xs text-amber-800 flex items-center justify-between gap-2 animate-fadeIn">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
              <span>{unavailableDocsWarning} You can continue this chat using remaining available documents.</span>
            </div>
            <button
              onClick={() => setUnavailableDocsWarning(null)}
              className="text-amber-600 hover:text-amber-800 p-1"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        )}

        {/* Expandable Knowledge Sources Panel */}
        {knowledgePanelExpanded && (
          <div className="bg-slate-50 border-b border-slate-200 p-4 shadow-inner space-y-3 animate-fadeIn">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/80 pb-2.5">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Knowledge Sources
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 font-medium">
                    {scopeBadge.detail}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Select documents to constrain retrieval and cross-document reasoning.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleSelectAll}
                  className="px-2.5 py-1 text-xs font-medium text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 rounded-lg transition-colors"
                >
                  Select All
                </button>
                <button
                  onClick={handleClearSelection}
                  className="px-2.5 py-1 text-xs font-medium text-slate-600 bg-white hover:bg-slate-100 border border-slate-300 rounded-lg transition-colors"
                >
                  Search All Docs
                </button>
              </div>
            </div>

            {completedDocs.length === 0 ? (
              <div className="p-4 text-center text-slate-400 text-xs bg-white rounded-xl border border-slate-200">
                No completed documents found. Upload PDFs to activate retrieval.
              </div>
            ) : (
              <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3 max-h-48 overflow-y-auto p-1">
                {completedDocs.map((doc) => {
                  const isSelected = selectedDocIds.includes(doc.id);
                  return (
                    <div
                      key={doc.id}
                      onClick={() => handleToggleDoc(doc.id)}
                      className={`flex items-start gap-2.5 p-2.5 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-brand-50/80 border-brand-300 text-brand-900 shadow-2xs'
                          : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
                      }`}
                    >
                      <div className="mt-0.5 text-brand-600">
                        {isSelected ? (
                          <CheckSquare className="w-4 h-4 text-brand-600" />
                        ) : (
                          <Square className="w-4 h-4 text-slate-400" />
                        )}
                      </div>
                      <div className="overflow-hidden flex-1">
                        <p className="text-xs font-medium truncate" title={doc.filename}>
                          {doc.filename}
                        </p>
                        <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                          <span>{doc.pages} p</span>
                          <span>•</span>
                          <span>{doc.chunks} chunks</span>
                          <span className="ml-auto text-[9px] font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
                            ready
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Messages Scroll Area */}
        <div className="flex-1 p-4 sm:p-6 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4 max-w-lg mx-auto">
              <div className="w-14 h-14 rounded-2xl bg-white text-brand-600 border border-slate-200 shadow-sm flex items-center justify-center">
                <MessageSquare className="w-7 h-7" />
              </div>

              <div>
                <h3 className="font-bold text-slate-900 text-base">
                  Persistent Document Intelligence
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Ask questions, query across multiple papers, and ask contextual follow-ups.
                  Your conversation history and document scopes are saved automatically.
                </p>
              </div>

              {completedDocs.length > 0 && (
                <div className="w-full pt-4 space-y-2">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                    {selectedDocIds.length > 1
                      ? 'Suggested Multi-Document Comparison Questions'
                      : 'Suggested Research Questions'}
                  </p>
                  <div className="grid gap-2 text-left">
                    {(selectedDocIds.length > 1
                      ? [
                          'Compare the primary research methodologies across the selected papers.',
                          'What datasets and experimental benchmarks are evaluated in both studies?',
                          'Compare the reported accuracy, efficiency, and performance results.',
                          'What are the key algorithmic differences and trade-offs between the approaches?',
                        ]
                      : [
                          'What is the primary research methodology proposed in the paper?',
                          'Summarize the experimental evaluation and benchmark results.',
                          'What are the main system architecture components and design tiers?',
                        ]
                    ).map((sugg, i) => (
                      <button
                        key={i}
                        onClick={() => handleSendMessage(sugg)}
                        className="p-2.5 rounded-xl bg-white border border-slate-200 text-xs text-slate-700 hover:border-brand-300 hover:bg-brand-50/30 transition-all text-left shadow-2xs"
                      >
                        "{sugg}"
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4 max-w-3xl mx-auto">
              {messages.map((m) => (
                <ChatMessage key={m.id} message={m} />
              ))}

              {loading && (
                <div className="flex justify-start mb-6">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-brand-600 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Sparkles className="w-4 h-4 animate-spin" />
                    </div>
                    <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm p-4 shadow-sm text-xs text-slate-600 flex items-center gap-2">
                      <span className="flex space-x-1">
                        <span className="w-2 h-2 bg-brand-500 rounded-full animate-bounce"></span>
                        <span
                          className="w-2 h-2 bg-brand-500 rounded-full animate-bounce"
                          style={{ animationDelay: '0.15s' }}
                        ></span>
                        <span
                          className="w-2 h-2 bg-brand-500 rounded-full animate-bounce"
                          style={{ animationDelay: '0.3s' }}
                        ></span>
                      </span>
                      <span>
                        Thinking & retrieving evidence across {scopeBadge.label}...
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Error notification */}
        {error && (
          <div className="px-4 bg-white border-t border-slate-200">
            <ErrorMessage message={error} onRetry={() => setError(null)} />
          </div>
        )}

        {/* Input Section */}
        <div className="bg-white border-t border-slate-200 p-3 sm:p-4">
          <div className="max-w-3xl mx-auto">
            <ChatInput
              onSendMessage={handleSendMessage}
              disabled={loading || completedDocs.length === 0}
              placeholder={
                completedDocs.length === 0
                  ? 'Upload a document before asking questions...'
                  : `Ask a question about ${scopeBadge.label}...`
              }
            />
            <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 px-1">
              <span>Press Enter to send, Shift + Enter for new lines</span>
              <span className="flex items-center gap-1.5 font-medium text-slate-500">
                <BookOpen className="w-3 h-3 text-brand-600" />
                <span>Scope: {scopeBadge.label}</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {sessionToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-2xs animate-fadeIn">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-red-600">
              <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center">
                <Trash2 className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Delete this conversation?</h3>
                <p className="text-xs text-slate-500">This action cannot be undone.</p>
              </div>
            </div>

            <p className="text-xs text-slate-600">
              Are you sure you want to delete <span className="font-semibold text-slate-800">"{sessionToDelete.title}"</span>?
              This will only remove conversation messages. Your uploaded PDF documents will not be affected.
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setSessionToDelete(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-red-600 hover:bg-red-700 transition-colors shadow-xs"
              >
                Delete Conversation
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rename Modal Dialog */}
      {sessionToRename && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-2xs animate-fadeIn">
          <form
            onSubmit={handleConfirmRename}
            className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center text-brand-600">
                <Edit3 className="w-5 h-5 text-brand-600" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Rename Conversation</h3>
                <p className="text-xs text-slate-500">Enter a descriptive title for this chat.</p>
              </div>
            </div>

            <div>
              <input
                type="text"
                value={renameInput}
                onChange={(e) => setRenameInput(e.target.value)}
                placeholder="Conversation Title"
                maxLength={100}
                autoFocus
                className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setSessionToRename(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!renameInput.trim()}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 disabled:opacity-50 transition-colors shadow-xs"
              >
                Save Changes
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
