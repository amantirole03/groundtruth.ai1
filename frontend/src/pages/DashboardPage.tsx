import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { FileText, CheckCircle2, MessageSquare, AlertCircle, ArrowUpRight, BarChart3, Plus, RefreshCw, ShieldAlert, Sparkles } from 'lucide-react';

interface StatsData {
  total_documents: number;
  indexed_documents: number;
  questions_answered: number;
  questions_abstained: number;
  recent_activity: Array<{
    id: string;
    conversation_title: string;
    status: string;
    content_preview: string;
    created_at: string;
  }>;
  processing_statuses: Record<string, number>;
}

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/stats');
      setStats(res.data);
    } catch (err: any) {
      if (err.response?.status === 405 || !err.response) {
        setStats({
          total_documents: 0,
          indexed_documents: 0,
          questions_answered: 0,
          questions_abstained: 0,
          recent_activity: [],
          processing_statuses: { completed: 0, processing: 0, failed: 0 }
        });
        return;
      }
      setError(err.response?.data?.detail || 'Failed to load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">System Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time evidence telemetry and document index metrics
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchStats}
            disabled={loading}
            className="p-2 text-slate-400 hover:text-white bg-slate-900 border border-slate-800 rounded-lg transition-colors flex items-center gap-2 text-xs font-medium"
            title="Refresh Metrics"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
            <span className="hidden sm:inline">Refresh Data</span>
          </button>
          <Link
            to="/documents"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Upload Document</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Primary KPI Cards - Real Database Metrics Only */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Documents */}
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Total Documents</span>
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-white">
            {stats ? stats.total_documents : 0}
          </div>
          <div className="text-[11px] text-slate-400">
            Uploaded to private tenant storage
          </div>
        </div>

        {/* Successfully Indexed */}
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Indexed Documents</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-emerald-400">
            {stats ? stats.indexed_documents : 0}
          </div>
          <div className="text-[11px] text-slate-400">
            Active in pgvector vector space
          </div>
        </div>

        {/* Questions Answered */}
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Questions Answered</span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
              <MessageSquare className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-blue-400">
            {stats ? stats.questions_answered : 0}
          </div>
          <div className="text-[11px] text-slate-400">
            With verified evidence support
          </div>
        </div>

        {/* Questions Abstained */}
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Honest Abstentions</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-amber-400">
            {stats ? stats.questions_abstained : 0}
          </div>
          <div className="text-[11px] text-slate-400">
            Unsubstantiated or conflicting queries
          </div>
        </div>
      </div>

      {/* Main Row: Recent Activity & Processing Statuses */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity List */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white">Recent Activity & Query Outcomes</h2>
            <Link to="/chat" className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1">
              <span>Open Chat</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {!stats || stats.recent_activity.length === 0 ? (
            <div className="p-8 text-center border border-dashed border-slate-800 rounded-lg space-y-2">
              <MessageSquare className="w-8 h-8 text-slate-600 mx-auto" />
              <p className="text-sm font-medium text-slate-400">No questions asked yet.</p>
              <p className="text-xs text-slate-500">Ask questions in the Chat Workspace to see evidence telemetry.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {stats.recent_activity.map((act) => (
                <div key={act.id} className="py-3 flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="text-xs font-medium text-slate-300">
                      {act.conversation_title}
                    </div>
                    <div className="text-xs text-slate-400 line-clamp-1 italic">
                      "{act.content_preview}"
                    </div>
                  </div>
                  <div className="shrink-0">
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                      act.status === 'answered'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        : act.status === 'conflicting_evidence'
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                    }`}>
                      {act.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Processing Status Breakdown & Quick Links */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h2 className="text-base font-semibold text-white">Index Processing Status</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  Completed (Indexed)
                </span>
                <span className="font-mono text-slate-200">
                  {stats?.processing_statuses?.completed || 0}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-400" />
                  Processing / Chunking
                </span>
                <span className="font-mono text-slate-200">
                  {stats?.processing_statuses?.processing || 0}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-rose-400" />
                  Failed / Corrupted
                </span>
                <span className="font-mono text-slate-200">
                  {stats?.processing_statuses?.failed || 0}
                </span>
              </div>
            </div>
          </div>

          {/* Quick System Actions */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Quick Actions</h2>
            <div className="space-y-2">
              <Link
                to="/evaluation"
                className="p-3 rounded-lg bg-slate-950 border border-slate-800 hover:border-indigo-500/30 transition-all flex items-center justify-between group"
              >
                <div className="flex items-center gap-3">
                  <BarChart3 className="w-4 h-4 text-indigo-400" />
                  <div className="text-xs font-medium text-slate-200 group-hover:text-white">Run Benchmark Suite</div>
                </div>
                <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400" />
              </Link>

              <Link
                to="/documents"
                className="p-3 rounded-lg bg-slate-950 border border-slate-800 hover:border-indigo-500/30 transition-all flex items-center justify-between group"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-blue-400" />
                  <div className="text-xs font-medium text-slate-200 group-hover:text-white">Manage Files</div>
                </div>
                <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-blue-400" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
