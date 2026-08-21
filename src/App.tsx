import React, { useState, useEffect } from 'react';
import { FsmState, Portfolio, IndicatorSnapshot, TradeSignal, RiskAudit, ExecutedTrade, LogEntry, SharkActivity, PostMortemAutopsy, BotSettings } from './types';
import { Header } from './components/Header';
import { OrchestratorPanel } from './components/OrchestratorPanel';
import { WorkerCard } from './components/WorkerCard';
import { CriticCard } from './components/CriticCard';
import { PortfolioLedger } from './components/PortfolioLedger';
import { PersonaViewerModal } from './components/PersonaViewerModal';
import { SettingsModal } from './components/SettingsModal';
import { INITIAL_AUTOPSIES } from './data/personaData';

const DEFAULT_SETTINGS: BotSettings = {
  cashReserve: 30000.0,
  initialBalance: 100000.0,
  maxPositionSize: 0.15,
  commissionPerTrade: 0.0015,
  workerModel: 'deepseek-r1:14b',
  criticModel: 'deepseek-r1:14b',
};

const INITIAL_PORTFOLIO: Portfolio = {
  cashBalance: DEFAULT_SETTINGS.initialBalance,
  reserveLimit: DEFAULT_SETTINGS.cashReserve,
  availableCash: Math.max(0, DEFAULT_SETTINGS.initialBalance - DEFAULT_SETTINGS.cashReserve),
  totalEquity: DEFAULT_SETTINGS.initialBalance,
  realizedPnl: 0.0,
  unrealizedPnl: 0.0,
  positions: [],
};

const TICKERS = ['5238.KL', '0138.KL', '0459.KL', '4677.KL', '1155.KL'];

const TICKER_META: Record<string, { name: string; symbol: string; sector: string }> = {
  '5238.KL': { name: 'Capital A Bhd (AirAsia)', symbol: 'AAGB', sector: 'Aviation & Consumer' },
  '0138.KL': { name: 'MY E.G. Services Bhd', symbol: 'ZETRIX', sector: 'Digital Services & Web3' },
  '0459.KL': { name: 'Supreme Consolidated Bhd', symbol: 'SUM', sector: 'Food Logistics & F&B' },
  '4677.KL': { name: 'YTL Corporation Bhd', symbol: 'YTL', sector: 'Utilities & Infrastructure' },
  '1155.KL': { name: 'Malayan Banking Bhd', symbol: 'MAYBANK', sector: 'Financial Services' },
};

const BASE_PRICES: Record<string, number> = {
  '5238.KL': 0.785,
  '0138.KL': 0.945,
  '0459.KL': 0.485,
  '4677.KL': 2.960,
  '1155.KL': 10.20,
};

export default function App() {
  const [fsmState, setFsmState] = useState<FsmState>('IDLE');
  const [activeTicker, setActiveTicker] = useState<string>('5238.KL');
  const [isAutoRunning, setIsAutoRunning] = useState<boolean>(false);
  const [isPersonaModalOpen, setIsPersonaModalOpen] = useState<boolean>(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState<boolean>(false);
  const [botSettings, setBotSettings] = useState<BotSettings>(DEFAULT_SETTINGS);
  const [ollamaConnected, setOllamaConnected] = useState<boolean>(true);
  const [cyclesObserved, setCyclesObserved] = useState<number>(0);
  const [sharkTriggersCount, setSharkTriggersCount] = useState<number>(0);

  // Indicators state for active ticker with shark activity detection
  const [indicators, setIndicators] = useState<IndicatorSnapshot>({
    rsi: 52.4,
    macd: 0.015,
    macdSignal: 0.011,
    bollingerUpper: 0.810,
    bollingerLower: 0.760,
    currentPrice: BASE_PRICES['5238.KL'],
    priceChangePct: 0.64,
    volume24h: 8500000,
    sharkActivity: {
      ticker: '5238.KL',
      type: 'OBSERVING_NORMAL_FLOW',
      deltaVolume: 1200,
      intensity: 'LOW',
      detected: false,
      notes: 'Normal Bursa Malaysia retail churn. No institutional blocks or stop runs detected.',
      timestamp: new Date().toISOString(),
    },
  });

  // Portfolio and historical ledger
  const [portfolio, setPortfolio] = useState<Portfolio>(INITIAL_PORTFOLIO);
  const [tradeLedger, setTradeLedger] = useState<ExecutedTrade[]>([
    {
      id: 'trd-seed-1',
      ticker: '5238.KL',
      action: 'BUY',
      quantity: 2000,
      price: 0.770,
      timestamp: new Date(Date.now() - 3600000 * 4).toISOString(),
      commission: 8.00,
      totalCost: 1540.0,
      status: 'FILLED',
    },
    {
      id: 'trd-seed-2',
      ticker: '5238.KL',
      action: 'SELL',
      quantity: 2000,
      price: 0.795,
      timestamp: new Date(Date.now() - 3600000 * 2).toISOString(),
      commission: 8.00,
      totalCost: 1590.0,
      realizedPnl: 34.00,
      pnlPercentage: 2.20,
      holdingPeriodMinutes: 120,
      exitReason: 'Take profit hit on resistance test',
      status: 'FILLED',
    }
  ]);

  // ChromaDB Post-Mortem Autopsies
  const [autopsies, setAutopsies] = useState<PostMortemAutopsy[]>(INITIAL_AUTOPSIES);

  const [latestSignal, setLatestSignal] = useState<TradeSignal | null>(null);
  const [latestAudit, setLatestAudit] = useState<RiskAudit | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: 'log-0',
      timestamp: new Date().toISOString(),
      level: 'SYSTEM',
      component: 'Orchestrator',
      message: 'Dual-Agent Trading Engine online. Worker & Critic routed to DeepSeek-R1 14B.',
    },
    {
      id: 'log-1',
      timestamp: new Date().toISOString(),
      level: 'WORKER',
      component: 'GeneratorWorker',
      message: 'Researcher Quinn: Low-aggression patience mode active. Checking ChromaDB loss autopsies before proposing trades.',
    },
    {
      id: 'log-2',
      timestamp: new Date().toISOString(),
      level: 'CRITIC',
      component: 'CriticAuditor',
      message: `Auditor Morgan: ChromaDB Post-Mortem Self-Reflection Engine active (${INITIAL_AUTOPSIES.length} past autopsies loaded).`,
    },
  ]);

  const addLog = (level: LogEntry['level'], component: string, message: string) => {
    setLogs((prev) => [
      {
        id: `log-${Date.now()}-${Math.random()}`,
        timestamp: new Date().toISOString(),
        level,
        component,
        message,
      },
      ...prev.slice(0, 99),
    ]);
  };

  // Helper: Get historical PnL summary for the given ticker
  const getHistoricalPnlSummary = (ticker: string) => {
    const tickerTrades = tradeLedger.filter((t) => t.ticker === ticker);
    const closed = tickerTrades.filter((t) => t.realizedPnl !== undefined);
    const tickerAutopsies = autopsies.filter((a) => a.ticker === ticker);
    
    let base = closed.length === 0 
      ? `0 closed trades on ${ticker}.` 
      : `${closed.length} closed trades, Cumulative P&L: $${closed.reduce((acc, t) => acc + (t.realizedPnl || 0), 0).toFixed(2)}.`;

    if (tickerAutopsies.length > 0) {
      base += ` ChromaDB Autopsy Recall: ${tickerAutopsies.length} past failure (${tickerAutopsies[0].failureTag}: "${tickerAutopsies[0].lessonLearned}").`;
    }
    return base;
  };

  // Trigger simulated loss autopsy with DeepSeek-R1 reasoning
  const handleTriggerSimulatedAutopsy = () => {
    const ticker = activeTicker;
    const loss = Math.floor(22 + Math.random() * 25) + 0.40;
    const lossPct = 1.8 + Math.random() * 1.5;
    const curPrice = BASE_PRICES[ticker] || 200.0;
    const entryPrice = curPrice * (1 + lossPct / 100);

    const failureTags: PostMortemAutopsy['failureTag'][] = [
      'FAKE_ABSORPTION_TRAP',
      'MACRO_RESISTANCE_COLLISION',
      'PREMATURE_BREAKOUT',
      'MOMENTUM_EXHAUSTION',
    ];
    const chosenTag = failureTags[Math.floor(Math.random() * failureTags.length)];

    const lessonsMap: Record<PostMortemAutopsy['failureTag'], { root: string; lesson: string; guard: string }> = {
      FAKE_ABSORPTION_TRAP: {
        root: `Spoof bid depth vanished upon fill on ${ticker}. Smart money distributed into retail longs.`,
        lesson: `Inspect multi-level Level-2 book persistence rather than single top-of-book bids.`,
        guard: `Require 3-bar CVD continuation before validating iceberg absorption on ${ticker}.`,
      },
      MACRO_RESISTANCE_COLLISION: {
        root: `Long entry executed 0.4% below major 4-Hour supply zone on ${ticker}. Opposing macro block rejected price.`,
        lesson: `Do not enter breakout longs within 1.5% of HTF (Higher Timeframe) key resistance.`,
        guard: `Reject all long signals when HTF supply overhang is within 1.5x expected ATR.`,
      },
      PREMATURE_BREAKOUT: {
        root: `Entered on first 1m momentum spike without waiting for 5m delta volume confirmation on ${ticker}.`,
        lesson: `Allow swing highs to be tested and absorbed with positive delta before entry.`,
        guard: `Enforce minimum +30,000 delta volume expansion before clearing breakout trades.`,
      },
      MOMENTUM_EXHAUSTION: {
        root: `RSI divergence at extreme overbought levels on ${ticker}. Volume dried up at local peak.`,
        lesson: `Avoid buying into late-stage trend runs when buy volume delta is declining.`,
        guard: `Cap entries when RSI > 72 and volume delta is lower than prior 3 bars.`,
      },
      OVERSIZED_FOMO: {
        root: `Position size exceeded conservative limits during volatility surge on ${ticker}.`,
        lesson: `Never scale position size based on emotional excitement.`,
        guard: `Hard cap sizing at 25% of available free cash above configured reserve limit.`,
      },
    };

    const details = lessonsMap[chosenTag];

    const newAutopsy: PostMortemAutopsy = {
      id: `autopsy-${Date.now()}`,
      ticker,
      tradeId: `trd-loss-${Date.now()}`,
      lossAmount: loss,
      lossPct,
      entryPrice,
      exitPrice: curPrice,
      initialThesis: `Quinn had proposed long setup on ${ticker} anticipating trend continuation.`,
      rootCause: `${chosenTag}: ${details.root}`,
      breakdown: `DeepSeek-R1 Post-Mortem Diagnosis: Stop-loss was hit at $${curPrice.toFixed(2)}. ${details.root} The system exited immediately, preserving capital and avoiding further drawdown. Lesson synthesized into ChromaDB HNSW index.`,
      lessonLearned: details.lesson,
      guardrailRule: details.guard,
      failureTag: chosenTag,
      timestamp: new Date().toISOString(),
      chromaEmbedded: true,
      criticModel: botSettings.criticModel,
    };

    setAutopsies((prev) => [newAutopsy, ...prev]);

    // Also record the closed loss in the ledger
    const lossTrade: ExecutedTrade = {
      id: `trd-loss-exec-${Date.now()}`,
      ticker,
      action: 'SELL',
      quantity: 3,
      price: curPrice,
      timestamp: new Date().toISOString(),
      commission: 0.65,
      totalCost: curPrice * 3,
      realizedPnl: -loss,
      pnlPercentage: -lossPct,
      holdingPeriodMinutes: 45,
      exitReason: `Stop-loss hit: ${chosenTag}`,
      status: 'FILLED',
    };

    setTradeLedger((prev) => [lossTrade, ...prev]);

    // Update portfolio realized PnL
    setPortfolio((prev) => ({
      ...prev,
      cashBalance: prev.cashBalance - loss,
      availableCash: Math.max(0, prev.cashBalance - loss - prev.reserveLimit),
      totalEquity: prev.totalEquity - loss,
      realizedPnl: prev.realizedPnl - loss,
    }));

    addLog('CRITIC', 'CriticAuditor', `[ChromaDB Post-Mortem Autopsy] Dissected -$${loss.toFixed(2)} loss on ${ticker}. Failure tag: ${chosenTag}. Saved new invariant to vector store.`);
  };

  // Handler: Save settings from modal and update portfolio & configuration
  const handleSaveSettings = (newSettings: BotSettings) => {
    setBotSettings(newSettings);
    setPortfolio((prev) => {
      const newBalance = newSettings.initialBalance;
      const newReserve = newSettings.cashReserve;
      const totalMarketValue = prev.positions.reduce((acc, p) => acc + p.marketValue, 0);
      return {
        ...prev,
        cashBalance: newBalance,
        reserveLimit: newReserve,
        availableCash: Math.max(0, newBalance - newReserve),
        totalEquity: newBalance + totalMarketValue,
      };
    });
    addLog(
      'SYSTEM',
      'Orchestrator',
      `Configuration updated: Cash Balance = $${newSettings.initialBalance.toLocaleString()}, Reserve Floor = $${newSettings.cashReserve.toLocaleString()}, Max Pos Size = ${(newSettings.maxPositionSize * 100).toFixed(0)}%.`
    );
  };

  const handleResetSettings = () => {
    handleSaveSettings(DEFAULT_SETTINGS);
  };

  // Run a single full FSM cycle
  const runCycle = async () => {
    if (fsmState !== 'IDLE' && fsmState !== 'STOPPED') return;

    try {
      setCyclesObserved((c) => c + 1);

      // Step 1: FETCHING_DATA
      setFsmState('FETCHING_DATA');
      addLog('SYSTEM', 'Orchestrator', `[Step 1] Fetching live order flow & querying ChromaDB autopsies for ${activeTicker}...`);

      const priceVariation = (Math.random() - 0.48) * 2.5;
      const curPrice = Math.max(10, BASE_PRICES[activeTicker] + priceVariation);
      const newRsi = Math.max(15, Math.min(85, 30 + Math.random() * 45));
      const newMacd = (Math.random() - 0.45) * 2.5;

      const availableTradingCash = Math.max(0, portfolio.cashBalance - portfolio.reserveLimit);
      const existingPosition = portfolio.positions.find((p) => p.ticker === activeTicker);

      // Check if there are past autopsies on this ticker in ChromaDB
      const tickerAutopsies = autopsies.filter((a) => a.ticker === activeTicker);

      // Shark Activity Random Generator
      // Toned-down aggression: ~85% observing, only ~15% high-probability shark footprints
      const sharkRoll = Math.random();
      let sharkActivity: SharkActivity;

      if (sharkRoll < 0.08) {
        sharkActivity = {
          ticker: activeTicker,
          type: 'WHALE_ACCUMULATION',
          deltaVolume: Math.floor(55000 + Math.random() * 90000),
          intensity: 'HIGH',
          detected: true,
          notes: 'High-conviction iceberg absorption at structural support. Cumulative volume delta is strongly positive (+institutional footprint).',
          timestamp: new Date().toISOString(),
        };
      } else if (sharkRoll < 0.15) {
        sharkActivity = {
          ticker: activeTicker,
          type: 'LIQUIDITY_SWEEP',
          deltaVolume: Math.floor(40000 + Math.random() * 60000),
          intensity: 'EXTREME',
          detected: true,
          notes: 'Key swing low was aggressively swept triggering retail stops, followed by immediate V-shape institutional absorption.',
          timestamp: new Date().toISOString(),
        };
      } else if (sharkRoll < 0.22 && existingPosition && existingPosition.quantity > 0) {
        sharkActivity = {
          ticker: activeTicker,
          type: 'DISTRIBUTION_BLOCK',
          deltaVolume: -Math.floor(45000 + Math.random() * 60000),
          intensity: 'HIGH',
          detected: true,
          notes: 'Institutional sell blocks capping overhead liquidity. Smart money distributing into retail bids.',
          timestamp: new Date().toISOString(),
        };
      } else {
        sharkActivity = {
          ticker: activeTicker,
          type: 'OBSERVING_NORMAL_FLOW',
          deltaVolume: Math.floor((Math.random() - 0.5) * 6000),
          intensity: 'LOW',
          detected: false,
          notes: 'Quiet tape. Retail flow is balanced without institutional absorption. Sitting on hands in pure observation mode.',
          timestamp: new Date().toISOString(),
        };
      }

      const newSnap: IndicatorSnapshot = {
        rsi: newRsi,
        macd: newMacd,
        macdSignal: newMacd * 0.8,
        bollingerUpper: curPrice * 1.025,
        bollingerLower: curPrice * 0.975,
        currentPrice: curPrice,
        priceChangePct: (priceVariation / curPrice) * 100,
        volume24h: Math.floor(3500000 + Math.random() * 2000000),
        sharkActivity,
      };
      setIndicators(newSnap);

      await new Promise((r) => setTimeout(r, 600));

      // Step 2: OBSERVATION CHECK (High threshold discipline)
      if (!sharkActivity.detected) {
        setFsmState('OBSERVING');
        addLog(
          'OBSERVER',
          'GeneratorWorker',
          `[Observation Discipline] ${activeTicker}: Tape reading in progress. No shark footprint detected. Sitting patiently (0 forced trades).`
        );
        await new Promise((r) => setTimeout(r, 800));
        setFsmState('IDLE');
        return;
      }

      // Pre-flight check inside Worker:
      const canAffordOneShare = availableTradingCash >= curPrice;
      if (!canAffordOneShare && sharkActivity.type !== 'DISTRIBUTION_BLOCK') {
        setFsmState('OBSERVING');
        addLog(
          'OBSERVER',
          'GeneratorWorker',
          `[Budget Self-Guard] Available cash above $${portfolio.reserveLimit.toLocaleString()} reserve is $${availableTradingCash.toFixed(2)} (< $${curPrice.toFixed(2)} for 1 share of ${activeTicker}). Quinn holds off to protect capital.`
        );
        await new Promise((r) => setTimeout(r, 800));
        setFsmState('IDLE');
        return;
      }

      // Shark activity confirmed & budget is healthy!
      setSharkTriggersCount((s) => s + 1);
      setFsmState('GENERATING_SIGNAL');
      addLog(
        'WORKER',
        'GeneratorWorker',
        `[Shark Setup: ${sharkActivity.type}] Quinn synthesizing thesis with ChromaDB past loss recall...`
      );

      let action: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
      let rationale = '';
      let calculatedQuantity = 0;

      const pnlContext = getHistoricalPnlSummary(activeTicker);

      if (sharkActivity.type === 'WHALE_ACCUMULATION' || sharkActivity.type === 'LIQUIDITY_SWEEP') {
        action = 'BUY';
        // Conservative Sizing: 10% to 25% of available cash above reserve
        const budgetToDeploy = availableTradingCash * 0.25; 
        const affordableShares = Math.floor(budgetToDeploy / curPrice);
        calculatedQuantity = Math.max(1, Math.min(affordableShares, 5));

        const memoryGuard = tickerAutopsies.length > 0 
          ? ` [ChromaDB Recall: ${tickerAutopsies[0].guardrailRule}]` 
          : '';

        rationale = `[High-Conviction Shark Setup] ${sharkActivity.type} (+${sharkActivity.deltaVolume.toLocaleString()} delta vol) confirmed at $${curPrice.toFixed(2)}. RSI: ${newRsi.toFixed(1)}.${memoryGuard} Sized cautiously at ${calculatedQuantity} shares ($${(calculatedQuantity * curPrice).toFixed(2)}) to maintain $${portfolio.reserveLimit.toLocaleString()} reserve buffer with $${(availableTradingCash - calculatedQuantity * curPrice).toFixed(2)} leftover.`;
      } else if (sharkActivity.type === 'DISTRIBUTION_BLOCK' && existingPosition) {
        action = 'SELL';
        calculatedQuantity = existingPosition.quantity;
        rationale = `[Shark Signal: Institutional Distribution] Sell blocks capping overhead liquidity. Locking in gains and reducing position risk on ${activeTicker}. Historical ledger context: "${pnlContext}".`;
      } else {
        action = 'HOLD';
        calculatedQuantity = 0;
        rationale = `Tape is neutral. Maintaining disciplined holding posture.`;
      }

      if (action === 'HOLD' || calculatedQuantity === 0) {
        setFsmState('OBSERVING');
        addLog('OBSERVER', 'GeneratorWorker', `Quinn determined risk-reward does not warrant capital deployment on ${activeTicker}. Holding.`);
        await new Promise((r) => setTimeout(r, 700));
        setFsmState('IDLE');
        return;
      }

      const signal: TradeSignal = {
        id: `sig-${Date.now()}`,
        ticker: activeTicker,
        action,
        quantity: calculatedQuantity,
        currentPrice: curPrice,
        targetPrice: action === 'BUY' ? curPrice * 1.045 : curPrice * 0.955,
        stopLoss: action === 'BUY' ? curPrice * 0.975 : curPrice * 1.025,
        takeProfit: action === 'BUY' ? curPrice * 1.065 : curPrice * 0.935,
        confidence: 0.92,
        timestamp: new Date().toISOString(),
        source: `worker_llm_${botSettings.workerModel}`,
        rationale,
        sharkPatternTriggered: sharkActivity.type,
        historicalPnlContext: pnlContext,
      };
      setLatestSignal(signal);

      await new Promise((r) => setTimeout(r, 700));

      // Step 3: VALIDATING_SIGNAL with Critic Auditor (DeepSeek-R1)
      setFsmState('VALIDATING_SIGNAL');
      addLog('CRITIC', 'CriticAuditor', `Morgan (${botSettings.criticModel}) auditing proposed ${action} order & ChromaDB loss autopsies...`);

      const totalCost = signal.quantity * curPrice;
      const maxAllowedPosition = portfolio.totalEquity * botSettings.maxPositionSize;

      const violations: string[] = [];
      let approved = true;
      let adjustedQty = signal.quantity;

      if (action === 'BUY' && totalCost > availableTradingCash) {
        violations.push(`Cash reserve floor invariant: trade cost $${totalCost.toFixed(2)} exceeds available capital $${Math.max(0, availableTradingCash).toFixed(2)} above $${portfolio.reserveLimit.toLocaleString()} reserve.`);
        approved = false;
        adjustedQty = Math.max(0, Math.floor(availableTradingCash / curPrice));
      }

      if (totalCost > maxAllowedPosition) {
        violations.push(`${(botSettings.maxPositionSize * 100).toFixed(0)}% position limit: $${totalCost.toFixed(2)} exceeds $${maxAllowedPosition.toFixed(2)}.`);
        adjustedQty = Math.min(adjustedQty, Math.max(0, Math.floor(maxAllowedPosition / curPrice)));
      }

      const thinking = `<think>
1. Auditor Check on Ticker: ${signal.ticker} proposed ${action} ${signal.quantity} shares @ $${curPrice.toFixed(2)} (Total: $${totalCost.toFixed(2)}).
2. ChromaDB Autopsy Cross-Check: Verified ${tickerAutopsies.length} past loss reflections on ${activeTicker}. Setup adheres to guardrail invariants.
3. Shark Footprint Validation: Verified ${sharkActivity.type} with delta volume ${sharkActivity.deltaVolume.toLocaleString()} shares.
4. Capital Preservation & Sizing: Proposed cost $${totalCost.toFixed(2)} is well within available liquid capital $${availableTradingCash.toFixed(2)} above $${portfolio.reserveLimit.toLocaleString()} reserve floor.
5. Invariant Verdict: ${approved ? 'Passes all hard constraints. Sizing is conservative and compliant. Approve trade execution.' : 'Violates reserve limit. Reduce/Reject.'}
</think>`;

      const audit: RiskAudit = {
        id: `audit-${Date.now()}`,
        signalId: signal.id,
        ticker: signal.ticker,
        action: signal.action,
        approved,
        violations,
        originalQuantity: signal.quantity,
        adjustedQuantity: adjustedQty,
        thinking,
        reason: approved ? `Trade validated against ChromaDB loss memories and verified ${sharkActivity.type} footprint. Sizing is conservative.` : `Rejected: ${violations.join('; ')}`,
        timestamp: new Date().toISOString(),
        model: botSettings.criticModel,
        historicalTraceCheck: pnlContext,
      };
      setLatestAudit(audit);
      addLog('CRITIC', 'CriticAuditor', `Risk Audit Verdict: ${approved ? 'APPROVED' : 'REJECTED'} (Adjusted Qty: ${adjustedQty})`);

      await new Promise((r) => setTimeout(r, 700));

      // Step 4: EXECUTING_TRADE (if approved)
      if (approved && adjustedQty > 0) {
        setFsmState('EXECUTING_TRADE');
        addLog('SYSTEM', 'BrokerGateway', `Routing approved ${action} order (${adjustedQty} ${activeTicker} @ $${curPrice.toFixed(2)}) to Sandbox Broker...`);

        let realizedPnl: number | undefined = undefined;
        let pnlPercentage: number | undefined = undefined;
        let exitReason: string | undefined = undefined;

        if (action === 'SELL' && existingPosition) {
          const sellQty = Math.min(existingPosition.quantity, adjustedQty);
          realizedPnl = (curPrice - existingPosition.avgCost) * sellQty - (curPrice * sellQty * botSettings.commissionPerTrade);
          pnlPercentage = ((curPrice - existingPosition.avgCost) / existingPosition.avgCost) * 100;
          exitReason = `Shark distribution exit at $${curPrice.toFixed(2)}`;
        }

        const execTrade: ExecutedTrade = {
          id: `trd-${Date.now()}`,
          ticker: activeTicker,
          action: action === 'BUY' ? 'BUY' : 'SELL',
          quantity: adjustedQty,
          price: curPrice,
          timestamp: new Date().toISOString(),
          commission: curPrice * adjustedQty * botSettings.commissionPerTrade,
          totalCost: curPrice * adjustedQty,
          realizedPnl,
          pnlPercentage,
          exitReason,
          status: 'FILLED',
        };

        setTradeLedger((prev) => [execTrade, ...prev]);

        // Step 5: UPDATING_STATE (Sync Portfolio & Ledger)
        setFsmState('UPDATING_STATE');
        setPortfolio((prev) => {
          let newCash = prev.cashBalance;
          let newPositions = [...prev.positions];
          let newRealized = prev.realizedPnl;

          if (action === 'BUY') {
            newCash -= execTrade.totalCost + execTrade.commission;
            const pos = newPositions.find((p) => p.ticker === activeTicker);
            if (pos) {
              const tot = pos.quantity + adjustedQty;
              const newAvg = (pos.quantity * pos.avgCost + execTrade.totalCost) / tot;
              pos.quantity = tot;
              pos.avgCost = newAvg;
              pos.currentPrice = curPrice;
              pos.marketValue = tot * curPrice;
              pos.unrealizedPnl = (curPrice - newAvg) * tot;
              pos.unrealizedPnlPct = ((curPrice - newAvg) / newAvg) * 100;
            } else {
              newPositions.push({
                ticker: activeTicker,
                quantity: adjustedQty,
                avgCost: curPrice,
                currentPrice: curPrice,
                marketValue: adjustedQty * curPrice,
                unrealizedPnl: 0,
                unrealizedPnlPct: 0,
              });
            }
          } else if (action === 'SELL') {
            newCash += execTrade.totalCost - execTrade.commission;
            if (realizedPnl !== undefined) {
              newRealized += realizedPnl;
            }
            newPositions = newPositions.filter((p) => p.ticker !== activeTicker);
          }

          const totalMarketValue = newPositions.reduce((acc, p) => acc + p.marketValue, 0);
          const totalUnrealized = newPositions.reduce((acc, p) => acc + p.unrealizedPnl, 0);
          const totalEq = newCash + totalMarketValue;

          return {
            ...prev,
            cashBalance: newCash,
            availableCash: Math.max(0, newCash - prev.reserveLimit),
            totalEquity: totalEq,
            realizedPnl: newRealized,
            unrealizedPnl: totalUnrealized,
            positions: newPositions,
          };
        });

        addLog(
          'SYSTEM',
          'TransactionLedger',
          `Trade committed to append-only JSONL ledger and embedded into ChromaDB HNSW memory.`
        );

        await new Promise((r) => setTimeout(r, 500));
      }

      setFsmState('IDLE');
    } catch (err: any) {
      console.error(err);
      setFsmState('ERROR');
      addLog('ERROR', 'Orchestrator', `Cycle execution failure: ${err?.message || err}`);
      setTimeout(() => setFsmState('IDLE'), 2000);
    }
  };

  // Auto-run loop timer
  useEffect(() => {
    let timer: any = null;
    if (isAutoRunning) {
      timer = setInterval(() => {
        if (fsmState === 'IDLE' || fsmState === 'STOPPED') {
          // Cycle through watchlist tickers
          setActiveTicker((prev) => {
            const nextIdx = (TICKERS.indexOf(prev) + 1) % TICKERS.length;
            return TICKERS[nextIdx];
          });
          runCycle();
        }
      }, 3500);
    }
    return () => clearInterval(timer);
  }, [isAutoRunning, fsmState]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-slate-950">
      {/* Top Navigation */}
      <Header
        fsmState={fsmState}
        isAutoRunning={isAutoRunning}
        onToggleAutoRun={() => setIsAutoRunning(!isAutoRunning)}
        onRunCycle={runCycle}
        onOpenPersonas={() => setIsPersonaModalOpen(true)}
        onOpenSettings={() => setIsSettingsModalOpen(true)}
        ollamaConnected={ollamaConnected}
      />

      {/* Main Workspace */}
      <main className="flex-1 p-4 lg:p-6 max-w-7xl mx-auto w-full flex flex-col gap-5">
        {/* Orchestrator FSM Pipeline Panel */}
        <OrchestratorPanel
          currentState={fsmState}
          activeTicker={activeTicker}
          onSelectTicker={(t) => setActiveTicker(t)}
          tickers={TICKERS}
          cyclesObserved={cyclesObserved}
          sharkTriggersCount={sharkTriggersCount}
        />

        {/* Dual Agent Cards (Researcher & Critic) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-stretch">
          <WorkerCard
            activeTicker={activeTicker}
            indicators={indicators}
            latestSignal={latestSignal}
            isGenerating={fsmState === 'GENERATING_SIGNAL'}
            isObserving={fsmState === 'OBSERVING'}
            historicalPnlSummary={getHistoricalPnlSummary(activeTicker)}
          />

          <CriticCard
            latestAudit={latestAudit}
            pendingSignal={latestSignal}
            isValidating={fsmState === 'VALIDATING_SIGNAL'}
            historicalPnlSummary={getHistoricalPnlSummary(activeTicker)}
            autopsies={autopsies}
            onTriggerSimulatedAutopsy={handleTriggerSimulatedAutopsy}
            reserveLimit={portfolio.reserveLimit}
            maxPosPct={botSettings.maxPositionSize * 100}
          />
        </div>

        {/* Portfolio, Earn/Loss Audit Ledger & Real-Time Logs */}
        <PortfolioLedger
          portfolio={portfolio}
          trades={tradeLedger}
          logs={logs}
          autopsies={autopsies}
          onTriggerSimulatedAutopsy={handleTriggerSimulatedAutopsy}
        />
      </main>

      {/* Persona and Invariants Modal */}
      {isPersonaModalOpen && (
        <PersonaViewerModal onClose={() => setIsPersonaModalOpen(false)} />
      )}

      {/* Settings Modal (Adjustable settings.yaml configurations) */}
      {isSettingsModalOpen && (
        <SettingsModal
          settings={botSettings}
          onSave={handleSaveSettings}
          onClose={() => setIsSettingsModalOpen(false)}
          onReset={handleResetSettings}
        />
      )}
    </div>
  );
}
