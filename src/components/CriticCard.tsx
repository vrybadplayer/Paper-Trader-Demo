import React, { useState } from 'react';
import { RiskAudit, TradeSignal, PostMortemAutopsy } from '../types';
import { CRITIC_PERSONA, SAMPLE_CHROMA_MEMORIES } from '../data/personaData';
import { ShieldCheck, ShieldAlert, Sparkles, AlertTriangle, CheckCircle2, XCircle, Database, ChevronDown, ChevronUp, History, BrainCircuit, Activity } from 'lucide-react';

interface CriticCardProps {
  latestAudit: RiskAudit | null;
  pendingSignal: TradeSignal | null;
  isValidating: boolean;
  historicalPnlSummary: string;
  autopsies: PostMortemAutopsy[];
  onTriggerSimulatedAutopsy: () => void;
  reserveLimit?: number;
  maxPosPct?: number;
}

export const CriticCard: React.FC<CriticCardProps> = ({
  latestAudit,
  pendingSignal,
  isValidating,
  historicalPnlSummary,
  autopsies,
  onTriggerSimulatedAutopsy,
  reserveLimit = 50000,
  maxPosPct = 10,
}) => {
  const [showThinking, setShowThinking] = useState(true);
  const [showMemory, setShowMemory] = useState(false);
  const [activeSubTab, setActiveSubTab] = useState<'audit' | 'autopsies'>('audit');

  const latestAutopsy = autopsies.length > 0 ? autopsies[0] : null;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden flex flex-col h-full shadow-md">
      {/* Card Header */}
      <div className="bg-slate-800/80 border-b border-slate-700/80 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-sm text-slate-100">{CRITIC_PERSONA.name}</h3>
              <span className="text-[11px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 font-mono font-bold">
                {CRITIC_PERSONA.model}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">System 2: Deep Risk Auditor &amp; ChromaDB Autopsy Engine</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowMemory(!showMemory)}
            className={`p-1.5 rounded-lg border text-xs font-mono transition flex items-center gap-1 cursor-pointer ${
              showMemory
                ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300'
                : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
            title="ChromaDB RAG Memory"
          >
            <Database className="w-3.5 h-3.5" />
            <span className="text-[10px]">ChromaDB ({autopsies.length})</span>
          </button>
        </div>
      </div>

      <div className="p-4 flex-1 flex flex-col gap-3.5">
        {/* ChromaDB Memory Dropdown */}
        {showMemory && (
          <div className="bg-slate-950 border border-indigo-900/50 rounded-lg p-3 text-xs space-y-2">
            <div className="flex items-center justify-between text-indigo-400 font-semibold text-[11px]">
              <span className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5" /> ChromaDB Dynamic Post-Mortem &amp; Behavioral Store
              </span>
              <span className="text-[10px] text-slate-500 font-mono">HNSW Vector Space</span>
            </div>
            <div className="space-y-1.5 max-h-44 overflow-y-auto">
              {autopsies.map((a) => (
                <div key={a.id} className="bg-slate-900/90 p-2 rounded border border-rose-900/40 text-[11px]">
                  <div className="flex items-center justify-between text-rose-300 font-semibold">
                    <span className="flex items-center gap-1 font-mono">
                      <ShieldAlert className="w-3 h-3 text-rose-400" />
                      {a.ticker} Failure Autopsy (-${a.lossAmount.toFixed(2)})
                    </span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-rose-950 text-rose-300 border border-rose-800 font-mono">
                      {a.failureTag}
                    </span>
                  </div>
                  <div className="text-slate-300 text-[10px] mt-1 font-medium">{a.rootCause}</div>
                  <div className="text-emerald-400/90 text-[10px] mt-0.5 italic">Guardrail: {a.guardrailRule}</div>
                </div>
              ))}
              {SAMPLE_CHROMA_MEMORIES.map((m, i) => (
                <div key={i} className="bg-slate-900/80 p-2 rounded border border-slate-800 text-[11px]">
                  <div className="text-indigo-300 font-semibold">{m.topic}</div>
                  <div className="text-slate-400 text-[10px] mt-0.5 leading-relaxed">{m.content}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Sub Navigation: Live Pre-Trade Audit vs Post-Mortem Autopsies */}
        <div className="flex bg-slate-950/80 p-1 rounded-lg border border-slate-800 text-xs">
          <button
            onClick={() => setActiveSubTab('audit')}
            className={`flex-1 py-1.5 px-2 rounded-md font-semibold transition flex items-center justify-center gap-1.5 cursor-pointer ${
              activeSubTab === 'audit'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            Live Pre-Trade Audit
          </button>
          <button
            onClick={() => setActiveSubTab('autopsies')}
            className={`flex-1 py-1.5 px-2 rounded-md font-semibold transition flex items-center justify-center gap-1.5 cursor-pointer ${
              activeSubTab === 'autopsies'
                ? 'bg-rose-600/80 text-white shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BrainCircuit className="w-3.5 h-3.5" />
            Post-Mortem Autopsies ({autopsies.length})
          </button>
        </div>

        {/* Tab 1: Live Pre-Trade Audit */}
        {activeSubTab === 'audit' && (
          <div className="flex-1 flex flex-col justify-between gap-3">
            {/* Invariant Status Check Bar */}
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2.5">
              <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Hard Risk Invariants Enforced
              </div>
              <div className="grid grid-cols-2 gap-1.5 text-[10px]">
                <div className="flex items-center gap-1.5 bg-slate-900/80 p-1.5 rounded border border-slate-800 text-slate-300">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                  <span>Reserve: &ge; ${reserveLimit >= 1000 ? `${(reserveLimit / 1000).toFixed(0)}k` : reserveLimit.toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-1.5 bg-slate-900/80 p-1.5 rounded border border-slate-800 text-slate-300">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                  <span>Max Pos: &le; {maxPosPct}%</span>
                </div>
                <div className="flex items-center gap-1.5 bg-slate-900/80 p-1.5 rounded border border-slate-800 text-slate-300">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                  <span>Shark Delta Proof</span>
                </div>
                <div className="flex items-center gap-1.5 bg-slate-900/80 p-1.5 rounded border border-slate-800 text-slate-300">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                  <span>Chroma Loss Guard</span>
                </div>
              </div>
            </div>

            {/* Dynamic State View */}
            {isValidating ? (
              <div className="bg-indigo-950/20 border border-indigo-800/40 rounded-lg p-4 flex flex-col items-center justify-center text-center gap-2 py-6">
                <ShieldCheck className="w-6 h-6 text-indigo-400 animate-bounce" />
                <p className="text-xs font-semibold text-indigo-300">
                  Morgan running DeepSeek-R1 Chain-of-Thought risk audit...
                </p>
                <p className="text-[11px] text-slate-400 font-mono">
                  Cross-checking ChromaDB loss autopsies &amp; available capital...
                </p>
              </div>
            ) : latestAudit ? (
              <div className="space-y-2.5">
                {/* Verdict header banner */}
                <div
                  className={`p-2.5 rounded-lg border flex items-center justify-between ${
                    latestAudit.approved
                      ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-300'
                      : 'bg-rose-950/30 border-rose-800/60 text-rose-300'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {latestAudit.approved ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400" />
                    )}
                    <div>
                      <div className="text-xs font-bold font-mono">
                        VERDICT: {latestAudit.approved ? 'APPROVED' : 'REJECTED BY RISK ENGINE'}
                      </div>
                      <div className="text-[10px] opacity-80">
                        Target: {latestAudit.ticker} ({latestAudit.action})
                      </div>
                    </div>
                  </div>

                  <div className="text-right font-mono text-xs">
                    {latestAudit.approved ? (
                      <span className="text-emerald-400 font-bold">
                        Qty: {latestAudit.adjustedQuantity} shares
                      </span>
                    ) : (
                      <span className="text-rose-400 font-bold">Qty: 0</span>
                    )}
                  </div>
                </div>

                {/* Violations if rejected */}
                {!latestAudit.approved && latestAudit.violations.length > 0 && (
                  <div className="bg-rose-950/40 border border-rose-900 p-2.5 rounded-lg text-xs space-y-1">
                    <div className="text-rose-400 font-semibold flex items-center gap-1.5 text-[11px]">
                      <AlertTriangle className="w-3.5 h-3.5" /> Identified Invariant Violations:
                    </div>
                    <ul className="list-disc list-inside text-[11px] text-rose-300/90 pl-1 font-mono">
                      {latestAudit.violations.map((v, i) => (
                        <li key={i}>{v}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Chain of Thought Reasoning Box */}
                <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-2.5">
                  <div
                    className="flex items-center justify-between cursor-pointer text-xs font-semibold text-slate-300 mb-1"
                    onClick={() => setShowThinking(!showThinking)}
                  >
                    <span className="flex items-center gap-1.5 text-indigo-300 text-[11px]">
                      <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> DeepSeek-R1 &lt;think&gt; Reasoning:
                    </span>
                    {showThinking ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />}
                  </div>

                  {showThinking && (
                    <div className="mt-1.5 text-slate-300 text-xs leading-relaxed space-y-1.5">
                      <p className="bg-slate-900/90 p-2.5 rounded border border-slate-800/80 font-mono text-[11px] text-slate-300 whitespace-pre-line">
                        {latestAudit.thinking || latestAudit.reason}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-slate-950/30 border border-dashed border-slate-800 rounded-lg p-5 text-center flex flex-col items-center justify-center gap-1 text-slate-500">
                <ShieldCheck className="w-5 h-5" />
                <p className="text-xs">Awaiting signal proposal from Researcher.</p>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Post-Mortem Autopsies View */}
        {activeSubTab === 'autopsies' && (
          <div className="flex-1 flex flex-col gap-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <BrainCircuit className="w-4 h-4 text-rose-400" />
                DeepSeek-R1 Post-Mortem Self-Reflection
              </span>
              <button
                onClick={onTriggerSimulatedAutopsy}
                className="px-2.5 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 text-[10px] font-semibold transition cursor-pointer flex items-center gap-1"
                title="Test how DeepSeek-R1 autopsies a stopped-out trade and embeds it into ChromaDB"
              >
                <Activity className="w-3 h-3" />
                + Run Loss Autopsy
              </button>
            </div>

            {latestAutopsy ? (
              <div className="bg-slate-950 border border-rose-900/50 rounded-xl p-3 space-y-2 text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div>
                    <span className="font-bold text-slate-100">{latestAutopsy.ticker} Failed Setup Autopsy</span>
                    <span className="text-[10px] text-rose-400 font-mono ml-2 font-bold">
                      -${latestAutopsy.lossAmount.toFixed(2)} (-{latestAutopsy.lossPct.toFixed(2)}%)
                    </span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 font-mono text-[9px] font-bold">
                    {latestAutopsy.failureTag}
                  </span>
                </div>

                <div className="space-y-1.5 text-[11px]">
                  <div>
                    <span className="text-slate-400">Root Cause: </span>
                    <span className="text-slate-200 font-medium">{latestAutopsy.rootCause}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Lesson Learned: </span>
                    <span className="text-amber-300">{latestAutopsy.lessonLearned}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800 font-mono text-[10px] text-emerald-300">
                    <span className="text-slate-400 block font-sans text-[9px] uppercase font-bold text-slate-500">
                      New Guardrail Invariant:
                    </span>
                    {latestAutopsy.guardrailRule}
                  </div>
                </div>

                <div className="pt-1 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                  <span className="flex items-center gap-1 text-indigo-400">
                    <Database className="w-3 h-3" /> Embedded in ChromaDB Vector Memory
                  </span>
                  <span>{new Date(latestAutopsy.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            ) : (
              <div className="bg-slate-950/40 border border-slate-800 rounded-lg p-4 text-center text-slate-500 text-xs">
                No loss autopsies recorded yet.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
