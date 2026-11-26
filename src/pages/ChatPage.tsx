import React, { useState, useEffect, useRef } from 'react';
import api from '../api/client';
import { Send, Plus, Trash2, MessageSquare, ShieldCheck, AlertTriangle, AlertCircle, Bookmark, FileText, ChevronDown, ChevronUp, Sparkles, HelpCircle } from 'lucide-react';
import { EvidenceModal, EvidenceDetail } from '../components/EvidenceModal';
import { ClaimVerificationBadge } from '../components/ClaimVerificationBadge';

interface CitationData {
  id: string;
  document_id: string;
  filename: string;
  page_number: number;
  chunk_id?: string | null;
  supporting_excerpt: string;
  claim_text: string;
  verification_status: string;
}

interface ClaimData {
  claim: string;
  status: string;
  evidence_excerpt?: string | null;
  citation_id?: string | null;
  reason?: string | null;
}

interface MessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  status: 'answered' | 'insufficient_evidence' | 'conflicting_evidence' | 'error' | string;
  reason?: string | null;
  citations: CitationData[];
  claims?: ClaimData[];
  created_at: string;
}

interface ConversationItem {
  id: string;
  title: string;
  created_at: string;
  message_count: number;
}

export const ChatPage: React.FC = () => {
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Evidence modal state
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceDetail | null>(null);
  
  // Expanded claim accordions
  const [expandedClaims, setExpandedClaims] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const loadConversations = async () => {
    try {
      const res = await api.get('/conversations');
      setConversations(res.data);
      if (!activeConversationId && res.data.length > 0) {
        loadConversation(res.data[0].id);
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  const loadConversation = async (convId: string) => {
    setActiveConversationId(convId);
    setError(null);
    try {
      const res = await api.get(`/conversations/${convId}`);
      setMessages(res.data.messages);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load conversation history.');
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  const handleNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
    setInputQuery('');
    setError(null);
  };

  const handleDeleteConversation = async (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation?')) return;
    try {
      await api.delete(`/conversations/${convId}`);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConversationId === convId) {
        handleNewChat();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete conversation.');
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || loading) return;

    const queryText = inputQuery.trim();
    setInputQuery('');
    setError(null);

    // Optimistically append user message
    const tempUserMsg: MessageItem = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: queryText,
      status: 'answered',
      citations: [],
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const res = await api.post('/chat/ask', {
        question: queryText,
        conversation_id: activeConversationId
      });

      const data = res.data;
      if (!activeConversationId) {
        setActiveConversationId(data.conversation_id);
        loadConversations();
      }

      const assistantMsg: MessageItem = {
        id: data.message_id,
        role: 'assistant',
        content: data.answer,
        status: data.status,
        reason: data.reason,
        citations: data.citations || [],
        claims: data.claims || [],
        created_at: new Date().toISOString()
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred during retrieval or generation.');
    } finally {
      setLoading(false);
    }
  };

  const toggleClaimExpansion = (msgId: string) => {
    setExpandedClaims((prev) => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
  };

  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden bg-slate-950">
      {/* Evidence Provenance Modal */}
      <EvidenceModal
        evidence={selectedEvidence}
        onClose={() => setSelectedEvidence(null)}
      />

      {/* Sidebar: Conversation History */}
      <div className="w-64 sm:w-72 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0">
        <div className="p-3 border-b border-slate-800">
          <button
            onClick={handleNewChat}
            className="w-full py-2 px-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>New Inquiry</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <div className="px-2 py-1 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
            Inquiry History
          </div>
          {conversations.length === 0 ? (
            <div className="px-3 py-6 text-center text-xs text-slate-500">
              No conversations yet
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = conv.id === activeConversationId;
              return (
                <div
                  key={conv.id}
                  onClick={() => loadConversation(conv.id)}
                  className={`group px-3 py-2.5 rounded-lg text-xs font-medium cursor-pointer transition-all flex items-center justify-between ${
                    isActive
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                      : 'text-slate-400 hover:bg-slate-800/70 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <MessageSquare className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                    <span className="truncate">{conv.title}</span>
                  </div>
                  <button
                    onClick={(e) => handleDeleteConversation(e, conv.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-400 transition-opacity"
                    title="Delete conversation"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Main Chat Thread */}
      <div className="flex-1 flex flex-col h-full bg-slate-950">
        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {error && (
            <div className="max-w-3xl mx-auto p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-300 flex items-center gap-3">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center p-8">
              <div className="max-w-md text-center space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-white tracking-tight">Ask GroundTruth.ai</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Query your uploaded documents with verifiable confidence. Every factual response is vetted against retrieved text chunks, with verified citations and honest abstention.
                </p>
                <div className="grid grid-cols-1 gap-2 pt-2 text-left">
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
                    💡 <span className="font-semibold text-slate-200">Try asking:</span> "What are the revenue figures in the Q3 report?"
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
                    💡 <span className="font-semibold text-slate-200">Abstention guarantee:</span> Questions absent from your files will be honestly declined.
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((msg) => {
                const isUser = msg.role === 'user';
                return (
                  <div key={msg.id} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
                    {/* Assistant Avatar */}
                    {!isUser && (
                      <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 flex items-center justify-center shrink-0 mt-1">
                        <ShieldCheck className="w-4 h-4" />
                      </div>
                    )}

                    <div className={`space-y-3 max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
                      {/* Message Bubble */}
                      <div
                        className={`p-4 rounded-2xl text-sm leading-relaxed ${
                          isUser
                            ? 'bg-indigo-600 text-white rounded-br-xs'
                            : msg.status === 'insufficient_evidence'
                            ? 'bg-slate-900 border border-amber-500/30 text-slate-200 rounded-bl-xs'
                            : msg.status === 'conflicting_evidence'
                            ? 'bg-slate-900 border border-rose-500/30 text-slate-200 rounded-bl-xs'
                            : 'bg-slate-900 border border-slate-800 text-slate-100 rounded-bl-xs'
                        }`}
                      >
                        {/* Status Header for Assistant */}
                        {!isUser && (
                          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-800/80">
                            {msg.status === 'answered' && (
                              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                                <ShieldCheck className="w-3.5 h-3.5" />
                                <span>Verified Evidence Grounded</span>
                              </span>
                            )}
                            {msg.status === 'insufficient_evidence' && (
                              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400">
                                <AlertCircle className="w-3.5 h-3.5" />
                                <span>Honest Abstention: Insufficient Evidence</span>
                              </span>
                            )}
                            {msg.status === 'conflicting_evidence' && (
                              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-400">
                                <AlertTriangle className="w-3.5 h-3.5" />
                                <span>Contradictory Evidence Detected</span>
                              </span>
                            )}
                          </div>
                        )}

                        <div className="whitespace-pre-wrap">{msg.content}</div>

                        {/* Abstention Reason Details */}
                        {msg.reason && (
                          <div className="mt-3 p-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-xs text-slate-400">
                            <span className="font-semibold text-slate-300">Grounding telemetry:</span> {msg.reason}
                          </div>
                        )}
                      </div>

                      {/* Verified Citation Chips */}
                      {!isUser && msg.citations && msg.citations.length > 0 && (
                        <div className="space-y-1.5">
                          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                            Supporting Document Sources
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {msg.citations.map((c, idx) => (
                              <button
                                key={c.id || idx}
                                onClick={() =>
                                  setSelectedEvidence({
                                    id: c.id,
                                    documentId: c.document_id,
                                    filename: c.filename,
                                    pageNumber: c.page_number,
                                    chunkId: c.chunk_id,
                                    supportingExcerpt: c.supporting_excerpt,
                                    claimText: c.claim_text,
                                    verificationStatus: c.verification_status
                                  })
                                }
                                className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700/80 hover:border-indigo-500 text-xs text-slate-300 flex items-center gap-2 group transition-all"
                              >
                                <Bookmark className="w-3 h-3 text-indigo-400" />
                                <span className="font-medium text-slate-200 group-hover:text-indigo-300">
                                  {c.filename} (p. {c.page_number})
                                </span>
                                <ClaimVerificationBadge status={c.verification_status} size="sm" />
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Claims Entailment Accordion */}
                      {!isUser && msg.claims && msg.claims.length > 0 && (
                        <div className="w-full">
                          <button
                            onClick={() => toggleClaimExpansion(msg.id)}
                            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1.5 transition-colors"
                          >
                            <span>
                              {expandedClaims[msg.id] ? 'Hide' : 'Inspect'} claim-by-claim verification breakdown ({msg.claims.length} claims)
                            </span>
                            {expandedClaims[msg.id] ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>

                          {expandedClaims[msg.id] && (
                            <div className="mt-2 p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-2 text-xs">
                              {msg.claims.map((cl, cIdx) => (
                                <div key={cIdx} className="p-2.5 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1.5">
                                  <div className="flex items-start justify-between gap-2">
                                    <span className="text-slate-200 font-medium">"{cl.claim}"</span>
                                    <ClaimVerificationBadge status={cl.status} />
                                  </div>
                                  {cl.reason && (
                                    <div className="text-[11px] text-slate-400">
                                      {cl.reason}
                                    </div>
                                  )}
                                  {cl.evidence_excerpt && (
                                    <div className="text-[10px] text-slate-500 font-mono bg-slate-900 p-2 rounded border border-slate-800">
                                      Passage excerpt: {cl.evidence_excerpt}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Loading Indicator */}
              {loading && (
                <div className="flex gap-3 justify-start">
                  <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 flex items-center justify-center shrink-0">
                    <ShieldCheck className="w-4 h-4 animate-pulse" />
                  </div>
                  <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl rounded-bl-xs text-xs text-slate-300 flex items-center gap-3">
                    <div className="flex space-x-1.5">
                      <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                      <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                      <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                    </div>
                    <span>Retrieving authorized passages, generating answer, and verifying claims...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Query Input Box */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60">
          <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto flex gap-2">
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask a question about your indexed documents..."
              disabled={loading}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            />
            <button
              type="submit"
              disabled={loading || !inputQuery.trim()}
              className="px-5 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl font-medium text-sm flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all"
            >
              <Send className="w-4 h-4" />
              <span className="hidden sm:inline">Ask</span>
            </button>
          </form>
          <div className="text-[11px] text-center text-slate-500 mt-2">
            GroundTruth.ai will strictly abstain if sufficient evidence cannot be established from your documents.
          </div>
        </div>
      </div>
    </div>
  );
};
