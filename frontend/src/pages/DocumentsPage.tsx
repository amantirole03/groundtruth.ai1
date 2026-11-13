import React, { useState, useEffect, useRef } from 'react';
import api from '../api/client';
import { UploadCloud, FileText, Trash2, CheckCircle2, AlertTriangle, Clock, RefreshCw, AlertCircle, FileCheck, Info } from 'lucide-react';

interface DocumentItem {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | string;
  page_count: number;
  chunk_count: number;
  error_message?: string | null;
  created_at: string;
}

export const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    try {
      const res = await api.get('/documents');
      setDocuments(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load documents.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx', 'txt'].includes(extension || '')) {
      setError("Unsupported file format. Please upload PDF, DOCX, or TXT documents.");
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      setError("File exceeds 20MB limit.");
      return;
    }

    setError(null);
    setSuccess(null);
    setUploading(true);
    setUploadProgress(`Uploading and indexing ${file.name}...`);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (res.data.status === 'failed') {
        setError(`Processing failed: ${res.data.error_message || 'Could not parse document'}`);
      } else {
        setSuccess(`Successfully indexed ${res.data.filename} (${res.data.chunk_count} vector chunks generated).`);
      }
      fetchDocuments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload document.');
    } finally {
      setUploading(false);
      setUploadProgress(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id: string, filename: string) => {
    if (!window.confirm(`Are you sure you want to delete ${filename}? All chunks and vector indexes will be removed.`)) {
      return;
    }

    try {
      await api.delete(`/documents/${id}`);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
      setSuccess(`Deleted ${filename}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete document.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Documents & Evidence Store</h1>
          <p className="text-sm text-slate-400 mt-1">
            Upload and manage the knowledge base for evidence-grounded queries
          </p>
        </div>
        <button
          onClick={fetchDocuments}
          className="p-2 text-slate-400 hover:text-white bg-slate-900 border border-slate-800 rounded-lg text-xs font-medium flex items-center gap-2 self-start"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 text-sm flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-xs text-rose-400 hover:underline">Dismiss</button>
        </div>
      )}

      {success && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-300 text-sm flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <span>{success}</span>
          </div>
          <button onClick={() => setSuccess(null)} className="text-xs text-emerald-400 hover:underline">Dismiss</button>
        </div>
      )}

      {/* Upload Dropzone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handleFileUpload(e.dataTransfer.files);
        }}
        className="p-8 border-2 border-dashed border-slate-700 hover:border-indigo-500/50 rounded-2xl bg-slate-900/40 hover:bg-slate-900/80 transition-all text-center cursor-pointer space-y-3 group"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(e) => handleFileUpload(e.target.files)}
        />
        <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 mx-auto flex items-center justify-center group-hover:scale-110 transition-transform">
          <UploadCloud className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">
            {uploading ? uploadProgress : 'Click or drag documents here to upload'}
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Supports PDF, DOCX, and TXT files up to 20MB. Automatically chunked (~600 tokens) with page provenance.
          </p>
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-base font-semibold text-white">Indexed Documents ({documents.length})</h2>
          <span className="text-xs text-slate-400">Strict per-user boundary enforced</span>
        </div>

        {documents.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <FileText className="w-10 h-10 text-slate-600 mx-auto" />
            <div className="text-slate-300 font-medium text-sm">No documents uploaded yet</div>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Upload your PDF reports, policies, or technical documentation to enable evidence-grounded Q&A.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800 uppercase font-medium tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Filename</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Pages</th>
                  <th className="px-6 py-3.5">Vector Chunks</th>
                  <th className="px-6 py-3.5">Uploaded</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4 font-medium text-white flex items-center gap-2.5">
                      <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                      <span className="truncate max-w-[220px]" title={doc.filename}>{doc.filename}</span>
                    </td>
                    <td className="px-6 py-4">
                      {doc.status === 'completed' && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Indexed</span>
                        </span>
                      )}
                      {doc.status === 'processing' && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                          <Clock className="w-3 h-3 animate-spin" />
                          <span>Processing</span>
                        </span>
                      )}
                      {doc.status === 'failed' && (
                        <span 
                          className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20 cursor-help"
                          title={doc.error_message || 'Processing error'}
                        >
                          <AlertTriangle className="w-3 h-3" />
                          <span>Failed</span>
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 font-mono">{doc.page_count}</td>
                    <td className="px-6 py-4 font-mono">{doc.chunk_count}</td>
                    <td className="px-6 py-4 text-slate-400">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded transition-colors"
                        title="Delete document and vector chunks"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
