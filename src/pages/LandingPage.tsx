import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, FileCheck, CheckCircle2, AlertCircle, Search, Sparkles, ArrowRight, Lock } from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Hero Section */}
      <div className="relative overflow-hidden pt-16 pb-20 lg:pt-24 lg:pb-32">
        {/* Subtle background glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-indigo-600/15 blur-[120px] rounded-full pointer-events-none" />

        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold uppercase tracking-wider">
              <ShieldCheck className="w-3.5 h-3.5" />
              Evidence-Grounded RAG Platform
            </div>

            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
              Answers you can <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-blue-400">verify.</span>
            </h1>

            <p className="text-lg sm:text-xl text-slate-300 font-normal leading-relaxed">
              Upload documents, ask complex questions, and get precise answers with claim-by-claim factual evidence verification. When sufficient evidence cannot be established, we honestly abstain.
            </p>

            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/register"
                className="w-full sm:w-auto px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 transition-all hover:gap-3"
              >
                <span>Start Free Workspace</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-auto px-6 py-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium text-sm transition-colors text-center"
              >
                Sign In to Account
              </Link>
            </div>
          </div>

          {/* Core Principle Callout */}
          <div className="mt-16 max-w-3xl mx-auto p-6 rounded-2xl bg-slate-900/90 border border-indigo-500/30 shadow-2xl relative">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shrink-0">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-indigo-300 uppercase tracking-wider">
                  Our Founding Principle
                </h3>
                <blockquote className="text-base sm:text-lg font-medium text-white italic leading-relaxed">
                  "Every factual answer must be supported by evidence from the uploaded documents. If sufficient evidence cannot be established, the system must say that it does not know."
                </blockquote>
                <p className="text-xs text-slate-400 pt-1">
                  We never pretend to be magically hallucination-free. We verify citations server-side, check natural language entailment, and surface unresolved claims transparently.
                </p>
              </div>
            </div>
          </div>

          {/* Interactive Feature Grid */}
          <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/30 transition-all space-y-3">
              <div className="w-10 h-10 rounded-lg bg-indigo-600/10 text-indigo-400 flex items-center justify-center">
                <Search className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-semibold text-white">Strict Tenant Retrieval</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Passages are indexed with pgvector and cosine distance. Retrieval thresholds strictly guarantee that questions without relevant passages trigger honest abstention.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/30 transition-all space-y-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-600/10 text-emerald-400 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-semibold text-white">Claim-by-Claim Verification</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Generated answers are decomposed into testable atomic claims. Each claim is verified against indexed passages with Supported, Contradicted, or Uncertain tags.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/30 transition-all space-y-3">
              <div className="w-10 h-10 rounded-lg bg-rose-600/10 text-rose-400 flex items-center justify-center">
                <AlertCircle className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-semibold text-white">Explicit Abstention</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                If evidence is missing or contradictory, the system abstains rather than inventing answers from generic web memory or ungrounded model weights.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
