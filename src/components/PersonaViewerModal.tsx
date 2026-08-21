import React, { useState } from 'react';
import { X, BookOpen, UserCheck, Shield, FileText, CheckCircle2, Eye, History, Waves } from 'lucide-react';
import { RESEARCHER_PERSONA, CRITIC_PERSONA } from '../data/personaData';

interface PersonaViewerModalProps {
  isOpen?: boolean;
  onClose: () => void;
}

export const PersonaViewerModal: React.FC<PersonaViewerModalProps> = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState<'RESEARCHER' | 'CRITIC' | 'MANIFESTS'>('RESEARCHER');

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-100">Persona Declarations &amp; Shark Hunting Rules</h3>
              <p className="text-xs text-slate-400">
                System 1 (Researcher: DeepSeek-R1 14B) &amp; System 2 (Critic: DeepSeek-R1 14B)
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Buttons */}
        <div className="flex border-b border-slate-800 bg-slate-950/60 px-6 gap-2 pt-2">
          <button
            onClick={() => setActiveTab('RESEARCHER')}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition flex items-center gap-2 border-b-2 cursor-pointer ${
              activeTab === 'RESEARCHER'
                ? 'border-emerald-400 text-emerald-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <UserCheck className="w-4 h-4 text-emerald-400" />
            Researcher (Quinn - DeepSeek-R1 14B)
          </button>

          <button
            onClick={() => setActiveTab('CRITIC')}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition flex items-center gap-2 border-b-2 cursor-pointer ${
              activeTab === 'CRITIC'
                ? 'border-indigo-400 text-indigo-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Shield className="w-4 h-4 text-indigo-400" />
            Critic Auditor (Morgan - DeepSeek-R1 14B)
          </button>

          <button
            onClick={() => setActiveTab('MANIFESTS')}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition flex items-center gap-2 border-b-2 cursor-pointer ${
              activeTab === 'MANIFESTS'
                ? 'border-amber-400 text-amber-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-4 h-4 text-amber-400" />
            Active Tools &amp; Invariants
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4 text-xs">
          {activeTab === 'RESEARCHER' && (
            <div className="space-y-4">
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-emerald-300">{RESEARCHER_PERSONA.name}</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono text-[11px]">
                    Model: {RESEARCHER_PERSONA.model} (Unified VRAM)
                  </span>
                </div>
                <p className="text-slate-400">{RESEARCHER_PERSONA.title}</p>
                <div className="text-slate-300 font-medium pt-1">
                  Focus: {RESEARCHER_PERSONA.role}
                </div>
              </div>

              {/* Shark Activity & Patience Principles */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 className="font-bold text-slate-200 text-xs uppercase tracking-wider flex items-center gap-1.5 text-amber-300">
                  <Waves className="w-4 h-4" /> Shark Activity Hunting &amp; Patience Rules
                </h4>
                <ul className="space-y-2 text-slate-300">
                  {RESEARCHER_PERSONA.corePrinciples.map((p, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{p}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* System prompt summary */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 className="font-bold text-slate-200 text-xs uppercase tracking-wider">
                  System Persona Directive
                </h4>
                <p className="text-slate-300 leading-relaxed font-mono text-[11px] bg-slate-900/90 p-3 rounded border border-slate-800">
                  {RESEARCHER_PERSONA.systemPromptSummary}
                </p>
              </div>
            </div>
          )}

          {activeTab === 'CRITIC' && (
            <div className="space-y-4">
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-indigo-300">{CRITIC_PERSONA.name}</span>
                  <span className="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono text-[11px]">
                    Model: {CRITIC_PERSONA.model} (Unified VRAM)
                  </span>
                </div>
                <p className="text-slate-400">{CRITIC_PERSONA.title}</p>
                <div className="text-slate-300 font-medium pt-1">
                  Focus: {CRITIC_PERSONA.role}
                </div>
              </div>

              {/* Core Invariants & Historical Traceback */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 className="font-bold text-slate-200 text-xs uppercase tracking-wider flex items-center gap-1.5 text-indigo-300">
                  <History className="w-4 h-4" /> Hard Invariants &amp; Historical Ledger Traceback
                </h4>
                <ul className="space-y-2 text-slate-300">
                  {CRITIC_PERSONA.coreInvariants.map((inv, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <Shield className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                      <span>{inv}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* System prompt directive */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 className="font-bold text-slate-200 text-xs uppercase tracking-wider">
                  Senior Auditor Directive
                </h4>
                <p className="text-slate-300 leading-relaxed font-mono text-[11px] bg-slate-900/90 p-3 rounded border border-slate-800">
                  {CRITIC_PERSONA.systemPromptSummary}
                </p>
              </div>
            </div>
          )}

          {activeTab === 'MANIFESTS' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 className="font-bold text-emerald-300 text-xs uppercase">Worker Tools Manifest</h4>
                <ul className="space-y-1 font-mono text-[11px] text-slate-400">
                  {RESEARCHER_PERSONA.tools.map((t, i) => (
                    <li key={i} className="bg-slate-900/80 p-1.5 rounded border border-slate-800/80">
                      {t}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 className="font-bold text-indigo-300 text-xs uppercase">Critic Tools Manifest</h4>
                <ul className="space-y-1 font-mono text-[11px] text-slate-400">
                  {CRITIC_PERSONA.tools.map((t, i) => (
                    <li key={i} className="bg-slate-900/80 p-1.5 rounded border border-slate-800/80">
                      {t}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between text-xs text-slate-400">
          <span>Both agents share the <code>deepseek-r1:14b</code> model weights in memory without double allocation.</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
