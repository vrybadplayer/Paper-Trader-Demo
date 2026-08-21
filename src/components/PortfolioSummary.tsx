import React from 'react';
import { Portfolio, ExecutedTrade } from '../types';
import { Wallet, DollarSign, PieChart, ArrowUpRight, ArrowDownRight, Layers } from 'lucide-react';

interface PortfolioSummaryProps {
  portfolio: Portfolio;
  recentTrades: ExecutedTrade[];
}

export const PortfolioSummary: React.FC<PortfolioSummaryProps> = ({
  portfolio,
  recentTrades,
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Portfolio Equity Stats */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between shadow-sm">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
          <span className="font-semibold uppercase tracking-wider flex items-center gap-1.5">
            <Wallet className="w-3.5 h-3.5 text-emerald-400" /> Account Capital
          </span>
          <span className="font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40 text-[10px]">
            Moomoo / Bursa Malaysia
          </span>
        </div>

        <div className="my-2">
          <div className="text-2xl font-bold font-mono text-slate-100">
            RM {portfolio.totalEquity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="flex items-center gap-2 text-xs mt-1">
            <span className="text-slate-400">Cash Balance:</span>
            <span className="font-mono font-medium text-slate-200">RM {portfolio.cashBalance.toLocaleString()}</span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400">Available:</span>
            <span className="font-mono font-medium text-emerald-300">
              RM {Math.max(0, portfolio.cashBalance - portfolio.reserveLimit).toLocaleString()}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs">
          <div>
            <span className="text-slate-500 text-[10px] block">Realized PnL</span>
            <span className={`font-mono font-bold ${portfolio.realizedPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {portfolio.realizedPnl >= 0 ? '+' : ''}RM {portfolio.realizedPnl.toFixed(2)}
            </span>
          </div>
          <div>
            <span className="text-slate-500 text-[10px] block">Unrealized PnL</span>
            <span className={`font-mono font-bold ${portfolio.unrealizedPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {portfolio.unrealizedPnl >= 0 ? '+' : ''}RM {portfolio.unrealizedPnl.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Active Positions */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col shadow-sm">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
          <span className="font-semibold uppercase tracking-wider flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" /> Bursa Positions ({portfolio.positions.length})
          </span>
          <span className="text-[10px] text-slate-500 font-mono">1 Lot = 100 Shares</span>
        </div>

        <div className="flex-1 overflow-y-auto max-h-32 space-y-1.5 pr-1">
          {portfolio.positions.length === 0 ? (
            <div className="text-center py-5 text-xs text-slate-500">
              No open positions. 100% liquid cash.
            </div>
          ) : (
            portfolio.positions.map((pos) => (
              <div
                key={pos.ticker}
                className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2 flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-bold text-slate-200 font-mono">{pos.ticker}</span>
                  <span className="text-slate-400 text-[11px] ml-2 font-mono">{pos.quantity} shares ({pos.quantity / 100} lots)</span>
                </div>
                <div className="text-right font-mono">
                  <div className="text-slate-200 font-medium">RM {pos.marketValue.toLocaleString()}</div>
                  <div className={`text-[10px] ${pos.unrealizedPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {pos.unrealizedPnl >= 0 ? '+' : ''}RM {pos.unrealizedPnl.toFixed(2)} ({pos.unrealizedPnlPct.toFixed(1)}%)
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Recent Executed Trades */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col shadow-sm">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
          <span className="font-semibold uppercase tracking-wider flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-amber-400" /> Trade Ledger (Recent)
          </span>
          <span className="text-[10px] text-slate-500 font-mono">{recentTrades.length} records</span>
        </div>

        <div className="flex-1 overflow-y-auto max-h-32 space-y-1.5 pr-1">
          {recentTrades.length === 0 ? (
            <div className="text-center py-5 text-xs text-slate-500">
              No trades executed yet.
            </div>
          ) : (
            recentTrades.slice(0, 5).map((trade) => (
              <div
                key={trade.id}
                className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2 flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold font-mono ${
                      trade.action === 'BUY'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    }`}
                  >
                    {trade.action}
                  </span>
                  <span className="font-bold text-slate-200 font-mono">{trade.ticker}</span>
                  <span className="text-slate-400 text-[11px] font-mono">{trade.quantity} @ ${trade.price.toFixed(2)}</span>
                </div>
                <div className="text-right text-[10px] text-slate-500 font-mono">
                  {trade.timestamp.split('T')[1]?.slice(0, 8) || 'Now'}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
