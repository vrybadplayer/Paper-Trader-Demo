import React, { useState } from 'react';
import { LogEntry } from '../types';
import { Terminal, Filter, Trash2, Shield, Cpu, Activity } from 'lucide-react';

interface LiveConsoleProps {
  logs: LogEntry[];
  onClearLogs: () => void;
}

export const LiveConsole: React.FC<LiveConsoleProps> = ({ logs, onClearLogs }) => {
  const [filter, setFilter] = useState<string>('ALL');

  const filteredLogs = logs.filter((log) => {
    if (filter === 'ALL') return true;
    if (filter === 'WORKER') return log.component.includes('Worker') || log.level === 'WORKER';
    if (filter === 'CRITIC') return log.component.includes('Critic') || log.level === 'CRITIC';
    if (filter === 'ORCHESTRATOR') return log.component.includes('Orchestrator') || log.level === 'SYSTEM';
    return true;
  });

  const getLevelBadge = (level: LogEntry['level']) => {
    switch (level) {
      case 'WORKER':
        return 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60';
      case 'CRITIC':
        return 'text-indigo-400 bg-indigo-950/60 border-indigo-800/60';
      case 'WARNING':
        return 'text-amber-400 bg-amber-950/60 border-amber-800/60';
      case 'ERROR':
        return 'text-rose-400 bg-rose-950/60 border-rose-800/60';
      case 'SYSTEM':
        return 'text-sky-400 bg-sky-950/60 border-sky-800/60';
      default:
        return 'text-slate-400 bg-slate-800 border-slate-700';
    }
  };

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-lg flex flex-col font-mono text-xs">
      {/* Console Header Bar */}
      <div className="bg-slate-900 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 text-slate-300">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span className="font-semibold text-xs text-slate-200">Dual-Agent Telemetry Stream</span>
          <span className="text-[10px] text-slate-500 font-mono">({filteredLogs.length} events)</span>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center bg-slate-950 rounded-lg p-0.5 border border-slate-800 text-[11px]">
            {['ALL', 'WORKER', 'CRITIC', 'ORCHESTRATOR'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-2 py-0.5 rounded cursor-pointer transition ${
                  filter === f
                    ? 'bg-slate-800 text-slate-100 font-bold shadow-xs'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <button
            onClick={onClearLogs}
            className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition cursor-pointer"
            title="Clear Console"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Log Feed */}
      <div className="p-3.5 max-h-60 overflow-y-auto space-y-1.5 bg-slate-950/95 text-[11px]">
        {filteredLogs.length === 0 ? (
          <div className="text-slate-600 py-6 text-center italic">
            Console ready. State events and LLM reasoning logs will stream here.
          </div>
        ) : (
          filteredLogs.map((log) => (
            <div key={log.id} className="flex items-start gap-2 hover:bg-slate-900/50 p-1 rounded transition">
              <span className="text-slate-500 shrink-0 select-none">{log.timestamp.split('T')[1]?.slice(0, 8)}</span>
              <span
                className={`px-1.5 py-0.2 rounded text-[9px] font-bold border uppercase shrink-0 ${getLevelBadge(
                  log.level
                )}`}
              >
                {log.component}
              </span>
              <span className="text-slate-300 leading-relaxed break-all">{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
