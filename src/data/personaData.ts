export const RESEARCHER_PERSONA = {
  name: "Quinn",
  title: "Finance Investment Researcher (Worker Agent - System 1)",
  model: "deepseek-r1:14b",
  role: "Patience-Driven Alpha Hunting, Shark Footprints & Strict Capital Sizing",
  temperature: 0.1,
  badgeColor: "emerald",
  corePrinciples: [
    "Capital-Aware Sizing: Never blindly propose large fixed share blocks. Calculate trade value against available cash above configured reserve (max 2-5% of available budget per trade)",
    "Patience & High-Threshold Setup: 90%+ of loop cycles are spent in quiet Observation & Tape Reading rather than forcing trades",
    "Shark Activity Confirmation: Only trigger orders when genuine institutional footprints (Whale Accumulation / Liquidity Sweeps) are detected with verified delta expansion",
    "Historical PnL Traceback: Consult past win/loss records on the ticker before formulating new entries to avoid revenge-trading",
    "Self-Preflight Audit: If available trading cash is insufficient for even 1 share without breaching the configured cash reserve floor, output HOLD instead of a failing BUY"
  ],
  systemPromptSummary: "You are Quinn, a calm and disciplined Investment Researcher. You prioritize extreme patience and spend over 90% of your time quietly observing order flow. You check available trading cash before proposing any purchase, strictly size orders to stay well within cash reserves, and only propose high-conviction trades when institutional shark footprints align.",
  tools: [
    "fetch_market_data(ticker, timeframe, limit)",
    "calculate_technical_indicator(ticker, indicator, params)",
    "detect_shark_footprints(ticker, orderbook_depth, delta_vol)",
    "traceback_historical_trades(ticker, limit)",
    "get_portfolio_summary()"
  ]
};

export const CRITIC_PERSONA = {
  name: "Morgan",
  title: "Senior Risk Auditor (Critic Agent - System 2)",
  model: "deepseek-r1:14b",
  role: "Deep Chain-of-Thought Auditing, Earns/Losses Traceback & Behavioral Defense",
  temperature: 0.1,
  badgeColor: "indigo",
  coreInvariants: [
    "Cash Reserve Invariant: Balance must NEVER drop below configured system cash reserve floor",
    "Position Sizing Invariant: Max 10% of total portfolio equity per single ticker",
    "Historical Loss Guard: Block revenge-trading after recent drawdowns without validated setup changes",
    "Market Psychology Defense: Scans ChromaDB memory for retail FOMO traps and fake breakouts"
  ],
  systemPromptSummary: "You are Morgan, a Senior Risk Auditor. You scrutinize all proposed trades from Quinn before broker execution, cross-checking past win/loss records and enforcing strict capital preservation.",
  tools: [
    "query_market_psychology(query, n_results)",
    "trace_historical_pnl_records(ticker)",
    "detect_market_regime(indicators, lookback_days)",
    "analyze_risk_scenarios(portfolio, trade_proposal)",
    "validate_trade_signal(signal, execution, market_data)"
  ]
};

export const INITIAL_AUTOPSIES = [
  {
    id: "autopsy-seed-1",
    ticker: "TSLA",
    tradeId: "trd-historical-tsla-1",
    lossAmount: 38.40,
    lossPct: 2.85,
    entryPrice: 224.50,
    exitPrice: 218.10,
    initialThesis: "Anticipated breakout over 224.00 resistance with minor delta volume bump.",
    rootCause: "PREMATURE_BREAKOUT: Entered before institutional icebergs verified absorption. Heavy macro seller pushed price below 220 support.",
    breakdown: "DeepSeek-R1 Autopsy: Price was rejected at the 4-hour supply band. Cumulative Volume Delta turned sharply negative 3 minutes after entry. Stop loss triggered as planned, saving $140+ in potential drawdown.",
    lessonLearned: "Require minimum +25,000 delta volume expansion on 5m timeframe before entering breakout setups near upper resistance.",
    guardrailRule: "Block long trades on TSLA when 5m CVD is declining, even if RSI appears bullish.",
    failureTag: "PREMATURE_BREAKOUT" as const,
    timestamp: new Date(Date.now() - 3600000 * 18).toISOString(),
    chromaEmbedded: true,
    criticModel: "deepseek-r1:14b"
  },
  {
    id: "autopsy-seed-2",
    ticker: "NVDA",
    tradeId: "trd-historical-nvda-1",
    lossAmount: 24.60,
    lossPct: 1.95,
    entryPrice: 128.20,
    exitPrice: 125.70,
    initialThesis: "Bought bounce off 128.00 support expecting shark accumulation continuation.",
    rootCause: "FAKE_ABSORPTION_TRAP: Retail liquidity trap. Large spoof bid pulled right before market open.",
    breakdown: "DeepSeek-R1 Autopsy: The 128.00 level had fake bid depth that disappeared upon fill. Tape speed accelerated downward with institutional distribution blocks.",
    lessonLearned: "Cross-check orderbook bid density across multiple levels (L2 depth) rather than relying on top-of-book bids.",
    guardrailRule: "Enforce a 2-minute post-fill tape velocity check. If bid cancellations exceed 60%, trigger immediate exit.",
    failureTag: "FAKE_ABSORPTION_TRAP" as const,
    timestamp: new Date(Date.now() - 3600000 * 8).toISOString(),
    chromaEmbedded: true,
    criticModel: "deepseek-r1:14b"
  }
];

export const SAMPLE_CHROMA_MEMORIES = [
  {
    topic: "TSLA Premature Breakout Autopsy",
    content: "Trade on TSLA failed (-$38.40) due to premature breakout at 4H supply band without verified delta volume (+25k). Enforce volume threshold before resistance longs.",
    category: "post_mortem_loss"
  },
  {
    topic: "NVDA Fake Absorption Trap Autopsy",
    content: "Trade on NVDA failed (-$24.60) due to fake bid spoofing at 128.00. DeepSeek-R1 mandated L2 multi-depth bid persistence checks before confirming whale accumulation.",
    category: "post_mortem_loss"
  },
  {
    topic: "Institutional Whale Accumulation",
    content: "When price forms a tight range at key support with hidden icebergs and positive cumulative volume delta (CVD), smart money is absorbing liquidity before markup.",
    category: "shark_pattern"
  },
  {
    topic: "Liquidity Sweep Setup",
    content: "When price quickly breaches swing lows to trigger retail stop-losses and immediately recovers with volume expansion, high-probability long entry is verified.",
    category: "market_structure"
  },
  {
    topic: "Overtrading & Revenge Defense",
    content: "Entering immediately after a loss without waiting for a new structural base leads to 68% failure rates. Enforce cooldown and historical win/loss review.",
    category: "behavioral_trap"
  },
  {
    topic: "Cash Reserve Discipline",
    content: "Maintaining a hard $50,000 liquid capital reserve ensures the fund survives black swan volatility events and extreme margin expansion.",
    category: "risk_invariant"
  }
];
