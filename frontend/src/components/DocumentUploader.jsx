import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import api from '../services/api';
import { formatBytes } from '../utils/helpers';

export default function DocumentUploader({ onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState(null); // 'uploading' | 'processing' | 'completed' | 'error'
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    if (!file) return 'No file selected.';
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return 'Only PDF documents (.pdf) are supported.';
    }
    const maxBytes = 25 * 1024 * 1024; // 25 MB
    if (file.size > maxBytes) {
      return `File exceeds the 25 MB limit (${formatBytes(file.size)}).`;
    }
    if (file.size === 0) {
      return 'Selected file is empty (0 bytes).';
    }
    return null;
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    setErrorMessage('');
    const error = validateFile(file);
    if (error) {
      setErrorMessage(error);
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
    startUpload(file);
  };

  const startUpload = async (file) => {
    try {
      setProcessingStatus('uploading');
      setUploadProgress(10);

      const result = await api.uploadDocument(file, (percent) => {
        setUploadProgress(Math.min(percent, 90));
        if (percent >= 90) {
          setProcessingStatus('processing');
        }
      });

      setUploadProgress(100);
      setProcessingStatus('completed');

      setTimeout(() => {
        if (onUploadSuccess) {
          onUploadSuccess(result);
        }
        setSelectedFile(null);
        setProcessingStatus(null);
        setUploadProgress(0);
      }, 1200);

    } catch (err) {
      setProcessingStatus('error');
      setErrorMessage(err.message || 'Upload failed. Please check file and server.');
    }
  };

  return (
    <div className="w-full">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleFileDrop}
        onClick={() => !processingStatus && fileInputRef.current?.click()}
        className={`relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-2xl cursor-pointer transition-all ${
          isDragging
            ? 'border-brand-500 bg-brand-50/60 scale-[1.005]'
            : 'border-slate-300 bg-white hover:border-slate-400 hover:bg-slate-50/50'
        } ${processingStatus ? 'pointer-events-none opacity-90' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileSelect}
          className="hidden"
        />

        <div className="flex flex-col items-center text-center">
          <div className="w-14 h-14 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mb-3 shadow-inner">
            {processingStatus === 'completed' ? (
              <CheckCircle2 className="w-8 h-8 text-emerald-600 animate-bounce" />
            ) : processingStatus === 'processing' || processingStatus === 'uploading' ? (
              <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
            ) : (
              <UploadCloud className="w-8 h-8" />
            )}
          </div>

          <h3 className="text-base font-semibold text-slate-800">
            {processingStatus === 'completed'
              ? 'Document Indexed Successfully!'
              : processingStatus === 'processing'
              ? 'Extracting text & generating ChromaDB embeddings...'
              : processingStatus === 'uploading'
              ? 'Uploading PDF...'
              : 'Drag & drop your PDF here'}
          </h3>

          <p className="mt-1 text-xs text-slate-500 max-w-sm">
            {!processingStatus && (
              <>
                or <span className="font-semibold text-brand-600 hover:underline">browse from device</span>.
                Supports academic papers and technical manuals (up to 25 MB).
              </>
            )}
            {selectedFile && !errorMessage && (
              <span className="block mt-1 font-mono text-slate-700">
                {selectedFile.name} ({formatBytes(selectedFile.size)})
              </span>
            )}
          </p>

          {/* Progress bar */}
          {(processingStatus === 'uploading' || processingStatus === 'processing') && (
            <div className="w-full max-w-xs mt-4">
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-brand-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <div className="flex justify-between items-center text-[11px] text-slate-500 mt-1.5 font-mono">
                <span>{processingStatus === 'processing' ? 'Processing pipeline' : 'Uploading'}</span>
                <span>{uploadProgress}%</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Error state */}
      {errorMessage && (
        <div className="flex items-center gap-2 p-3 mt-3 text-xs text-red-700 bg-red-50 border border-red-200 rounded-xl">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
}
