import React from 'react';
import { FsmState } from '../types';
import { Database, TrendingUp, CheckCircle, ArrowRight, Zap, PlayCircle, Clock, Eye, History } from 'lucide-react';

interface OrchestratorPanelProps {
  currentState: FsmState;
  activeTicker: string;
  onSelectTicker: (ticker: string) => void;
  tickers: string[];
  cyclesObserved: number;
  sharkTriggersCount: number;
}

export const OrchestratorPanel: React.FC<OrchestratorPanelProps> = ({
  currentState,
  activeTicker,
  onSelectTicker,
  tickers,
  cyclesObserved,
  sharkTriggersCount,
}) => {
  const steps: { state: FsmState; label: string; icon: any; agent: string; desc: string }[] = [
    { state: 'IDLE', label: 'Idle / Clock', icon: Clock, agent: 'Scheduler', desc: 'Awaiting scheduled scan interval' },
    { state: 'FETCHING_DATA', label: 'Market & PnL Trace', icon: History, agent: 'Broker & Ledger', desc: 'Reads historical win/loss ledger' },
    { state: 'OBSERVING', label: 'Shark Flow Monitor', icon: Eye, agent: 'Tape Reader', desc: 'Scanning for institutional volume footprints' },
    { state: 'GENERATING_SIGNAL', label: 'DeepSeek Researcher', icon: TrendingUp, agent: 'Worker (R1 14B)', desc: 'Formulates trade only on confirmed setup' },
    { state: 'VALIDATING_SIGNAL', label: 'DeepSeek Risk Audit', icon: CheckCircle, agent: 'Critic (R1 14B)', desc: 'Audits past drawdowns & invariants' },
    { state: 'EXECUTING_TRADE', label: 'Sandbox Execution', icon: Zap, agent: 'Broker Gateway', desc: 'Executes order with slippage control' },
  ];

  const getStateIndex = (state: FsmState) => {
    return steps.findIndex((s) => s.state === state);
  };

  const currentIndex = getStateIndex(currentState);

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 lg:p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
              Dual-Agent Orchestrator • Shark Activity &amp; PnL Traceback Pipeline
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Patience-first execution: loops quietly observe orderbook flow; trades trigger only when whale indicators align.
          </p>
        </div>

        {/* Stats and Watchlist selector */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2 text-xs bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800">
            <span className="text-slate-400">Cycles:</span>
            <span className="font-mono font-bold text-amber-400">{cyclesObserved}</span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">Shark Triggers:</span>
            <span className="font-mono font-bold text-emerald-400">{sharkTriggersCount}</span>
          </div>

          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs text-slate-400 font-medium mr-1">Bursa Watchlist:</span>
            {tickers.map((t) => {
              const aliasMap: Record<string, string> = {
                '5238.KL': '5238 AAGB',
                '0138.KL': '0138 ZETRIX',
                '0459.KL': '0459 SUM',
                '4677.KL': '4677 YTL',
                '1155.KL': '1155 MAYBANK',
              };
              const displayLabel = aliasMap[t] || t;
              return (
                <button
                  key={t}
                  id={`ticker-btn-${t}`}
                  onClick={() => onSelectTicker(t)}
                  className={`px-2.5 py-1 text-xs font-mono font-bold rounded-lg transition cursor-pointer ${
                    activeTicker === t
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm'
                      : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700/60'
                  }`}
                >
                  {displayLabel}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* FSM Steps progression pipeline */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 pt-1">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isActive = step.state === currentState;
          const isPast = currentIndex > idx;

          let badgeStyles = 'border-slate-800 bg-slate-900/60 text-slate-500';
          if (isActive) {
            badgeStyles = 'border-emerald-500/80 bg-emerald-950/40 text-emerald-300 shadow-md shadow-emerald-900/20 ring-1 ring-emerald-500/30';
          } else if (isPast) {
            badgeStyles = 'border-slate-700/80 bg-slate-800/60 text-slate-300';
          }

          return (
            <div
              key={step.state}
              className={`p-2.5 rounded-lg border transition-all duration-200 flex flex-col justify-between relative ${badgeStyles}`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono font-semibold opacity-60">0{idx + 1}</span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium ${isActive ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}>
                  {step.agent}
                </span>
              </div>
              <div className="flex items-center gap-2 my-1">
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-emerald-400 animate-bounce' : isPast ? 'text-emerald-500/70' : 'text-slate-500'}`} />
                <span className="text-xs font-semibold leading-tight">{step.label}</span>
              </div>
              <p className="text-[10px] text-slate-400 line-clamp-1 opacity-80">{step.desc}</p>
              {isActive && (
                <span className="text-[9px] text-emerald-400 font-mono font-medium animate-pulse mt-1">
                  ● ACTIVE STEP
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
