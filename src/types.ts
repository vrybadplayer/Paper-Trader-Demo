export type FsmState = 
  | 'IDLE' 
  | 'OBSERVING'
  | 'FETCHING_DATA' 
  | 'GENERATING_SIGNAL' 
  | 'VALIDATING_SIGNAL' 
  | 'EXECUTING_TRADE' 
  | 'UPDATING_STATE' 
  | 'ERROR' 
  | 'STOPPED';

export interface Position {
  ticker: string;
  quantity: number;
  avgCost: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnl: number;
  unrealizedPnlPct: number;
}

export interface Portfolio {
  cashBalance: number;
  reserveLimit: number;
  availableCash: number;
  totalEquity: number;
  realizedPnl: number;
  unrealizedPnl: number;
  positions: Position[];
}

export interface SharkActivity {
  ticker: string;
  type: 'WHALE_ACCUMULATION' | 'LIQUIDITY_SWEEP' | 'AGGRESSIVE_ABSORPTION' | 'DISTRIBUTION_BLOCK' | 'OBSERVING_NORMAL_FLOW';
  deltaVolume: number;
  intensity: 'LOW' | 'MEDIUM' | 'HIGH' | 'EXTREME';
  detected: boolean;
  notes: string;
  timestamp: string;
}

export interface IndicatorSnapshot {
  rsi: number;
  macd: number;
  macdSignal: number;
  bollingerUpper: number;
  bollingerLower: number;
  currentPrice: number;
  priceChangePct: number;
  volume24h: number;
  sharkActivity?: SharkActivity;
}

export interface TradeSignal {
  id: string;
  ticker: string;
  action: 'BUY' | 'SELL' | 'HOLD';
  quantity: number;
  currentPrice: number;
  targetPrice: number;
  stopLoss: number;
  takeProfit: number;
  confidence: number;
  timestamp: string;
  source: string;
  rationale: string;
  sharkPatternTriggered?: string;
  historicalPnlContext?: string;
}

export interface RiskAudit {
  id: string;
  signalId: string;
  ticker: string;
  action: 'BUY' | 'SELL' | 'HOLD';
  approved: boolean;
  violations: string[];
  originalQuantity: number;
  adjustedQuantity: number;
  thinking: string;
  reason: string;
  timestamp: string;
  model: string;
  historicalTraceCheck?: string;
}

export interface ExecutedTrade {
  id: string;
  ticker: string;
  action: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  timestamp: string;
  commission: number;
  totalCost: number;
  realizedPnl?: number;
  pnlPercentage?: number;
  holdingPeriodMinutes?: number;
  exitReason?: string;
  status: 'FILLED' | 'REJECTED';
}

export interface PostMortemAutopsy {
  id: string;
  ticker: string;
  tradeId: string;
  lossAmount: number;
  lossPct: number;
  exitPrice: number;
  entryPrice: number;
  initialThesis: string;
  rootCause: string;
  breakdown: string;
  lessonLearned: string;
  guardrailRule: string;
  failureTag: 'FAKE_ABSORPTION_TRAP' | 'MACRO_RESISTANCE_COLLISION' | 'PREMATURE_BREAKOUT' | 'MOMENTUM_EXHAUSTION' | 'OVERSIZED_FOMO';
  timestamp: string;
  chromaEmbedded: boolean;
  criticModel: string;
}

export interface ChromaMemoryItem {
  id: string;
  topic: string;
  content: string;
  category: 'post_mortem_loss' | 'shark_pattern' | 'market_structure' | 'behavioral_trap' | 'risk_invariant';
  ticker?: string;
  similarity?: number;
  timestamp: string;
}

export interface BotSettings {
  cashReserve: number;
  initialBalance: number;
  maxPositionSize: number;
  commissionPerTrade: number;
  workerModel: string;
  criticModel: string;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'SYSTEM' | 'CRITIC' | 'WORKER' | 'OBSERVER';
  component: string;
  message: string;
  details?: any;
}
