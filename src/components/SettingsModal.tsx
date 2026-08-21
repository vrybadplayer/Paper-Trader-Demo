import React, { useState } from 'react';
import { BotSettings } from '../types';
import { Settings, X, Save, RotateCcw, Shield, DollarSign, Percent, Cpu, CheckCircle2, AlertCircle, FileCode, Radio, ExternalLink, Activity } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: BotSettings;
  onSaveSettings: (newSettings: BotSettings) => void;
  onResetDefaults: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSaveSettings,
  onResetDefaults,
}) => {
  const [cashReserve, setCashReserve] = useState<string>(settings.cashReserve.toString());
  const [initialBalance, setInitialBalance] = useState<string>(settings.initialBalance.toString());
  const [maxPositionSize, setMaxPositionSize] = useState<string>((settings.maxPositionSize * 100).toString());
  const [commissionPerTrade, setCommissionPerTrade] = useState<string>((settings.commissionPerTrade * 100).toString());
  const [workerModel, setWorkerModel] = useState<string>(settings.workerModel);
  const [criticModel, setCriticModel] = useState<string>(settings.criticModel);
  const [activeSubTab, setActiveSubTab] = useState<'editor' | 'alpaca_broker' | 'yaml_preview'>('editor');
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const reserveNum = parseFloat(cashReserve);
    const balanceNum = parseFloat(initialBalance);
    const maxPosNum = parseFloat(maxPositionSize) / 100;
    const commNum = parseFloat(commissionPerTrade) / 100;

    if (isNaN(reserveNum) || reserveNum < 0) {
      setErrorMsg('Cash Reserve floor must be a valid non-negative number.');
      return;
    }
    if (isNaN(balanceNum) || balanceNum < 0) {
      setErrorMsg('Starting Cash Balance must be a valid non-negative number.');
      return;
    }
    if (isNaN(maxPosNum) || maxPosNum <= 0 || maxPosNum > 1) {
      setErrorMsg('Max Position Size must be between 1% and 100%.');
      return;
    }
    if (isNaN(commNum) || commNum < 0) {
      setErrorMsg('Commission rate must be a valid percentage.');
      return;
    }

    setErrorMsg(null);
    const updated: BotSettings = {
      cashReserve: reserveNum,
      initialBalance: balanceNum,
      maxPositionSize: maxPosNum,
      commissionPerTrade: commNum,
      workerModel,
      criticModel,
    };

    onSaveSettings(updated);
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 900);
  };

  const handleReset = () => {
    onResetDefaults();
    setCashReserve('50000');
    setInitialBalance('52400');
    setMaxPositionSize('10');
    setCommissionPerTrade('0.1');
    setWorkerModel('deepseek-r1:14b');
    setCriticModel('deepseek-r1:14b');
    setErrorMsg(null);
  };

  // Generate live settings.yaml representation
  const generatedYaml = `# Auto-synchronized settings.yaml
model_routing:
  ollama_base_url: "http://localhost:11434"
  request_timeout: 60
  worker_engine:
    primary: "${workerModel}"
    cloud_fallback: "deepseek-r1:7b"
    temperature: 0.1
    mode: "System 1: Deep Quantitative Researcher"
  critic_engine:
    primary: "${criticModel}"
    cloud_fallback: "deepseek-r1:32b"
    temperature: 0.1
    mode: "System 2: Deep Chain-of-Thought Risk Auditor"

system:
  cash_reserve: ${parseFloat(cashReserve) || 0}  # Minimum cash reserve invariant floor (RM)
  max_position_size: ${(parseFloat(maxPositionSize) || 10) / 100}  # Max % of equity per position
  risk_free_rate: 0.03  # Bank Negara Malaysia OPR reference (3.00%)
  base_currency: "MYR"

broker:
  type: "moomoo"               # "moomoo" (FutuOpenD Bursa Gateway) or "bursa_sandbox"
  sandbox_enabled: true
  live_enabled: false          # set true to execute on Moomoo Malaysia Live
  host: "127.0.0.1"
  port: 11111
  market: "MY"                 # Bursa Malaysia
  security_firm: "FUTU_MY"     # Moomoo Securities Malaysia Sdn. Bhd.
  target_stocks:
    - symbol: "5238.KL"
      name: "CAPITAL A BHD (AAGB)"
    - symbol: "0138.KL"
      name: "MY E.G. SERVICES BHD (ZETRIX)"
    - symbol: "0459.KL"
      name: "SUPREME CONSOLIDATED BHD (SUM)"
    - symbol: "4677.KL"
      name: "YTL CORPORATION BHD (YTL)"
  lot_size: 100                # Bursa Malaysia standard 100-share lot
  shark_block_threshold_myr: 150000.0 # Institutional print flag (RM 150k+)
  sandbox_initial_balance: ${parseFloat(initialBalance) || 0}
  commission_per_trade: ${(parseFloat(commissionPerTrade) || 0.0) / 100}
  rate_limits:
    orders_per_30s: 15         # Strict Moomoo order limit
    order_inter_delay_s: 1.5   # Pacing delay between executions
    quote_qps_limit: 9.0       # Safe ceiling for 10 QPS quota
    klines_per_30s: 30         # K-Line historical fetch ceiling
    max_active_subscriptions: 100 # LRU auto-eviction capacity

chromadb:
  persist_directory: "./database/data/chroma_db"
  collection_name: "trading_memory"
  embedding_function: "default"

logging:
  level: "INFO"
  file: "./database/logs/trading_bot.log"`;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <Settings className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-100 flex items-center gap-2">
                Settings &amp; Broker Gateway
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-emerald-300 border border-slate-700">
                  Alpaca Paper / Sandbox
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Configure broker endpoints, institutional shark tape scanners, and risk floor limits
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

        {/* Sub Tabs */}
        <div className="flex border-b border-slate-800 bg-slate-950/60 px-6 gap-2 pt-2 text-xs">
          <button
            onClick={() => setActiveSubTab('editor')}
            className={`px-4 py-2 font-semibold rounded-t-lg transition flex items-center gap-2 border-b-2 cursor-pointer ${
              activeSubTab === 'editor'
                ? 'border-emerald-400 text-emerald-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Settings className="w-3.5 h-3.5" />
            Capital &amp; Risk
          </button>
          <button
            onClick={() => setActiveSubTab('alpaca_broker')}
            className={`px-4 py-2 font-semibold rounded-t-lg transition flex items-center gap-2 border-b-2 cursor-pointer ${
              activeSubTab === 'alpaca_broker'
                ? 'border-amber-400 text-amber-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            Bursa Malaysia (Moomoo / MYX)
          </button>
          <button
            onClick={() => setActiveSubTab('yaml_preview')}
            className={`px-4 py-2 font-semibold rounded-t-lg transition flex items-center gap-2 border-b-2 cursor-pointer ${
              activeSubTab === 'yaml_preview'
                ? 'border-indigo-400 text-indigo-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileCode className="w-3.5 h-3.5" />
            settings.yaml
          </button>
        </div>

        {/* Tab Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {errorMsg && (
            <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800/80 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
          )}

          {savedSuccess && (
            <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-800/80 text-emerald-300 text-xs flex items-center gap-2 animate-pulse">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
              <span>Configuration saved! Portfolio balance and reserve limit updated.</span>
            </div>
          )}

          {activeSubTab === 'editor' && (
            <form id="settings-form" onSubmit={handleSave} className="space-y-4 text-xs">
              {/* Cash & Reserve Section */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-3.5">
                <div className="flex items-center gap-2 text-slate-200 font-bold border-b border-slate-800/80 pb-2">
                  <DollarSign className="w-4 h-4 text-emerald-400" />
                  Account Balance &amp; Reserve Floor (Dynamic)
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-slate-300 font-semibold mb-1">
                      Account Cash Balance ($)
                    </label>
                    <div className="relative">
                      <span className="absolute left-3 top-2.5 text-slate-500 font-mono text-xs">$</span>
                      <input
                        type="number"
                        step="any"
                        value={initialBalance}
                        onChange={(e) => setInitialBalance(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-7 pr-3 py-2 text-slate-100 font-mono text-xs focus:outline-hidden focus:border-emerald-500"
                        placeholder="52400"
                        required
                      />
                    </div>
                    <span className="text-[10px] text-slate-400 mt-1 block">
                      Maps to <code>broker.sandbox_initial_balance</code>
                    </span>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1">
                      <Shield className="w-3.5 h-3.5 text-indigo-400" /> Cash Reserve Limit ($)
                    </label>
                    <div className="relative">
                      <span className="absolute left-3 top-2.5 text-slate-500 font-mono text-xs">$</span>
                      <input
                        type="number"
                        step="any"
                        value={cashReserve}
                        onChange={(e) => setCashReserve(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-7 pr-3 py-2 text-slate-100 font-mono text-xs focus:outline-hidden focus:border-indigo-500"
                        placeholder="50000"
                        required
                      />
                    </div>
                    <span className="text-[10px] text-slate-400 mt-1 block">
                      Maps to <code>system.cash_reserve</code> (Auditor floor)
                    </span>
                  </div>
                </div>

                {/* Live calculation banner */}
                <div className="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800 text-[11px] flex items-center justify-between text-slate-300 font-mono">
                  <span>Calculated Free Trading Capital:</span>
                  <span className="font-bold text-emerald-400">
                    ${Math.max(0, (parseFloat(initialBalance) || 0) - (parseFloat(cashReserve) || 0)).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              {/* Risk Limits & Position Constraints */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-3.5">
                <div className="flex items-center gap-2 text-slate-200 font-bold border-b border-slate-800/80 pb-2">
                  <Percent className="w-4 h-4 text-indigo-400" />
                  Risk Invariants &amp; Sizing Limits
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-slate-300 font-semibold mb-1">
                      Max Single Position Size (% of Equity)
                    </label>
                    <div className="relative">
                      <input
                        type="number"
                        step="0.5"
                        min="1"
                        max="100"
                        value={maxPositionSize}
                        onChange={(e) => setMaxPositionSize(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 font-mono text-xs focus:outline-hidden focus:border-emerald-500"
                        placeholder="10"
                        required
                      />
                      <span className="absolute right-3 top-2 text-slate-500 font-mono text-xs">%</span>
                    </div>
                    <span className="text-[10px] text-slate-400 mt-1 block">
                      Maps to <code>system.max_position_size</code>
                    </span>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-semibold mb-1">
                      Commission per Trade (%)
                    </label>
                    <div className="relative">
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={commissionPerTrade}
                        onChange={(e) => setCommissionPerTrade(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 font-mono text-xs focus:outline-hidden focus:border-emerald-500"
                        placeholder="0.0"
                        required
                      />
                      <span className="absolute right-3 top-2 text-slate-500 font-mono text-xs">%</span>
                    </div>
                    <span className="text-[10px] text-slate-400 mt-1 block">
                      0.0% on Alpaca US Equities
                    </span>
                  </div>
                </div>
              </div>

              {/* Models Selection */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-3.5">
                <div className="flex items-center gap-2 text-slate-200 font-bold border-b border-slate-800/80 pb-2">
                  <Cpu className="w-4 h-4 text-teal-400" />
                  Dual-Agent Model Configuration
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-slate-300 font-semibold mb-1">
                      Researcher Engine (Worker)
                    </label>
                    <select
                      value={workerModel}
                      onChange={(e) => setWorkerModel(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 font-mono text-xs focus:outline-hidden focus:border-emerald-500"
                    >
                      <option value="deepseek-r1:14b">deepseek-r1:14b (Unified)</option>
                      <option value="deepseek-r1:7b">deepseek-r1:7b (Lightweight)</option>
                      <option value="deepseek-r1:32b">deepseek-r1:32b (Ultra Deep)</option>
                      <option value="qwen2.5-coder:7b">qwen2.5-coder:7b</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-semibold mb-1">
                      Critic Auditor Engine (System 2)
                    </label>
                    <select
                      value={criticModel}
                      onChange={(e) => setCriticModel(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 font-mono text-xs focus:outline-hidden focus:border-indigo-500"
                    >
                      <option value="deepseek-r1:14b">deepseek-r1:14b (Unified)</option>
                      <option value="deepseek-r1:32b">deepseek-r1:32b (Max Precision)</option>
                      <option value="deepseek-r1:7b">deepseek-r1:7b (Fast Fallback)</option>
                    </select>
                  </div>
                </div>
              </div>
            </form>
          )}

          {activeSubTab === 'alpaca_broker' && (
            <div className="space-y-4 text-xs">
              <div className="bg-slate-950/80 p-4 rounded-xl border border-amber-500/30 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
                    <span className="font-bold text-slate-100 text-sm">Moomoo Malaysia (FutuOpenD) &amp; Bursa Malaysia Gateway</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] border border-amber-500/40">
                    Bursa Malaysia (MYX)
                  </span>
                </div>

                <p className="text-slate-300 leading-relaxed text-[11px]">
                  Moomoo Malaysia (Futu Securities) and IBKR provide licensed market access to <strong>Bursa Malaysia (KLSE)</strong> with real-time Level 2 Broker Queue, Tick-by-Tick Time &amp; Sales, Institutional Capital Inflow tracking, and free Simulated Paper Trading in <strong>Malaysian Ringgit (MYR)</strong>.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 font-mono text-[10px]">
                    <span className="text-slate-400 block">FutuOpenD Local Host &amp; Port:</span>
                    <span className="text-amber-300 font-semibold">127.0.0.1:11111</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 font-mono text-[10px]">
                    <span className="text-slate-400 block">Active Bursa Watchlist (4):</span>
                    <span className="text-emerald-300 font-semibold">5238 (AAGB), 0138 (ZETRIX), 0459 (SUM), 4677 (YTL)</span>
                  </div>
                </div>
              </div>

              {/* Moomoo Strict Rate Limit Compliance Engine */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-indigo-500/30 space-y-3">
                <div className="flex items-center gap-2 font-bold text-slate-200 border-b border-slate-800 pb-2">
                  <Shield className="w-4 h-4 text-indigo-400" />
                  Moomoo Strict Rate Limit &amp; Quota Safeguards
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 font-mono text-[10px]">
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-400 block">Order Throttle:</span>
                    <span className="text-amber-300 font-bold">15 orders / 30s</span>
                    <span className="text-slate-500 block text-[9px] mt-0.5">Enforces 1.5s inter-order pacing</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-400 block">Quote &amp; Snapshot QPS:</span>
                    <span className="text-emerald-300 font-bold">9.0 QPS Cap</span>
                    <span className="text-slate-500 block text-[9px] mt-0.5">Under official 10.0 QPS ceiling</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-400 block">Historical K-Line Quota:</span>
                    <span className="text-sky-300 font-bold">30 requests / 30s</span>
                    <span className="text-slate-500 block text-[9px] mt-0.5">Token bucket sliding window</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-400 block">Active Subscriptions:</span>
                    <span className="text-purple-300 font-bold">100 Symbols Max</span>
                    <span className="text-slate-500 block text-[9px] mt-0.5">LRU automatic unsubscription</span>
                  </div>
                </div>
              </div>

              {/* Shark Activity Detection Features for Malaysia */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-3">
                <div className="flex items-center gap-2 font-bold text-slate-200 border-b border-slate-800 pb-2">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  Bursa Malaysia Institutional Shark &amp; Whale Tracking
                </div>

                <ul className="space-y-2 text-slate-300 text-[11px]">
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">1.</span>
                    <span><strong>Super-Large Capital Inflow (Whale/Shark):</strong> Categorizes trades into Super-Large (&ge; RM 150,000 / &ge; 500 lots) vs Retail Flow.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">2.</span>
                    <span><strong>Level 2 Broker Queue:</strong> Reveals institutional buy/sell pressure across Bursa investment banks (Maybank IB, CIMB IB, Affin Hwang, Kenanga, RHB).</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">3.</span>
                    <span><strong>Standard 100-Share Lot Execution:</strong> Automatically formats and routes orders compliant with Bursa Malaysia 100-share lot rules.</span>
                  </li>
                </ul>
              </div>

              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
                <span>Moomoo Open API &amp; FutuOpenD Gateway:</span>
                <a
                  href="https://www.moomoo.com/en-my/download/OpenAPI"
                  target="_blank"
                  rel="noreferrer"
                  className="text-amber-400 hover:text-amber-300 underline flex items-center gap-1 font-mono"
                >
                  moomoo.com/en-my <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          )}

          {activeSubTab === 'yaml_preview' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Synchronized YAML representation of <code>trading_bot_core/config/settings.yaml</code></span>
                <span className="font-mono text-[10px] text-emerald-400">Live Mirror</span>
              </div>
              <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-[11px] text-emerald-300/90 overflow-x-auto leading-relaxed max-h-96">
                {generatedYaml}
              </pre>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between text-xs">
          <button
            type="button"
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Defaults ($50k)
          </button>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              form="settings-form"
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-md transition cursor-pointer"
            >
              <Save className="w-3.5 h-3.5" />
              Save &amp; Apply to Engine
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
