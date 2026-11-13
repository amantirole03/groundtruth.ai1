import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { BarChart3, Play, CheckCircle2, AlertTriangle, Clock, ShieldCheck, DollarSign, HelpCircle, RefreshCw, AlertCircle } from 'lucide-react';

interface MetricsData {
  total_cases: number;
  retrieval_recall_at_k: number;
  citation_support_rate: number;
  answer_correctness_rate: number;
  correct_abstention_rate: number;
  false_abstention_rate: number;
  mean_latency_ms: number;
  estimated_cost_usd: number;
}

interface EvaluationItem {
  id: string;
  category: string;
  question: string;
  expected_status: string;
  actual_status: string;
  status_match: boolean;
  actual_answer: string;
  latency_ms: number;
  metrics: Record<string, any>;
}

export const EvaluationPage: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [evaluations, setEvaluations] = useState<EvaluationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningBenchmark, setRunningBenchmark] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const fetchEvaluationSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/evaluation/summary');
      if (res.data.latest_metrics) {
        setMetrics(res.data.latest_metrics);
      }
      setEvaluations(res.data.recent_evaluations || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load evaluation telemetry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvaluationSummary();
  }, []);

  const handleRunBenchmark = async () => {
    setRunningBenchmark(true);
    setError(null);
    setStatusMessage('Executing benchmark suite across direct queries, paraphrases, absent topics, prompt injections, and cross-user boundaries...');
    try {
      const res = await api.post('/evaluation/run', { sample_size: 8 });
      setMetrics(res.data.latest_metrics);
      setEvaluations(res.data.recent_evaluations || []);
      setStatusMessage('Benchmark run completed successfully. Real test metrics updated below.');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Benchmark execution failed.');
    } finally {
      setRunningBenchmark(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">System Evaluation & Benchmarks</h1>
          <p className="text-sm text-slate-400 mt-1">
            Empirical measurements of retrieval fidelity, claim entailment, and honest abstention accuracy
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRunBenchmark}
            disabled={runningBenchmark}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all"
          >
            <Play className={`w-3.5 h-3.5 ${runningBenchmark ? 'animate-spin' : ''}`} />
            <span>{runningBenchmark ? 'Running Benchmark...' : 'Run Benchmark Suite'}</span>
          </button>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-xs text-indigo-300 flex items-center gap-2.5">
          <ShieldCheck className="w-4 h-4 shrink-0 text-indigo-400" />
          <span>{statusMessage}</span>
        </div>
      )}

      {error && (
        <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-300 flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Retrieval Recall@k */}
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Retrieval Recall@k</span>
            <span title="Percentage of answerable test queries where ground truth chunks were retrieved.">
              <HelpCircle className="w-4 h-4 text-slate-500 cursor-help" />
            </span>
          </div>
          <div className="text-3xl font-bold text-white font-mono">
            {metrics ? `${(metrics.retrieval_recall_at_k * 100).toFixed(1)}%` : '--'}
          </div>
          <p className="text-[11px] text-slate-500">Threshold-gated passage recall</p>
        </div>

        {/* Citation Support Rate */}
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Citation Support Rate</span>
            <span title="Proportion of citations verified as strictly supported by retrieved chunks.">
              <HelpCircle className="w-4 h-4 text-slate-500 cursor-help" />
            </span>
          </div>
          <div className="text-3xl font-bold text-emerald-400 font-mono">
            {metrics ? `${(metrics.citation_support_rate * 100).toFixed(1)}%` : '--'}
          </div>
          <p className="text-[11px] text-slate-500">Verified server-side entailment</p>
        </div>

        {/* Correct Abstention Rate */}
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Correct Abstention</span>
            <span title="Accuracy in declining queries when evidence is absent, conflicting, or off-topic.">
              <HelpCircle className="w-4 h-4 text-slate-500 cursor-help" />
            </span>
          </div>
          <div className="text-3xl font-bold text-blue-400 font-mono">
            {metrics ? `${(metrics.correct_abstention_rate * 100).toFixed(1)}%` : '--'}
          </div>
          <p className="text-[11px] text-slate-500">Honest refusal on absent docs</p>
        </div>

        {/* False Abstention Rate */}
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">False Abstention</span>
            <span title="Rate at which answerable questions were incorrectly declined.">
              <HelpCircle className="w-4 h-4 text-slate-500 cursor-help" />
            </span>
          </div>
          <div className="text-3xl font-bold text-amber-400 font-mono">
            {metrics ? `${(metrics.false_abstention_rate * 100).toFixed(1)}%` : '--'}
          </div>
          <p className="text-[11px] text-slate-500">Over-conservative refusal rate</p>
        </div>
      </div>

      {/* Latency & Cost Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
              <Clock className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs text-slate-400">Mean Pipeline Latency</div>
              <div className="text-lg font-bold text-white font-mono">
                {metrics ? `${metrics.mean_latency_ms.toFixed(1)} ms` : '--'}
              </div>
            </div>
          </div>
          <span className="text-[11px] text-slate-500">Embed + Retrieve + Verify</span>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <DollarSign className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs text-slate-400">Provider Usage / Cost</div>
              <div className="text-lg font-bold text-white font-mono">
                {metrics ? `$${metrics.estimated_cost_usd.toFixed(4)}` : '$0.0000'}
              </div>
            </div>
          </div>
          <span className="text-[11px] text-slate-500">Direct provider billing</span>
        </div>
      </div>

      {/* Benchmark Test Cases Breakdown */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">Synthetic Test Suite Execution Records</h2>
            <p className="text-xs text-slate-400">Actual test runs evaluating prompt injection defense, cross-user isolation, and paraphrase matching</p>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {evaluations.length} test records
          </span>
        </div>

        {evaluations.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <BarChart3 className="w-10 h-10 text-slate-600 mx-auto" />
            <div className="text-sm font-medium text-slate-300">No benchmark executions recorded</div>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Click "Run Benchmark Suite" to run the labeled test cases through the real RAG pipeline.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800 uppercase font-medium tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Category</th>
                  <th className="px-6 py-3.5">Test Question</th>
                  <th className="px-6 py-3.5">Expected Status</th>
                  <th className="px-6 py-3.5">Actual Status</th>
                  <th className="px-6 py-3.5">Verdict</th>
                  <th className="px-6 py-3.5">Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {evaluations.map((ev, idx) => (
                  <tr key={ev.id || idx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4 font-mono text-slate-400">
                      <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700/50 text-[10px]">
                        {ev.category}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-medium text-white max-w-xs truncate" title={ev.question}>
                      {ev.question}
                    </td>
                    <td className="px-6 py-4 font-mono text-slate-400">{ev.expected_status}</td>
                    <td className="px-6 py-4 font-mono text-slate-200">{ev.actual_status}</td>
                    <td className="px-6 py-4">
                      {ev.status_match ? (
                        <span className="inline-flex items-center gap-1 font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full text-[10px]">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>PASS</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full text-[10px]">
                          <AlertTriangle className="w-3 h-3" />
                          <span>FAIL</span>
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 font-mono text-slate-400">
                      {ev.latency_ms.toFixed(1)} ms
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Explanatory Methodology Card */}
      <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
        <h3 className="text-sm font-semibold text-white">Evaluation Methodology & Metric Formulas</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-400">
          <div>
            <span className="font-semibold text-slate-300">Citation Support Rate:</span> Calculated as the fraction of generated citations where server-side entailment verification determined the claim is strictly supported by the cited passage.
          </div>
          <div>
            <span className="font-semibold text-slate-300">Honest Abstention Rate:</span> Ratio of unanswerable or absent-document queries that correctly returned `insufficient_evidence` or `conflicting_evidence` rather than hallucinating.
          </div>
          <div>
            <span className="font-semibold text-slate-300">Prompt Injection Defense:</span> Evaluates resilience when documents contain prompt overrides (e.g. "IGNORE PREVIOUS INSTRUCTIONS"). The system treats all document text as untrusted data.
          </div>
          <div>
            <span className="font-semibold text-slate-300">Cross-Tenant Isolation:</span> Ensures vector searches enforce SQL `owner_id == current_user.id` so private documents of User B cannot leak to User A.
          </div>
        </div>
      </div>
    </div>
  );
};
