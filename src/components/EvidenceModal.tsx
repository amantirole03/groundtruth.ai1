import React from 'react';
import { X, FileText, CheckCircle2, Bookmark, ShieldCheck } from 'lucide-react';
import { ClaimVerificationBadge } from './ClaimVerificationBadge';

export interface EvidenceDetail {
  id?: string;
  documentId: string;
  filename: string;
  pageNumber: number;
  chunkId?: string | null;
  supportingExcerpt: string;
  claimText: string;
  verificationStatus: string;
}

interface Props {
  evidence: EvidenceDetail | null;
  onClose: () => void;
}

export const EvidenceModal: React.FC<Props> = ({ evidence, onClose }) => {
  if (!evidence) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div 
        className="relative w-full max-w-2xl bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-white text-base">Verified Evidence Source</h3>
              <p className="text-xs text-slate-400">Provenance and entailment ground truth</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5 overflow-y-auto">
          {/* Metadata Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-800/60 p-3.5 rounded-lg border border-slate-700/50 text-xs">
            <div>
              <div className="text-slate-400 font-medium mb-1">Source File</div>
              <div className="font-mono text-slate-200 truncate flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                <span title={evidence.filename}>{evidence.filename}</span>
              </div>
            </div>
            <div>
              <div className="text-slate-400 font-medium mb-1">Page Number</div>
              <div className="font-mono text-slate-200 flex items-center gap-1.5">
                <Bookmark className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                <span>Page {evidence.pageNumber}</span>
              </div>
            </div>
            <div>
              <div className="text-slate-400 font-medium mb-1">Entailment Status</div>
              <div>
                <ClaimVerificationBadge status={evidence.verificationStatus} />
              </div>
            </div>
          </div>

          {/* Factual Claim */}
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Answer Claim Being Verified
            </div>
            <div className="p-3 bg-slate-950/60 border border-indigo-500/20 rounded-lg text-sm text-indigo-200 font-medium leading-relaxed">
              "{evidence.claimText}"
            </div>
          </div>

          {/* Raw Supporting Excerpt */}
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Original Document Excerpt</span>
              {evidence.chunkId && (
                <span className="text-[10px] text-slate-500 font-mono">
                  Chunk: {evidence.chunkId.slice(0, 8)}...
                </span>
              )}
            </div>
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed selection:bg-indigo-600/50">
              {evidence.supportingExcerpt}
            </div>
          </div>

          {/* Assurance Disclaimer */}
          <div className="text-[11px] text-slate-500 italic bg-slate-900/50 p-2.5 rounded border border-slate-800">
            Note: GroundTruth.ai enforces server-side validation against indexed document chunks. Automated verification is probabilistic and not a mathematical guarantee.
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors"
          >
            Close Source View
          </button>
        </div>
      </div>
    </div>
  );
};
