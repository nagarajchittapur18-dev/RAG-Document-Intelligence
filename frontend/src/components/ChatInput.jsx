import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

export default function ChatInput({ onSendMessage, disabled, placeholder }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSendMessage(input.trim());
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  return (
    <form onSubmit={handleSubmit} className="relative bg-white border border-slate-300 rounded-xl shadow-sm focus-within:ring-2 focus-within:ring-brand-500 focus-within:border-brand-500 transition-all">
      <textarea
        ref={textareaRef}
        rows={1}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder || 'Ask a question about the selected document(s)...'}
        className="w-full pl-4 pr-14 py-3.5 text-sm text-slate-800 placeholder-slate-400 bg-transparent resize-none focus:outline-none max-h-40 leading-relaxed disabled:bg-slate-50 disabled:text-slate-400"
      />

      <div className="absolute right-2.5 bottom-2.5">
        <button
          type="submit"
          disabled={!input.trim() || disabled}
          className="p-2 rounded-lg bg-brand-600 text-white hover:bg-brand-700 disabled:bg-slate-200 disabled:text-slate-400 transition-colors shadow-sm focus:outline-none"
          aria-label="Send Message"
        >
          {disabled ? (
            <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </div>
    </form>
  );
}
