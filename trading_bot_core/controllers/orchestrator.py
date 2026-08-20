"""
Orchestrator
Central orchestrator that manages the dual-agent workflow (Worker and Critic agents).
Implements the FSM (Finite State Machine) and DAG (Directed Acyclic Graph) for task planning and execution.
"""

import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging

from ..models.schemas import PortfolioState, TradeSignal, RiskCheckResult
from ..models.order_contracts import OrderContract, OrderAction, OrderType, OrderStatus
from ..broker_gateway.sandbox_broker import SandboxBroker
from ..database.position_tracker import PositionTracker
from ..database.transaction_ledger import TransactionLedger
from ..database.vector_store import VectorStore
from ..self_healing.process_guard import ProcessGuard
from ..self_healing.traceback_sanitizer import safe_execute, setup_traceback_excepthook
from ..views.rich_dashboard import RichDashboard
from ..models.portfolio_state import PortfolioManager

logger = logging.getLogger(__name__)

class OrchestratorState(Enum):
    """States of the orchestrator FSM."""
    IDLE = "IDLE"
    FETCHING_DATA = "FETCHING_DATA"
    GENERATING_SIGNAL = "GENERATING_SIGNAL"
    VALIDATING_SIGNAL = "VALIDATING_SIGNAL"
    EXECUTING_TRADE = "EXECUTING_TRADE"
    UPDATING_STATE = "UPDATING_STATE"
    ERROR = "ERROR"
    STOPPED = "STOPPED"

class Orchestrator:
    """
    Central orchestrator for the trading bot.
    Manages the state machine, agent orchestration, and overall workflow.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the orchestrator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.state = OrchestratorState.IDLE
        self.state_lock = threading.RLock()
        
        # Initialize components
        self.portfolio_manager = PortfolioManager(
            initial_cash=config.get('initial_cash', 50000.0)
        )
        self.broker = SandboxBroker(config.get('broker', {}))
        self.position_tracker = PositionTracker()
        self.transaction_ledger = TransactionLedger()
        self.vector_store = VectorStore()
        self.process_guard = ProcessGuard()
        self.dashboard = RichDashboard(self.portfolio_manager)
        
        # Worker and Critic agents (will be implemented in separate files)
        self.worker_agent = None  # Will be set to GeneratorWorker instance
        self.critic_agent = None  # Will be set to CriticAuditor instance
        
        # Trading parameters
        self.tickers = config.get('tickers', ['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
        self.timeframe = config.get('timeframe', '1D')
        self.max_position_size = config.get('max_position_size', 0.1)  # 10% of equity
        self.min_cash_reserve = config.get('min_cash_reserve', 50000.0)
        
        # Control flags
        self.is_running = False
        self.main_thread = None
        
        # Setup traceback handling
        setup_traceback_excepthook()
        
        logger.info("Orchestrator initialized")
    
    def start(self):
        """Start the orchestrator and all components."""
        with self.state_lock:
            if self.is_running:
                logger.warning("Orchestrator already running")
                return
            
            self.is_running = True
            self.state = OrchestratorState.IDLE
        
        # Start monitoring
        self.process_guard.start_monitoring()
        
        # Connect to broker
        if not self.broker.connect():
            logger.error("Failed to connect to broker")
            self.state = OrchestratorState.ERROR
            return
        
        # Start the main loop in a separate thread
        self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.main_thread.start()
        
        # Start the dashboard (this will block until stopped)
        try:
            self.dashboard.start()
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the orchestrator and all components."""
        logger.info("Stopping orchestrator...")
        self.is_running = False
        
        # Stop the dashboard
        self.dashboard.stop()
        
        # Wait for main thread to finish
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=5.0)
        
        # Disconnect from broker
        self.broker.disconnect()
        
        # Stop monitoring
        self.process_guard.stop_monitoring()
        
        with self.state_lock:
            self.state = OrchestratorState.STOPPED
        
        logger.info("Orchestrator stopped")
    
    def _main_loop(self):
        """Main orchestration loop."""
        logger.info("Starting main orchestration loop")
        
        while self.is_running:
            try:
                with self.state_lock:
                    if self.state == OrchestratorState.ERROR:
                        # In error state, wait a bit before trying to recover
                        time.sleep(5.0)
                        continue
                    
                    # Proceed through the states
                    if self.state == OrchestratorState.IDLE:
                        self._state_idle()
                    elif self.state == OrchestratorState.FETCHING_DATA:
                        self._state_fetching_data()
                    elif self.state == OrchestratorState.GENERATING_SIGNAL:
                        self._state_generating_signal()
                    elif self.state == OrchestratorState.VALIDATING_SIGNAL:
                        self._state_validating_signal()
                    elif self.state == OrchestratorState.EXECUTING_TRADE:
                        self._state_executing_trade()
                    elif self.state == OrchestratorState.UPDATING_STATE:
                        self._state_updating_state()
                    elif self.state == OrchestratorState.STOPPED:
                        break
                
                # Small sleep to prevent busy waiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                with self.state_lock:
                    self.state = OrchestratorState.ERROR
                time.sleep(5.0)  # Wait before retrying
    
    def _state_idle(self):
        """IDLE state: waiting for next cycle."""
        # Transition to fetching data after a short delay
        time.sleep(1.0)  # Wait 1 second between cycles
        with self.state_lock:
            if self.is_running:
                self.state = OrchestratorState.FETCHING_DATA
    
    def _state_fetching_data(self):
        """FETCHING_DATA state: gather market data and system status."""
        logger.debug("Fetching market data")
        
        # Fetch market data for all tickers
        market_data = {}
        for ticker in self.tickers:
            data = self.broker.get_market_data(ticker, self.timeframe, limit=10)
            if data:
                market_data[ticker] = data
        
        # Update portfolio manager with latest prices
        for ticker, data in market_data.items():
            if data:
                latest_price = data[-1]['close']  # Most recent close price
                self.portfolio_manager.update_position_price(ticker, latest_price)
        
        # Transition to generating signal
        with self.state_lock:
            if self.is_running:
                self.state = OrchestratorState.GENERATING_SIGNAL
    
    def _state_generating_signal(self):
        """GENERATING_SIGNAL state: Worker agent generates trade signals."""
        logger.debug("Generating trade signal")
        
        # For now, we'll generate a simple signal based on moving average crossover
        # In a real implementation, this would involve the Worker Agent (LLM)
        signal = self._generate_simple_signal()
        
        if signal:
            # Store the signal for the next state
            self._pending_signal = signal
            with self.state_lock:
                if self.is_running:
                    self.state = OrchestratorState.VALIDATING_SIGNAL
        else:
            # No signal generated, go back to idle
            with self.state_lock:
                if self.is_running:
                    self.state = OrchestratorState.IDLE
    
    def _state_validating_signal(self):
        """VALIDATING_SIGNAL state: Critic agent validates the signal."""
        logger.debug("Validating signal")
        
        if not hasattr(self, '_pending_signal'):
            logger.warning("No pending signal to validate")
            with self.state_lock:
                if self.is_running:
                    self.state = OrchestratorState.IDLE
            return
        
        signal = self._pending_signal
        
        # Validate the signal using risk checks and critic analysis
        validation_result = self._validate_signal(signal)
        
        if validation_result.get('approved', False):
            # Signal approved, proceed to execution
            self._pending_order = self._signal_to_order(signal, validation_result)
            with self.state_lock:
                if self.is_running:
                    self.state = OrchestratorState.EXECUTING_TRADE
        else:
            # Signal rejected, log and go back to idle
            logger.info(f"Signal rejected: {validation_result.get('reason', 'Unknown reason')}")
            with self.state_lock:
                if self.is_running:
                    self.state = OrchestratorState.IDLE
    
    def _state_executing_trade(self):
        """EXECUTING_TRADE state: execute the approved order."""
        logger.debug("Executing trade")
        
        if not hasattr(self, '_pending_order'):
            logger.warning("No pending order to execute")
            with self.state_lock:
                if self.is_running:
                    self.state = OrchestratorState.IDLE
            return
        
        order = self._pending_order
        
        # Execute the order via the broker
        executed_order = safe_execute(self.broker.place_order, order)
        
        if executed_order and executed_order.status == OrderStatus.FILLED:
            # Order executed successfully, update state
            self._pending_executed_order = executed_order
            with self.state_lock:
                if self.is_running:
                    self.state = OrchestratorState.UPDATING_STATE
        else:
            # Order execution failed
            logger.error("Order execution failed")
            with self.state_lock:
                if self.is_running:
                    self.state = OrchestratorState.IDLE
    
    def _state_updating_state(self):
        """UPDATING_STATE state: update all systems with the executed trade."""
        logger.debug("Updating state with executed trade")
        
        if not hasattr(self, '_pending_executed_order'):
            logger.warning("No pending executed order to update state with")
            with self.state_lock:
                if self.is_running:
                    self.state = OrchestratorState.IDLE
            return
        
        executed_order = self._pending_executed_order
        
        # Update position tracker
        order_dict = executed_order.dict()
        self.position_tracker.update_from_order(order_dict)
        
        # Record transaction in ledger
        self.transaction_ledger.record_transaction(order_dict)
        
        # Add to vector store as memory
        self.vector_store.add_trade_memory(order_dict)
        
        # Clean up pending attributes
        delattr(self, '_pending_signal')
        delattr(self, '_pending_order')
        delattr(self, '_pending_executed_order')
        
        # Transition back to idle
        with self.state_lock:
            if self.is_running:
                self.state = OrchestratorState.IDLE
    
    def _generate_simple_signal(self) -> Optional[TradeSignal]:
        """
        Generate a simple trade signal based on technical indicators.
        This is a placeholder for the Worker Agent's signal generation.
        
        Returns:
            TradeSignal if a signal is generated, None otherwise
        """
        # For demonstration, we'll generate a random signal for AAPL every few cycles
        import random
        
        # Only generate a signal occasionally to avoid overtrading
        if random.random() < 0.1:  # 10% chance each cycle
            ticker = random.choice(self.tickers)
            action = random.choice([OrderAction.BUY, OrderAction.SELL])
            
            # Get current price for the ticker
            market_data = self.broker.get_market_data(ticker, self.timeframe, limit=1)
            if not market_data:
                return None
            
            current_price = market_data[-1]['close']
            
            # Create a simple signal
            signal = TradeSignal(
                ticker=ticker,
                action=action,
                quantity=100,  # Fixed quantity for demo
                target_price=current_price * 1.01 if action == OrderAction.BUY else current_price * 0.99,
                stop_loss=current_price * 0.95 if action == OrderAction.BUY else current_price * 1.05,
                take_profit=current_price * 1.1 if action == OrderAction.BUY else current_price * 0.9,
                confidence=0.7,
                timestamp=datetime.utcnow(),
                source="technical_demo",
                rationale=f"Demo signal based on random selection: {action.value} {ticker}"
            )
            
            return signal
        
        return None
    
    def _validate_signal(self, signal: TradeSignal) -> Dict[str, Any]:
        """
        Validate a trade signal using risk checks and critic analysis.
        This is a placeholder for the Critic Agent's validation.
        
        Args:
            signal: TradeSignal to validate
            
        Returns:
            Dictionary with validation results
        """
        # For now, we'll do a simple risk check
        # In a real implementation, this would involve the Critic Agent (LLM)
        
        # Check cash reserve
        account_info = self.broker.get_account_info()
        available_cash = account_info['available_for_trading']
        
        # Estimate cost of the trade
        market_data = self.broker.get_market_data(signal.ticker, self.timeframe, limit=1)
        if not market_data:
            return {
                'approved': False,
                'reason': f"Unable to get market data for {signal.ticker}",
                'violations': ['market_data_unavailable']
            }
        
        current_price = market_data[-1]['close']
        estimated_cost = signal.quantity * current_price
        
        # Check if we have enough cash (respecting reserve)
        if estimated_cost > available_cash:
            return {
                'approved': False,
                'reason': f"Insufficient cash: need ${estimated_cost:.2f}, have ${available_cash:.2f} available",
                'violations': ['cash_reserve'],
                'adjusted_quantity': int(available_cash / current_price) if current_price > 0 else 0
            }
        
        # Check position size limit
        position_value = estimated_cost
        total_equity = account_info['total_equity']
        position_pct = position_value / total_equity if total_equity > 0 else 0
        
        if position_pct > self.max_position_size:
            return {
                'approved': False,
                'reason': f"Position size too large: {position_pct:.2%} > {self.max_position_size:.2%}",
                'violations': ['position_size'],
                'adjusted_quantity': int((total_equity * self.max_position_size) / current_price) if current_price > 0 else 0
            }
        
        # If we pass all checks, approve the signal
        return {
            'approved': True,
            'reason': "Signal passed all risk checks",
            'violations': [],
            'adjusted_quantity': signal.quantity  # No adjustment needed
        }
    
    def _signal_to_order(self, signal: TradeSignal, validation_result: Dict[str, Any]) -> OrderContract:
        """
        Convert a validated signal to an order contract.
        
        Args:
            signal: The validated trade signal
            validation_result: Result from signal validation (may contain adjusted quantity)
            
        Returns:
            OrderContract ready for execution
        """
        quantity = validation_result.get('adjusted_quantity', signal.quantity)
        if quantity <= 0:
            quantity = 1  # Minimum quantity
        
        # Determine order type - for simplicity, we'll use market orders
        order_type = OrderType.MARKET
        
        order = OrderContract(
            ticker=signal.ticker,
            action=signal.action,
            quantity=quantity,
            order_type=order_type,
            # For market orders, price and stop_price are not required
            source_component="orchestrator"
        )
        
        return order

# Example usage (for testing)
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Configuration for the orchestrator
    config = {
        'initial_cash': 50000.0,
        'tickers': ['AAPL', 'GOOGL', 'MSFT'],
        'timeframe': '1D',
        'max_position_size': 0.1,
        'min_cash_reserve': 50000.0,
        'broker': {
            'initial_balance': 50000.0,
            'commission_per_trade': 0.001,
            'slippage_model': 'fixed'
        }
    }
    
    # Create and start the orchestrator
    orchestrator = Orchestrator(config)
    try:
        orchestrator.start()
    except KeyboardInterrupt:
        print("\nOrchestrator stopped by user")