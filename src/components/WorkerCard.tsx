import React, { useState } from 'react';
import { IndicatorSnapshot, TradeSignal, SharkActivity } from '../types';
import { RESEARCHER_PERSONA } from '../data/personaData';
import { Brain, TrendingUp, TrendingDown, Target, ShieldAlert, Code2, Sparkles, Check, HelpCircle, Eye, Waves, History } from 'lucide-react';

interface WorkerCardProps {
  activeTicker: string;
  indicators: IndicatorSnapshot;
  latestSignal: TradeSignal | null;
  isGenerating: boolean;
  isObserving: boolean;
  historicalPnlSummary: string;
}

export const WorkerCard: React.FC<WorkerCardProps> = ({
  activeTicker,
  indicators,
  latestSignal,
  isGenerating,
  isObserving,
  historicalPnlSummary,
}) => {
  const [showJson, setShowJson] = useState(false);
  const shark = indicators.sharkActivity;

  const getRsiColor = (rsi: number) => {
    if (rsi < 32) return 'text-emerald-400 font-bold';
    if (rsi > 68) return 'text-rose-400 font-bold';
    return 'text-slate-300';
  };

  const getSharkBadge = (type?: SharkActivity['type']) => {
    switch (type) {
      case 'WHALE_ACCUMULATION':
        return { label: 'Whale Accumulation Block', color: 'bg-emerald-950 text-emerald-300 border-emerald-700/60' };
      case 'LIQUIDITY_SWEEP':
        return { label: 'Stop Hunt / Liquidity Sweep', color: 'bg-indigo-950 text-indigo-300 border-indigo-700/60' };
      case 'AGGRESSIVE_ABSORPTION':
        return { label: 'Limit Order Delta Absorption', color: 'bg-teal-950 text-teal-300 border-teal-700/60' };
      case 'DISTRIBUTION_BLOCK':
        return { label: 'Institutional Distribution', color: 'bg-rose-950 text-rose-300 border-rose-700/60' };
      default:
        return { label: 'Observing Normal Retail Flow', color: 'bg-slate-900 text-slate-400 border-slate-800' };
    }
  };

  const sharkBadge = getSharkBadge(shark?.type);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden flex flex-col h-full shadow-md">
      {/* Card Header */}
      <div className="bg-slate-800/80 border-b border-slate-700/80 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-sm text-slate-100">{RESEARCHER_PERSONA.name}</h3>
              <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono font-bold">
                {RESEARCHER_PERSONA.model}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">System 1: Deep Alpha Researcher &amp; Tape Observer</p>
          </div>
        </div>

        <button
          onClick={() => setShowJson(!showJson)}
          className={`p-1.5 rounded-lg border text-xs font-mono transition flex items-center gap-1 cursor-pointer ${
            showJson
              ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300'
              : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
          }`}
          title="Toggle JSON Output"
        >
          <Code2 className="w-3.5 h-3.5" />
          <span className="text-[10px]">JSON</span>
        </button>
      </div>

      <div className="p-4 flex-1 flex flex-col gap-3.5">
        {/* Shark Activity & Tape Radar Box */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
            <span className="font-semibold uppercase tracking-wider text-[10px] flex items-center gap-1.5 text-amber-300">
              <Waves className="w-3.5 h-3.5" /> Shark Activity Radar ({activeTicker})
            </span>
            <span className={`text-[10px] px-2 py-0.5 rounded font-mono border ${sharkBadge.color}`}>
              {sharkBadge.label}
            </span>
          </div>

          <div className="text-[11px] text-slate-300 bg-slate-900/90 p-2.5 rounded border border-slate-800/80 flex items-start gap-2">
            <Eye className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <p className="leading-snug">{shark?.notes || 'Scanning order book delta and volume absorption...'}</p>
              {shark?.detected && (
                <div className="mt-1 flex items-center gap-2 text-[10px] font-mono text-emerald-400 font-semibold">
                  <span>● SHARK CONFIRMATION: {shark.type}</span>
                  <span>| Delta Vol: {shark.deltaVolume > 0 ? '+' : ''}{shark.deltaVolume.toLocaleString()} sh</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Technical Indicators Box */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="font-semibold uppercase tracking-wider text-[10px]">Technical Context</span>
            <span className="font-mono text-slate-200 font-bold">${indicators.currentPrice.toFixed(2)}</span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="bg-slate-900/90 p-2 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400">RSI (14)</div>
              <div className={`font-mono text-sm ${getRsiColor(indicators.rsi)}`}>
                {indicators.rsi.toFixed(1)}
              </div>
              <div className="text-[9px] text-slate-500 mt-0.5">
                {indicators.rsi < 30 ? 'Oversold' : indicators.rsi > 70 ? 'Overbought' : 'Fair Value'}
              </div>
            </div>

            <div className="bg-slate-900/90 p-2 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400">MACD / Signal</div>
              <div className="font-mono text-xs text-slate-200">
                {indicators.macd.toFixed(2)} / {indicators.macdSignal.toFixed(2)}
              </div>
              <div className="text-[9px] text-slate-500 mt-0.5">
                {indicators.macd > indicators.macdSignal ? 'Bullish Cross' : 'Bearish Divergence'}
              </div>
            </div>

            <div className="bg-slate-900/90 p-2 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400">Bollinger Range</div>
              <div className="font-mono text-xs text-slate-200">
                ${indicators.bollingerLower.toFixed(1)} - ${indicators.bollingerUpper.toFixed(1)}
              </div>
              <div className="text-[9px] text-slate-500 mt-0.5">
                20-period Volatility
              </div>
            </div>
          </div>
        </div>

        {/* Historical Ledger Traceback for this ticker */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2.5 text-xs">
          <div className="flex items-center gap-1.5 text-slate-400 font-semibold text-[10px] uppercase mb-1">
            <History className="w-3.5 h-3.5 text-sky-400" /> Historical Performance Check ({activeTicker}):
          </div>
          <p className="text-slate-300 font-mono text-[11px]">
            {historicalPnlSummary || `No previous closed trades recorded for ${activeTicker}. Clean slate.`}
          </p>
        </div>

        {/* Signal Status */}
        <div className="flex-1 flex flex-col justify-between">
          {isGenerating ? (
            <div className="bg-emerald-950/20 border border-emerald-800/40 rounded-lg p-4 flex flex-col items-center justify-center text-center gap-2 py-5">
              <Brain className="w-6 h-6 text-emerald-400 animate-pulse" />
              <p className="text-xs font-semibold text-emerald-300">
                Quinn conducting DeepSeek-R1 CoT thesis formulation for {activeTicker}...
              </p>
              <p className="text-[11px] text-slate-400 font-mono">
                Factoring in shark volume patterns and historical win/loss ratios...
              </p>
            </div>
          ) : isObserving ? (
            <div className="bg-amber-950/20 border border-amber-800/40 rounded-lg p-4 flex flex-col items-center justify-center text-center gap-1.5 py-5 text-amber-300">
              <Eye className="w-5 h-5 animate-pulse text-amber-400" />
              <p className="text-xs font-semibold">Patience Mode: Quietly observing order flow</p>
              <p className="text-[11px] text-slate-400">
                No forced action. Waiting for confirmed institutional shark indicators before entry.
              </p>
            </div>
          ) : latestSignal ? (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                <div className="flex items-center gap-2.5">
                  <div
                    className={`w-9 h-9 rounded-lg flex items-center justify-center font-bold text-xs ${
                      latestSignal.action === 'BUY'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                        : latestSignal.action === 'SELL'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                        : 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {latestSignal.action === 'BUY' ? (
                      <TrendingUp className="w-5 h-5" />
                    ) : (
                      <TrendingDown className="w-5 h-5" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-slate-100 text-sm">
                        {latestSignal.action} {latestSignal.quantity} {latestSignal.ticker}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                        Conf: {(latestSignal.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono">
                      @ ${latestSignal.currentPrice.toFixed(2)} | Target: ${latestSignal.targetPrice.toFixed(2)}
                    </div>
                  </div>
                </div>

                <div className="text-right text-[11px] font-mono">
                  <div className="text-rose-400">Stop: ${latestSignal.stopLoss.toFixed(2)}</div>
                  <div className="text-emerald-400">Take: ${latestSignal.takeProfit.toFixed(2)}</div>
                </div>
              </div>

              {/* Rationale Thesis */}
              <div className="bg-slate-950/50 p-2.5 rounded-lg border border-slate-800/80 text-xs">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-1">
                  Researcher CoT Thesis (DeepSeek-R1):
                </span>
                <p className="text-slate-300 leading-relaxed text-xs">
                  {latestSignal.rationale}
                </p>
              </div>

              {/* JSON preview if active */}
              {showJson && (
                <pre className="bg-slate-950 p-2.5 rounded border border-slate-800 font-mono text-[10px] text-emerald-400 overflow-x-auto max-h-36">
                  {JSON.stringify(latestSignal, null, 2)}
                </pre>
              )}
            </div>
          ) : (
            <div className="bg-slate-950/30 border border-dashed border-slate-800 rounded-lg p-5 text-center flex flex-col items-center justify-center gap-1 text-slate-500">
              <Eye className="w-5 h-5" />
              <p className="text-xs">Observing tape. Waiting for confirmed shark setup.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
