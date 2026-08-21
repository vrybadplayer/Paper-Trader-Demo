import React, { useState } from 'react';
import { Portfolio, ExecutedTrade, LogEntry, PostMortemAutopsy } from '../types';
import { Wallet, TrendingUp, TrendingDown, Clock, Shield, Terminal, ArrowUpRight, ArrowDownRight, History, Award, BrainCircuit, Database, ShieldAlert, Sparkles } from 'lucide-react';

interface PortfolioLedgerProps {
  portfolio: Portfolio;
  trades: ExecutedTrade[];
  logs: LogEntry[];
  autopsies: PostMortemAutopsy[];
  onTriggerSimulatedAutopsy: () => void;
}

export const PortfolioLedger: React.FC<PortfolioLedgerProps> = ({
  portfolio,
  trades,
  logs,
  autopsies,
  onTriggerSimulatedAutopsy,
}) => {
  const [activeTab, setActiveTab] = useState<'ledger' | 'autopsies' | 'positions' | 'logs'>('ledger');

  const totalPnL = portfolio.realizedPnl + portfolio.unrealizedPnl;
  const isPositivePnL = totalPnL >= 0;

  // Calculate Win/Loss statistics from executed trade ledger
  const closedTrades = trades.filter((t) => t.realizedPnl !== undefined && t.realizedPnl !== 0);
  const winningTrades = closedTrades.filter((t) => (t.realizedPnl || 0) > 0);
  const winRate = closedTrades.length > 0 ? (winningTrades.length / closedTrades.length) * 100 : 0;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-md flex flex-col">
      {/* Portfolio Top Bar */}
      <div className="bg-slate-800/80 border-b border-slate-700/80 p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-700 flex items-center justify-center text-emerald-400">
              <Wallet className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-slate-400 font-medium">Total Portfolio Equity</div>
              <div className="text-xl font-mono font-black text-slate-100">
                RM {portfolio.totalEquity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6 flex-wrap">
            <div>
              <div className="text-[11px] text-slate-400">Available Liquid Cash</div>
              <div className="text-sm font-mono font-bold text-slate-200">
                RM {portfolio.availableCash.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>

            <div>
              <div className="text-[11px] text-slate-400">Reserve Floor Limit</div>
              <div className="text-sm font-mono font-semibold text-indigo-300 flex items-center gap-1">
                <Shield className="w-3 h-3 text-indigo-400" />
                RM {portfolio.reserveLimit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>

            <div>
              <div className="text-[11px] text-slate-400">Historical Realized P&amp;L</div>
              <div
                className={`text-sm font-mono font-bold flex items-center gap-1 ${
                  portfolio.realizedPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {portfolio.realizedPnl >= 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                {portfolio.realizedPnl >= 0 ? '+' : ''}
                RM {portfolio.realizedPnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>

            <div>
              <div className="text-[11px] text-slate-400">Ledger Win Rate</div>
              <div className="text-sm font-mono font-bold text-amber-300 flex items-center gap-1">
                <Award className="w-3.5 h-3.5 text-amber-400" />
                {closedTrades.length > 0 ? `${winRate.toFixed(1)}% (${winningTrades.length}/${closedTrades.length})` : 'N/A'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-950/60 px-4 text-xs font-semibold overflow-x-auto">
        <button
          onClick={() => setActiveTab('ledger')}
          className={`py-3 px-4 flex items-center gap-2 border-b-2 cursor-pointer transition whitespace-nowrap ${
            activeTab === 'ledger'
              ? 'border-emerald-500 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <History className="w-4 h-4" />
          Trade Audit Ledger ({trades.length})
        </button>

        <button
          onClick={() => setActiveTab('autopsies')}
          className={`py-3 px-4 flex items-center gap-2 border-b-2 cursor-pointer transition whitespace-nowrap ${
            activeTab === 'autopsies'
              ? 'border-rose-500 text-rose-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <BrainCircuit className="w-4 h-4 text-rose-400" />
          ChromaDB Post-Mortem Autopsies ({autopsies.length})
        </button>

        <button
          onClick={() => setActiveTab('positions')}
          className={`py-3 px-4 flex items-center gap-2 border-b-2 cursor-pointer transition whitespace-nowrap ${
            activeTab === 'positions'
              ? 'border-emerald-500 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Wallet className="w-4 h-4" />
          Open Positions ({portfolio.positions.length})
        </button>

        <button
          onClick={() => setActiveTab('logs')}
          className={`py-3 px-4 flex items-center gap-2 border-b-2 cursor-pointer transition whitespace-nowrap ${
            activeTab === 'logs'
              ? 'border-emerald-500 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Terminal className="w-4 h-4" />
          Live FSM Logs ({logs.length})
        </button>
      </div>

      {/* Tab Contents */}
      <div className="p-4 flex-1 overflow-y-auto max-h-80">
        {/* TAB 1: Ledger */}
        {activeTab === 'ledger' && (
          <div>
            {trades.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500">
                No trades executed yet. The bot is actively observing the market.
              </div>
            ) : (
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                    <th className="pb-2">Time</th>
                    <th className="pb-2">Action</th>
                    <th className="pb-2">Ticker</th>
                    <th className="pb-2">Shares</th>
                    <th className="pb-2">Exec Price</th>
                    <th className="pb-2">Realized Earn/Loss</th>
                    <th className="pb-2">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {trades.map((trade) => (
                    <tr key={trade.id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 text-slate-400 text-[11px]">
                        {new Date(trade.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="py-2.5">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            trade.action === 'BUY'
                              ? 'bg-emerald-500/20 text-emerald-400'
                              : 'bg-rose-500/20 text-rose-400'
                          }`}
                        >
                          {trade.action}
                        </span>
                      </td>
                      <td className="py-2.5 font-bold text-slate-200">{trade.ticker}</td>
                      <td className="py-2.5 text-slate-300">{trade.quantity} ({trade.quantity / 100} lots)</td>
                      <td className="py-2.5 text-slate-300">RM {trade.price.toFixed(3)}</td>
                      <td className="py-2.5">
                        {trade.realizedPnl !== undefined ? (
                          <span
                            className={`font-bold ${
                              trade.realizedPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                            }`}
                          >
                            {trade.realizedPnl >= 0 ? '+' : ''}
                            RM {trade.realizedPnl.toFixed(2)}
                            {trade.pnlPercentage !== undefined && (
                              <span className="text-[10px] opacity-80 ml-1">
                                ({trade.pnlPercentage >= 0 ? '+' : ''}{trade.pnlPercentage.toFixed(1)}%)
                              </span>
                            )}
                          </span>
                        ) : (
                          <span className="text-slate-500 text-[11px]">- (Open)</span>
                        )}
                      </td>
                      <td className="py-2.5">
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-semibold">
                          {trade.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* TAB 2: ChromaDB Post-Mortem Autopsies */}
        {activeTab === 'autopsies' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between bg-slate-950/80 p-2.5 rounded-lg border border-slate-800">
              <div className="text-xs text-slate-300">
                <span className="font-semibold text-rose-400">DeepSeek-R1 Automated Post-Mortem Engine:</span>{' '}
                When a trade hits a stop-loss or exits in the red, Morgan dissects the structural breakdown, extracts hard guardrails, and embeds the vector representation into ChromaDB memory.
              </div>
              <button
                onClick={onTriggerSimulatedAutopsy}
                className="px-3 py-1.5 rounded-lg bg-rose-600/30 hover:bg-rose-600/40 border border-rose-500/50 text-rose-200 text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 shrink-0 ml-3"
              >
                <Sparkles className="w-3.5 h-3.5 text-rose-400" />
                Simulate Stop-Loss &amp; Run Autopsy
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {autopsies.map((a) => (
                <div key={a.id} className="bg-slate-950 border border-rose-900/60 rounded-xl p-3.5 space-y-2.5 text-xs shadow-xs">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <div className="flex items-center gap-2">
                      <ShieldAlert className="w-4 h-4 text-rose-400" />
                      <span className="font-bold text-slate-100">{a.ticker} Failure Autopsy</span>
                      <span className="font-mono font-bold text-rose-400 text-[11px]">
                        -${a.lossAmount.toFixed(2)} (-{a.lossPct.toFixed(1)}%)
                      </span>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 font-mono text-[9px] font-bold">
                      {a.failureTag}
                    </span>
                  </div>

                  <div className="space-y-1.5 text-[11px]">
                    <div>
                      <span className="text-slate-400 font-medium">Root Cause: </span>
                      <span className="text-slate-200">{a.rootCause}</span>
                    </div>

                    <div className="bg-slate-900/90 p-2 rounded border border-slate-800/80 font-mono text-[10px] text-slate-300 leading-relaxed">
                      <span className="text-indigo-400 font-semibold block mb-0.5">DeepSeek-R1 CoT Diagnosis:</span>
                      {a.breakdown}
                    </div>

                    <div>
                      <span className="text-slate-400 font-medium">Lesson Learned: </span>
                      <span className="text-amber-300">{a.lessonLearned}</span>
                    </div>

                    <div className="p-2 rounded bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 font-mono text-[10px]">
                      <span className="text-emerald-400 font-semibold block text-[9px] uppercase font-sans">
                        Immutable Guardrail Invariant:
                      </span>
                      {a.guardrailRule}
                    </div>
                  </div>

                  <div className="pt-1 flex items-center justify-between text-[10px] text-slate-500 font-mono border-t border-slate-800/60">
                    <span className="flex items-center gap-1 text-indigo-400">
                      <Database className="w-3 h-3" /> ChromaDB HNSW Embedded
                    </span>
                    <span>{new Date(a.timestamp).toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: Positions */}
        {activeTab === 'positions' && (
          <div>
            {portfolio.positions.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500">
                100% Cash Portfolio (RM {portfolio.cashBalance.toLocaleString()} liquid capital). No open risk exposure.
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {portfolio.positions.map((pos) => (
                  <div key={pos.ticker} className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono font-bold text-slate-100">{pos.ticker}</span>
                      <span className="text-xs text-slate-400 font-mono">{pos.quantity} shares ({pos.quantity / 100} lots)</span>
                    </div>
                    <div className="text-xs text-slate-400 space-y-1 font-mono">
                      <div className="flex justify-between">
                        <span>Avg Cost:</span>
                        <span>RM {pos.avgCost.toFixed(3)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Current:</span>
                        <span>RM {pos.currentPrice.toFixed(3)}</span>
                      </div>
                      <div className="flex justify-between font-bold pt-1 border-t border-slate-800">
                        <span>Unrealized P&amp;L:</span>
                        <span className={pos.unrealizedPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                          {pos.unrealizedPnl >= 0 ? '+' : ''}RM {pos.unrealizedPnl.toFixed(2)} ({pos.unrealizedPnlPct.toFixed(1)}%)
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 4: Logs */}
        {activeTab === 'logs' && (
          <div className="space-y-1.5 font-mono text-[11px]">
            {logs.slice(0, 30).map((log) => (
              <div key={log.id} className="p-1.5 rounded bg-slate-950/70 border border-slate-800/80 flex items-start gap-2">
                <span className="text-slate-500 shrink-0">{new Date(log.timestamp).toLocaleTimeString()}</span>
                <span
                  className={`px-1 py-0.2 rounded text-[9px] font-bold shrink-0 ${
                    log.level === 'CRITIC'
                      ? 'bg-indigo-950 text-indigo-300'
                      : log.level === 'WORKER'
                      ? 'bg-emerald-950 text-emerald-300'
                      : log.level === 'OBSERVER'
                      ? 'bg-amber-950 text-amber-300'
                      : log.level === 'SYSTEM'
                      ? 'bg-slate-800 text-slate-300'
                      : 'bg-slate-900 text-slate-400'
                  }`}
                >
                  {log.level}
                </span>
                <span className="text-slate-300">{log.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
