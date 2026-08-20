"""
Task DAG Planner
Implements Directed Acyclic Graph (DAG) for task planning and dependencies.
Manages the workflow of tasks between Worker and Critic agents.
"""

import time
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import logging

from ..models.schemas import TradeSignal, PortfolioState
from ..models.order_contracts import OrderContract
from ..broker_gateway.sandbox_broker import SandboxBroker
from ..controllers.generator_worker import GeneratorWorker
from ..controllers.critic_auditor import CriticAuditor

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Status of a task in the DAG."""
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class TaskType(Enum):
    """Types of tasks in the trading bot DAG."""
    FETCH_MARKET_DATA = "FETCH_MARKET_DATA"
    CALCULATE_INDICATOR = "CALCULATE_INDICATOR"
    GENERATE_SIGNAL = "GENERATE_SIGNAL"
    VALIDATE_SIGNAL = "VALIDATE_SIGNAL"
    EXECUTE_ORDER = "EXECUTE_ORDER"
    UPDATE_STATE = "UPDATE_STATE"
    ANALYZE_PSYCHOLOGY = "ANALYZE_PSYCHOLOGY"
    DETECT_REGIME = "DETECT_REGIME"
    ANALYZE_RISK = "ANALYZE_RISK"

class Task:
    """Represents a single task in the DAG."""
    
    def __init__(self, task_id: str, task_type: TaskType, 
                 agent: str, params: Dict[str, Any] = None):
        """
        Initialize a task.
        
        Args:
            task_id: Unique identifier for the task
            task_type: Type of task to perform
            agent: Which agent should execute this task ('worker' or 'critic')
            params: Parameters for the task execution
        """
        self.task_id = task_id
        self.task_type = task_type
        self.agent = agent  # 'worker' or 'critic'
        self.params = params or {}
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.dependencies: List[str] = []  # Task IDs that must complete before this task
        self.dependents: List[str] = []    # Task IDs that depend on this task
    
    def add_dependency(self, task_id: str):
        """Add a dependency task ID."""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
    
    def add_dependent(self, task_id: str):
        """Add a dependent task ID."""
        if task_id not in self.dependents:
            self.dependents.append(task_id)
    
    def is_ready(self, completed_tasks: Dict[str, 'Task']) -> bool:
        """Check if all dependencies are completed."""
        if self.status != TaskStatus.PENDING:
            return False
        for dep_id in self.dependencies:
            dep_task = completed_tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    def mark_running(self):
        """Mark task as running."""
        self.status = TaskStatus.RUNNING
        self.start_time = datetime.utcnow()
    
    def mark_completed(self, result: Any = None):
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.end_time = datetime.utcnow()
    
    def mark_failed(self, error: str = None):
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.end_time = datetime.utcnow()
    
    def get_execution_time(self) -> Optional[float]:
        """Get task execution time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

class TaskDAGPlanner:
    """
    Directed Acyclic Graph planner for trading bot tasks.
    Manages task dependencies and execution order between Worker and Critic agents.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the DAG planner.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []  # Ordered list of task IDs to execute
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}
        self.is_running = False
        self.execution_thread = None
        
        # Agent instances
        self.worker_agent = GeneratorWorker(config)
        self.critic_agent = CriticAuditor(config)
        self.broker = SandboxBroker(config.get('broker', {}))
        
        logger.info("Task DAG Planner initialized")
    
    def add_task(self, task_id: str, task_type: TaskType, 
                 agent: str, params: Dict[str, Any] = None,
                 dependencies: List[str] = None) -> bool:
        """
        Add a task to the DAG.
        
        Args:
            task_id: Unique identifier for the task
            task_type: Type of task to perform
            agent: Which agent should execute this task ('worker' or 'critic')
            params: Parameters for the task execution
            dependencies: List of task IDs that must complete before this task
            
        Returns:
            bool: True if task added successfully, False otherwise
        """
        if task_id in self.tasks:
            logger.warning(f"Task {task_id} already exists")
            return False
        
        task = Task(task_id, task_type, agent, params)
        if dependencies:
            for dep_id in dependencies:
                task.add_dependency(dep_id)
        
        self.tasks[task_id] = task
        logger.debug(f"Added task {task_id}: {task_type.value} for {agent}")
        return True
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove a task from the DAG.
        
        Args:
            task_id: Task ID to remove
            
        Returns:
            bool: True if task removed successfully, False otherwise
        """
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found")
            return False
        
        task = self.tasks[task_id]
        
        # Remove dependencies from other tasks
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                dep_task = self.tasks[dep_id]
                if task_id in dep_task.dependents:
                    dep_task.dependents.remove(task_id)
        
        # Remove dependents from other tasks
        for dep_id in task.dependents:
            if dep_id in self.tasks:
                dep_task = self.tasks[dep_id]
                if task_id in dep_task.dependencies:
                    dep_task.dependencies.remove(task_id)
        
        del self.tasks[task_id]
        logger.debug(f"Removed task {task_id}")
        return True
    
    def _build_execution_order(self) -> List[str]:
        """
        Build a topological ordering of tasks based on dependencies.
        
        Returns:
            List of task IDs in execution order
        """
        # Make a copy of tasks to work with
        remaining_tasks = dict(self.tasks)
        execution_order = []
        
        while remaining_tasks:
            # Find tasks with no remaining dependencies
            ready_tasks = []
            for task_id, task in remaining_tasks.items():
                # Check if all dependencies are either not in remaining_tasks (already processed) or completed
                deps_satisfied = True
                for dep_id in task.dependencies:
                    if dep_id in remaining_tasks:
                        deps_satisfied = False
                        break
                if deps_satisfied:
                    ready_tasks.append(task_id)
            
            if not ready_tasks:
                # Circular dependency or missing dependency
                remaining_ids = list(remaining_tasks.keys())
                logger.error(f"Circular dependency or missing dependency detected. Remaining tasks: {remaining_ids}")
                # Break the cycle by removing one task (not ideal but prevents infinite loop)
                if remaining_tasks:
                    task_id = remaining_ids[0]
                    logger.warning(f"Breaking cycle by removing task {task_id}")
                    del remaining_tasks[task_id]
                    execution_order.append(task_id)
                continue
            
            # Add ready tasks to execution order (in the order they were found)
            for task_id in ready_tasks:
                execution_order.append(task_id)
                del remaining_tasks[task_id]
        
        return execution_order
    
    def _execute_task(self, task: Task) -> Any:
        """
        Execute a single task using the appropriate agent.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        try:
            task.mark_running()
            logger.debug(f"Executing task {task.task_id}: {task.task_type.value}")
            
            # Route to appropriate agent based on task type and agent
            if task.agent == 'worker':
                result = self._execute_worker_task(task)
            elif task.agent == 'critic':
                result = self._execute_critic_task(task)
            else:
                raise ValueError(f"Unknown agent: {task.agent}")
            
            task.mark_completed(result)
            logger.debug(f"Task {task.task_id} completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Task {task.task_id} failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.mark_failed(error_msg)
            raise
    
    def _execute_worker_task(self, task: Task) -> Any:
        """Execute a task using the Worker Agent."""
        task_type = task.task_type
        params = task.params
        
        if task_type == TaskType.FETCH_MARKET_DATA:
            ticker = params.get('ticker', 'AAPL')
            timeframe = params.get('timeframe')
            limit = params.get('limit', 100)
            return self.worker_agent.fetch_market_data(ticker, timeframe, limit)
        
        elif task_type == TaskType.CALCULATE_INDICATOR:
            ticker = params.get('ticker', 'AAPL')
            indicator = params.get('indicator', 'RSI')
            timeframe = params.get('timeframe')
            period = params.get('period')
            apply_to = params.get('apply_to', 'close')
            return self.worker_agent.calculate_technical_indicator(
                ticker, indicator, timeframe, period, apply_to)
        
        elif task_type == TaskType.GENERATE_SIGNAL:
            ticker = params.get('ticker', 'AAPL')
            return self.worker_agent.generate_signal(ticker)
        
        elif task_type == TaskType.EXECUTE_ORDER:
            ticker = params.get('ticker', 'AAPL')
            action = params.get('action', 'BUY')
            quantity = params.get('quantity', 100)
            order_type = params.get('order_type', 'MARKET')
            price = params.get('price')
            stop_price = params.get('stop_price')
            return self.worker_agent.execute_order(ticker, action, quantity, order_type, price, stop_price)
        
        elif task_type == TaskType.UPDATE_STATE:
            # This would typically update internal state, but we'll return success
            return {"status": "success", "message": "State updated"}
        
        else:
            raise ValueError(f"Unsupported task type for worker: {task_type}")
    
    def _execute_critic_task(self, task: Task) -> Any:
        """Execute a task using the Critic Agent."""
        task_type = task.task_type
        params = task.params
        
        if task_type == TaskType.VALIDATE_SIGNAL:
            signal = params.get('signal')
            execution = params.get('execution')
            market_data = params.get('market_data')
            return self.critic_agent.validate_trade_signal(signal, execution, market_data)
        
        elif task_type == TaskType.ANALYZE_PSYCHOLOGY:
            ticker = params.get('ticker')
            lookback_days = params.get('lookback_days')
            data_sources = params.get('data_sources')
            return self.critic_agent.analyze_market_psychology(ticker, lookback_days, data_sources)
        
        elif task_type == TaskType.DETECT_REGIME:
            indicators = params.get('indicators')
            lookback_days = params.get('lookback_days')
            return self.critic_agent.detect_market_regime(indicators, lookback_days)
        
        elif task_type == TaskType.ANALYZE_RISK:
            portfolio = params.get('portfolio')
            trade_proposal = params.get('trade_proposal')
            scenarios = params.get('scenarios')
            return self.critic_agent.analyze_risk_scenarios(portfolio, trade_proposal, scenarios)
        
        elif task_type == TaskType.GET_PORTFOLIO:
            return self.critic_agent.position_tracker.get_state()
        
        else:
            raise ValueError(f"Unsupported task type for critic: {task_type}")
    
    def execute_dag(self) -> Dict[str, Any]:
        """
        Execute the entire DAG of tasks in dependency order.
        
        Returns:
            Dictionary containing execution results and statistics
        """
        if self.is_running:
            logger.warning("DAG execution already running")
            return {"error": "DAG execution already running"}
        
        self.is_running = True
        start_time = datetime.utcnow()
        
        try:
            # Build execution order
            execution_order = self._build_execution_order()
            logger.info(f"Executing DAG with {len(execution_order)} tasks in order: {execution_order}")
            
            # Execute tasks in order
            for task_id in execution_order:
                if task_id not in self.tasks:
                    logger.warning(f"Task {task_id} not found in tasks")
                    continue
                
                task = self.tasks[task_id]
                
                try:
                    result = self._execute_task(task)
                    self.completed_tasks[task_id] = task
                except Exception as e:
                    # Task failed - we could implement retry logic here
                    self.failed_tasks[task_id] = task
                    logger.error(f"Task {task_id} failed, stopping DAG execution: {e}")
                    break  # Stop execution on first failure
            
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            # Prepare results
            results = {
                "execution_time_seconds": execution_time,
                "start_time": start_time.isoformat() + 'Z',
                "end_time": end_time.isoformat() + 'Z',
                "total_tasks": len(self.tasks),
                "completed_tasks": len(self.completed_tasks),
                "failed_tasks": len(self.failed_tasks),
                "skipped_tasks": 0,  # Not implemented in this version
                "task_results": {}
            }
            
            # Collect results from completed tasks
            for task_id, task in self.completed_tasks.items():
                results["task_results"][task_id] = {
                    "status": task.status.value,
                    "result": task.result,
                    "execution_time": task.get_execution_time()
                }
            
            # Collect errors from failed tasks
            for task_id, task in self.failed_tasks.items():
                results["task_results"][task_id] = {
                    "status": task.status.value,
                    "error": task.error,
                    "execution_time": task.get_execution_time()
                }
            
            logger.info(f"DAG execution completed in {execution_time:.2f} seconds")
            logger.info(f"Completed: {len(self.completed_tasks)}, Failed: {len(self.failed_tasks)}")
            
            return results
            
        finally:
            self.is_running = False
    
    def execute_dag_async(self, callback: Callable[[Dict[str, Any]], None] = None):
        """
        Execute the DAG asynchronously in a separate thread.
        
        Args:
            callback: Function to call with results when execution completes
        """
        if self.is_running:
            logger.warning("DAG execution already running")
            return
        
        def execution_wrapper():
            try:
                results = self.execute_dag()
                if callback:
                    callback(results)
            except Exception as e:
                logger.error(f"Error in async DAG execution: {e}")
                if callback:
                    callback({"error": str(e)})
        
        self.execution_thread = threading.Thread(target=execution_wrapper, daemon=True)
        self.execution_thread.start()
        logger.info("Started asynchronous DAG execution")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific task.
        
        Args:
            task_id: Task ID to check
            
        Returns:
            Dictionary with task status information or None if not found
        """
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "agent": task.agent,
            "status": task.status.value,
            "result": task.result,
            "error": task.error,
            "start_time": task.start_time.isoformat() + 'Z' if task.start_time else None,
            "end_time": task.end_time.isoformat() + 'Z' if task.end_time else None,
            "execution_time": task.get_execution_time(),
            "dependencies": task.dependencies,
            "dependents": task.dependents
        }
    
    def get_dag_status(self) -> Dict[str, Any]:
        """
        Get the status of the entire DAG.
        
        Returns:
            Dictionary with DAG status information
        """
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
        running_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
        pending_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "pending_tasks": pending_tasks,
            "is_running": self.is_running
        }
    
    def reset(self):
        """Reset the DAG planner to initial state."""
        # Wait for any running execution to complete
        if self.is_running:
            logger.warning("Cannot reset while DAG is running")
            return
        
        # Reset all tasks
        for task in self.tasks.values():
            task.status = TaskStatus.PENDING
            task.result = None
            task.error = None
            task.start_time = None
            task.end_time = None
        
        # Clear completed and failed task tracking
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        
        logger.info("DAG planner reset")

# Example usage (for testing)
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Configuration
    config = {
        'tickers': ['AAPL', 'GOOGL', 'MSFT'],
        'timeframe': '1D',
        'broker': {
            'initial_balance': 50000.0,
            'commission_per_trade': 0.001,
            'slippage_model': 'fixed'
        }
    }
    
    # Create DAG planner
    planner = TaskDAGPlanner(config)
    
    # Connect broker
    if planner.broker.connect():
        print("Connected to broker")
        
        # Add tasks for a simple trading workflow
        # 1. Fetch market data for AAPL
        planner.add_task(
            "fetch_data_aapl",
            TaskType.FETCH_MARKET_DATA,
            "worker",
            {"ticker": "AAPL", "limit": 20}
        )
        
        # 2. Calculate RSI indicator
        planner.add_task(
            "calc_rsi_aapl",
            TaskType.CALCULATE_INDICATOR,
            "worker",
            {"ticker": "AAPL", "indicator": "RSI", "period": 14},
            dependencies=["fetch_data_aapl"]
        )
        
        # 3. Generate signal based on RSI
        planner.add_task(
            "generate_signal",
            TaskType.GENERATE_SIGNAL,
            "worker",
            {"ticker": "AAPL"},
            dependencies=["calc_rsi_aapl"]
        )
        
        # 4. Validate signal (critic task)
        planner.add_task(
            "validate_signal",
            TaskType.VALIDATE_SIGNAL,
            "critic",
            {},  # Parameters will be filled in during execution
            dependencies=["generate_signal"]
        )
        
        # 5. Execute order if signal is valid
        planner.add_task(
            "execute_order",
            TaskType.EXECUTE_ORDER,
            "worker",
            {},  # Parameters will be filled in during execution
            dependencies=["validate_signal"]
        )
        
        # Show DAG status
        status = planner.get_dag_status()
        print(f"DAG status: {status}")
        
        # Execute the DAG
        print("\nExecuting DAG...")
        results = planner.execute_dag()
        
        print(f"\nExecution results:")
        print(f"  Execution time: {results.get('execution_time_seconds', 0):.2f} seconds")
        print(f"  Completed tasks: {results.get('completed_tasks', 0)}")
        print(f"  Failed tasks: {results.get('failed_tasks', 0)}")
        
        # Show task results
        for task_id, task_result in results.get('task_results', {}).items():
            status = task_result.get('status', 'unknown')
            print(f"  Task {task_id}: {status}")
            if status == 'failed':
                print(f"    Error: {task_result.get('error', 'Unknown error')}")
        
        # Disconnect
        planner.broker.disconnect()
    else:
        print("Failed to connect to broker")