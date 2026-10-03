import React, { useState, useRef, useEffect } from 'react';
import {
  MessageSquare,
  Sparkles,
  Layers,
  Trash2,
  Filter,
  Check,
  ChevronDown,
  Info,
  BookOpen,
  Plus,
  Clock,
  History,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import ErrorMessage from '../components/ErrorMessage';
import api from '../services/api';

export default function Chat() {
  const { documents, selectedDocIds, setSelectedDocIds } = useApp();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showDocSelector, setShowDocSelector] = useState(false);
  const [showSessionSelector, setShowSessionSelector] = useState(false);

  // Chat sessions state
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);

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
      const data = await api.getSession(sessionId);
      setCurrentSessionId(sessionId);
      // Format messages
      const formatted = (data.messages || []).map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        sources: m.sources || [],
        timestamp: m.created_at,
      }));
      setMessages(formatted);
      setShowSessionSelector(false);
    } catch (err) {
      setError('Failed to load conversation history.');
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setError(null);
    setShowSessionSelector(false);
  };

  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation();
    try {
      await api.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (currentSessionId === sessionId) {
        handleNewChat();
      }
    } catch (err) {
      console.error('Failed to delete chat session:', err);
    }
  };

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
    setSelectedDocIds([]); // Empty array represents all documents
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
      // If no active session, create one with the question as title
      if (!activeSession) {
        const title = questionText.slice(0, 36) + (questionText.length > 36 ? '...' : '');
        const newSession = await api.createSession(title);
        activeSession = newSession.id;
        setCurrentSessionId(activeSession);
        setSessions((prev) => [newSession, ...prev]);
      }

      const docScope = selectedDocIds.length > 0 ? selectedDocIds : null;
      const response = await api.askQuestion(questionText, docScope, null, activeSession);

      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
        retrievedChunks: response.retrieved_chunks,
        responseTimeMs: response.response_time_ms,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, aiMessage]);
      loadSessions(); // refresh updated_at
    } catch (err) {
      setError(err.message || 'Failed to generate answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Helper label for document scope selector
  const getScopeLabel = () => {
    if (selectedDocIds.length === 0) {
      return `All Documents (${documents.length})`;
    }
    if (selectedDocIds.length === 1) {
      const doc = documents.find((d) => d.id === selectedDocIds[0]);
      return doc ? doc.filename : '1 Document Selected';
    }
    return `${selectedDocIds.length} Documents Selected`;
  };

  const activeSessionTitle = currentSessionId
    ? sessions.find((s) => s.id === currentSessionId)?.title || 'Active Session'
    : 'New Conversation';

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] max-w-5xl mx-auto">
      {/* Chat Header & Document Scoper */}
      <div className="bg-white border border-slate-200 rounded-t-2xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-3 relative z-20">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center border border-brand-100">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="font-bold text-slate-900 text-sm">DocuRAG AI Assistant</h2>
            <p className="text-[11px] text-slate-500">
              Grounded Question Answering with Verified Citations
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* History / Sessions dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowSessionSelector(!showSessionSelector)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-50 border border-slate-300 text-slate-700 hover:bg-slate-100 transition-colors"
              title="Chat History"
            >
              <History className="w-3.5 h-3.5 text-slate-500" />
              <span className="max-w-[130px] truncate">{activeSessionTitle}</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {showSessionSelector && (
              <>
                <div
                  className="fixed inset-0 z-20"
                  onClick={() => setShowSessionSelector(false)}
                />
                <div className="absolute right-0 mt-2 w-72 sm:w-80 bg-white border border-slate-200 rounded-xl shadow-xl z-30 p-2 text-xs space-y-1">
                  <div className="p-2 border-b border-slate-100 flex items-center justify-between font-semibold text-slate-700">
                    <span>Chat History</span>
                    <button
                      onClick={handleNewChat}
                      className="inline-flex items-center gap-1 text-[11px] text-brand-600 hover:text-brand-700 font-medium"
                    >
                      <Plus className="w-3 h-3" />
                      <span>New Chat</span>
                    </button>
                  </div>

                  {sessions.length === 0 ? (
                    <div className="p-4 text-center text-slate-400 text-xs">
                      No conversations yet. Ask a question to begin.
                    </div>
                  ) : (
                    <div className="max-h-60 overflow-y-auto space-y-1 p-1">
                      {sessions.map((s) => (
                        <div
                          key={s.id}
                          onClick={() => handleSelectSession(s.id)}
                          className={`flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                            currentSessionId === s.id
                              ? 'bg-brand-50 text-brand-900 font-medium border border-brand-200'
                              : 'hover:bg-slate-50 text-slate-700'
                          }`}
                        >
                          <div className="truncate pr-2">
                            <p className="truncate text-xs">{s.title}</p>
                            <span className="text-[10px] text-slate-400 flex items-center gap-1 mt-0.5">
                              <Clock className="w-2.5 h-2.5" />
                              {new Date(s.updated_at).toLocaleDateString()}
                            </span>
                          </div>
                          <button
                            onClick={(e) => handleDeleteSession(e, s.id)}
                            className="p-1 text-slate-400 hover:text-red-500 rounded transition-colors"
                            title="Delete Session"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {/* New Chat Button */}
          <button
            onClick={handleNewChat}
            className="p-1.5 rounded-lg text-slate-600 hover:bg-slate-100 border border-slate-300 transition-colors"
            title="Start New Chat"
          >
            <Plus className="w-4 h-4" />
          </button>

          {/* Document Scope Selector Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowDocSelector(!showDocSelector)}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-50 border border-slate-300 text-slate-700 hover:bg-slate-100 transition-colors"
            >
              <Filter className="w-3.5 h-3.5 text-slate-500" />
              <span className="max-w-[150px] sm:max-w-[200px] truncate">{getScopeLabel()}</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {/* Dropdown Menu */}
            {showDocSelector && (
              <>
                <div
                  className="fixed inset-0 z-20"
                  onClick={() => setShowDocSelector(false)}
                />
                <div className="absolute right-0 mt-2 w-72 sm:w-80 bg-white border border-slate-200 rounded-xl shadow-xl z-30 p-2 text-xs space-y-1">
                  <div className="p-2 border-b border-slate-100 font-semibold text-slate-700 flex items-center justify-between">
                    <span>Retrieval Document Scope</span>
                    <button
                      onClick={handleSelectAll}
                      className="text-brand-600 hover:underline font-normal text-[11px]"
                    >
                      Select All
                    </button>
                  </div>

                  {documents.length === 0 ? (
                    <div className="p-4 text-center text-slate-400 text-xs">
                      No documents available. Upload PDFs first.
                    </div>
                  ) : (
                    <div className="max-h-56 overflow-y-auto space-y-1 p-1">
                      <button
                        onClick={handleSelectAll}
                        className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition-colors ${
                          selectedDocIds.length === 0
                            ? 'bg-brand-50 text-brand-800 font-medium'
                            : 'hover:bg-slate-50 text-slate-700'
                        }`}
                      >
                        <span className="truncate">All Documents ({documents.length})</span>
                        {selectedDocIds.length === 0 && <Check className="w-4 h-4 text-brand-600" />}
                      </button>

                      {documents.map((doc) => {
                        const isSelected = selectedDocIds.includes(doc.id);
                        return (
                          <button
                            key={doc.id}
                            onClick={() => handleToggleDoc(doc.id)}
                            className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition-colors ${
                              isSelected
                                ? 'bg-brand-50 text-brand-800 font-medium'
                                : 'hover:bg-slate-50 text-slate-700'
                            }`}
                          >
                            <div className="truncate pr-2">
                              <p className="truncate">{doc.filename}</p>
                              <span className="text-[10px] text-slate-400">
                                {doc.pages} p • {doc.chunks} chunks
                              </span>
                            </div>
                            {isSelected && <Check className="w-4 h-4 text-brand-600 flex-shrink-0" />}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 bg-slate-50/70 border-x border-slate-200 p-4 sm:p-6 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4 max-w-lg mx-auto">
            <div className="w-14 h-14 rounded-2xl bg-white text-brand-600 border border-slate-200 shadow-sm flex items-center justify-center">
              <MessageSquare className="w-7 h-7" />
            </div>

            <div>
              <h3 className="font-bold text-slate-900 text-base">
                Start a Conversation with Your Documents
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Ask natural language questions. DocuRAG retrieves relevant passages from ChromaDB
                and instructs Gemini to ground its response exclusively on your papers.
              </p>
            </div>

            {documents.length > 0 && (
              <div className="w-full pt-4 space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Suggested Questions
                </p>
                <div className="grid gap-2 text-left">
                  {[
                    'What is the primary research methodology proposed in the paper?',
                    'Summarize the experimental evaluation and benchmark results.',
                    'What are the four processing tiers in the system architecture?',
                  ].map((sugg, i) => (
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
          <div className="space-y-4">
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
                    <span>Retrieving passages & synthesizing grounded answer...</span>
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
        <div className="px-4 bg-white border-x border-slate-200">
          <ErrorMessage message={error} onRetry={() => setError(null)} />
        </div>
      )}

      {/* Input Section */}
      <div className="bg-white border border-slate-200 rounded-b-2xl p-4 shadow-sm">
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={loading || documents.length === 0}
          placeholder={
            documents.length === 0
              ? 'Upload a document before asking questions...'
              : `Ask a question about ${getScopeLabel()}...`
          }
        />
        <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 px-1">
          <span>Press Enter to send, Shift + Enter for new lines</span>
          <span className="flex items-center gap-1">
            <BookOpen className="w-3 h-3 text-slate-400" />
            Grounding: Strict
          </span>
        </div>
      </div>
    </div>
  );
}
