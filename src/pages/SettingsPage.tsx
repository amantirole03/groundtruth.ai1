import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { Settings as SettingsIcon, Cpu, Sliders, Shield, Key, CheckCircle2, Lock, Terminal } from 'lucide-react';

interface HealthData {
  status: string;
  service: string;
  tagline: string;
  llm_provider: string;
  embedding_provider: string;
  retrieval_threshold: number;
  chunk_size: number;
  chunk_overlap: number;
}

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/health')
      .then((res) => setHealth(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="border-b border-slate-800 pb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">System & AI Configuration</h1>
        <p className="text-sm text-slate-400 mt-1">
          Review provider bindings, vector embedding dimensions, and retrieval threshold settings
        </p>
      </div>

      {/* Active Providers Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Active AI Engine Architecture</h2>
            <p className="text-xs text-slate-400">Pluggable provider abstraction layer</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="text-xs text-slate-400 font-medium">LLM Answer Generator</div>
            <div className="text-base font-bold text-white flex items-center gap-2">
              <span className="uppercase">{health?.llm_provider || 'Mock Engine'}</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Active
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Responsible for synthesizing candidate answers conditioned strictly on retrieved evidence.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="text-xs text-slate-400 font-medium">Vector Embedding Model</div>
            <div className="text-base font-bold text-white flex items-center gap-2">
              <span className="uppercase">{health?.embedding_provider || 'Mock Feature Hash'}</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                1536 Dimensions
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Generates normalized dense vectors stored in PostgreSQL with pgvector cosine distance.
            </p>
          </div>
        </div>
      </div>

      {/* RAG & Verification Hyperparameters */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">RAG Ingestion & Verification Hyperparameters</h2>
            <p className="text-xs text-slate-400">Thresholds governing evidence sufficiency and chunk granularity</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <div className="text-slate-400 font-medium">Chunk Target Size</div>
            <div className="text-lg font-bold text-white font-mono">
              {health?.chunk_size || 600} tokens
            </div>
            <div className="text-slate-500 text-[11px]">~2,400 characters per passage</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <div className="text-slate-400 font-medium">Chunk Overlap</div>
            <div className="text-lg font-bold text-white font-mono">
              {health?.chunk_overlap || 100} tokens
            </div>
            <div className="text-slate-500 text-[11px]">Preserves contextual boundaries</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <div className="text-slate-400 font-medium">Retrieval Cosine Threshold</div>
            <div className="text-lg font-bold text-indigo-400 font-mono">
              {health?.retrieval_threshold || 0.45}
            </div>
            <div className="text-slate-500 text-[11px]">Scores below this trigger honest abstention</div>
          </div>
        </div>
      </div>

      {/* Security Architecture & Provider Switching Guide */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Security & API Key Management</h2>
            <p className="text-xs text-slate-400">Zero frontend credential exposure guarantee</p>
          </div>
        </div>

        <div className="text-xs text-slate-300 leading-relaxed space-y-3">
          <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg flex items-start gap-3">
            <Lock className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-white">Backend Isolation:</span> API keys for OpenAI, Gemini, or Anthropic are exclusively configured through server-side environment variables (`.env`). No API keys or private document chunks are ever exposed in client-side bundles.
            </div>
          </div>

          <div className="space-y-2">
            <div className="font-semibold text-slate-200">How to configure external providers:</div>
            <p className="text-slate-400">
              To connect OpenAI, Gemini, or Claude, set the following environment variables in <code className="text-indigo-300 bg-slate-950 px-1 py-0.5 rounded">.env</code>:
            </p>
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg font-mono text-[11px] text-slate-300 space-y-1">
              <div>LLM_PROVIDER=openai</div>
              <div>OPENAI_API_KEY=sk-...</div>
              <div>OPENAI_MODEL=gpt-4o-mini</div>
              <div>EMBEDDING_PROVIDER=openai</div>
              <div>EMBEDDING_MODEL=text-embedding-3-small</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
