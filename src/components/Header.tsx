import React from 'react';
import { Activity, Shield, Cpu, Terminal, BookOpen, Play, Pause, RefreshCw, Eye, Settings } from 'lucide-react';
import { FsmState } from '../types';

interface HeaderProps {
  fsmState: FsmState;
  isAutoRunning: boolean;
  onToggleAutoRun: () => void;
  onRunCycle: () => void;
  onOpenPersonas: () => void;
  onOpenSettings: () => void;
  ollamaConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  fsmState,
  isAutoRunning,
  onToggleAutoRun,
  onRunCycle,
  onOpenPersonas,
  onOpenSettings,
  ollamaConnected,
}) => {
  const getStateBadge = (state: FsmState) => {
    switch (state) {
      case 'IDLE': return { label: 'IDLE (Awaiting Tick)', color: 'bg-slate-500 text-slate-100' };
      case 'OBSERVING': return { label: 'OBSERVING (Shark Hunter)', color: 'bg-amber-500/90 text-amber-950 font-bold animate-pulse' };
      case 'FETCHING_DATA': return { label: 'SCANNING TAPE & PNL', color: 'bg-sky-500 text-sky-100 animate-pulse' };
      case 'GENERATING_SIGNAL': return { label: 'RESEARCHER COT (Alpha)', color: 'bg-emerald-500 text-emerald-100 animate-pulse' };
      case 'VALIDATING_SIGNAL': return { label: 'CRITIC AUDIT (DeepSeek)', color: 'bg-indigo-500 text-indigo-100 animate-pulse' };
      case 'EXECUTING_TRADE': return { label: 'EXECUTING ORDER', color: 'bg-rose-500 text-rose-100 animate-pulse' };
      case 'UPDATING_STATE': return { label: 'LEDGER & MEMORY SYNC', color: 'bg-teal-500 text-teal-100 animate-pulse' };
      case 'ERROR': return { label: 'SYSTEM ERROR', color: 'bg-rose-600 text-white' };
      default: return { label: state, color: 'bg-slate-600 text-slate-200' };
    }
  };

  const currentBadge = getStateBadge(fsmState);

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-30 px-4 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 via-teal-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-emerald-900/20 text-white font-black text-xl">
          PT
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-lg text-slate-100 tracking-tight">
              Paper Trader <span className="text-emerald-400 font-medium text-sm">Dual DeepSeek-R1 Engine</span>
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-mono">
              FSM v2.5
            </span>
          </div>
          <p className="text-xs text-slate-400">
            System 1 Worker (DeepSeek-R1) + System 2 Critic (DeepSeek-R1) • Shark Activity &amp; PnL Traceback Mode
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        {/* Model Unified Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/80 text-xs">
          <span className="w-2 h-2 rounded-full bg-indigo-400 ring-2 ring-indigo-400/20 animate-pulse"></span>
          <span className="text-indigo-300 font-mono font-bold">deepseek-r1:14b</span>
          <span className="px-1.5 py-0.2 text-[10px] rounded font-semibold uppercase bg-indigo-950 text-indigo-300 border border-indigo-800/50">
            Unified Shared RAM
          </span>
        </div>

        {/* FSM state indicator */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/80 text-xs">
          <span className="text-slate-400 font-medium">State:</span>
          <span className={`px-2 py-0.5 rounded font-mono font-semibold text-[11px] ${currentBadge.color}`}>
            {currentBadge.label}
          </span>
        </div>

        {/* Action buttons */}
        <button
          id="btn-run-cycle"
          onClick={onRunCycle}
          disabled={fsmState !== 'IDLE' && fsmState !== 'STOPPED'}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-semibold shadow-md transition-all cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${fsmState !== 'IDLE' && fsmState !== 'STOPPED' ? 'animate-spin' : ''}`} />
          Run Loop Cycle
        </button>

        <button
          id="btn-toggle-auto"
          onClick={onToggleAutoRun}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-md transition-all cursor-pointer ${
            isAutoRunning
              ? 'bg-amber-600 hover:bg-amber-500 text-white'
              : 'bg-indigo-600 hover:bg-indigo-500 text-white'
          }`}
        >
          {isAutoRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          {isAutoRunning ? 'Pause Monitor' : 'Auto Shark Monitor'}
        </button>

        <button
          id="btn-open-personas"
          onClick={onOpenPersonas}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition cursor-pointer"
        >
          <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
          Personas &amp; Rules
        </button>

        <button
          id="btn-open-settings"
          onClick={onOpenSettings}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition cursor-pointer"
          title="Configure Balance & Cash Reserve (settings.yaml)"
        >
          <Settings className="w-3.5 h-3.5 text-emerald-400" />
          Settings (yaml)
        </button>
      </div>
    </header>
  );
};
