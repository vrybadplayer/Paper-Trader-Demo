"""
Rich Dashboard for Live Terminal Telemetry
Provides real-time visualizations of trading bot performance using the Rich library.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.text import Text
from rich import box
from ..models.portfolio_state import PortfolioManager
from ..models.schemas import PortfolioState, Order

class RichDashboard:
    """
    A live dashboard that displays key trading bot metrics in the terminal.
    Uses Rich library for beautiful, real-time visualizations.
    """
    
    def __init__(self, portfolio_manager: PortfolioManager, refresh_rate: float = 1.0):
        """
        Initialize the dashboard.
        
        Args:
            portfolio_manager: Portfolio manager instance to get state from
            refresh_rate: How often to refresh the display (in seconds)
        """
        self.portfolio_manager = portfolio_manager
        self.refresh_rate = refresh_rate
        self.console = Console()
        self.layout = Layout()
        self.live = None
        self.is_running = False
        
        # Setup layout
        self._setup_layout()
    
    def _setup_layout(self):
        """Setup the layout structure for the dashboard."""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        # Split main section
        self.layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        # Split left section
        self.layout["left"].split_column(
            Layout(name="positions", ratio=1),
            Layout(name="performance", ratio=1)
        )
        
        # Split right section
        self.layout["right"].split_column(
            Layout(name="risk", ratio=1),
            Layout(name="activity", ratio=1)
        )
    
    def _make_header(self) -> Panel:
        """Create the header panel."""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        header_text = Text("Autonomous Hermes Quantitative Trading Framework", style="bold blue")
        header_text.append(f"\n{now}", style="dim")
        return Panel(header_text, style="blue", box=box.ROUNDED)
    
    def _make_positions_table(self) -> Panel:
        """Create the positions table panel."""
        state = self.portfolio_manager.get_state()
        
        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
        table.add_column("Ticker", style="cyan", width=8)
        table.add_column("Qty", justify="right", width=8)
        table.add_column("Avg Cost", justify="right", width=10)
        table.add_column("Current", justify="right", width=10)
        table.add_column("Market Value", justify="right", width=12)
        table.add_column("Unrealized P&L", justify="right", width=14)
        
        for pos in state.positions:
            pnl_color = "green" if pos.unrealized_pnl >= 0 else "red"
            table.add_row(
                pos.ticker,
                str(pos.quantity),
                f"${pos.avg_cost:.2f}",
                f"${pos.current_price:.2f}",
                f"${pos.market_value:.2f}",
                f"[{pnl_color}]${pos.unrealized_pnl:.2f}[/{pnl_color}]"
            )
        
        if not state.positions:
            table.add_row("", "No open positions", "", "", "", "", style="dim")
        
        return Panel(table, title="[bold]Current Positions[/bold]", border_style="green")
    
    def _make_performance_panel(self) -> Panel:
        """Create the performance metrics panel."""
        state = self.portfolio_manager.get_state()
        
        # Calculate performance metrics
        total_return = ((state.total_equity - 50000.0) / 50000.0) * 100 if state.total_equity > 0 else 0
        return_color = "green" if total_return >= 0 else "red"
        
        perf_text = Text()
        perf_text.append(f"Total Equity: ${state.total_equity:,.2f}\n", style="bold")
        perf_text.append(f"Cash Balance: ${state.cash_balance:,.2f}\n")
        perf_text.append(f"Reserve: ${state.reserve_limit:,.2f}\n")
        perf_text.append(f"Realized P&L: ${state.realized_pnl:,.2f}\n")
        perf_text.append(f"Unrealized P&L: ${state.unrealized_pnl:,.2f}\n")
        perf_text.append(f"Total Return: [{return_color}]{total_return:+.2f}%[/{return_color}]\n")
        
        # Calculate win rate if we have trades
        # This would come from transaction history in a real implementation
        perf_text.append(f"Win Rate: N/A (no trades yet)\n", style="dim")
        
        return Panel(perf_text, title="[bold]Performance[/bold]", border_style="yellow")
    
    def _make_risk_panel(self) -> Panel:
        """Create the risk metrics panel."""
        state = self.portfolio_manager.get_state()
        
        # Risk metrics
        cash_reserve_ok = state.cash_balance >= state.reserve_limit
        reserve_color = "green" if cash_reserve_ok else "red"
        
        # Position concentration (simplified)
        max_position_pct = 0.0
        if state.total_equity > 0 and state.positions:
            max_position_value = max((pos.market_value for pos in state.positions), default=0)
            max_position_pct = (max_position_value / state.total_equity) * 100
        
        concentration_ok = max_position_pct <= 10.0  # 10% max per position
        concentration_color = "green" if concentration_ok else "red"
        
        risk_text = Text()
        risk_text.append(f"Cash Reserve: ${state.cash_balance:,.2f}\n")
        risk_text.append(f"Required Reserve: ${state.reserve_limit:,.2f} [{reserve_color}]{'✓ PASS' if cash_reserve_ok else '✗ FAIL'}[/{reserve_color}]\n")
        risk_text.append(f"Max Position Size: {max_position_pct:.1f}% [{concentration_color}]{'✓ PASS' if concentration_ok else '✗ FAIL'}[/{concentration_color}]\n")
        risk_text.append(f"Daily P&L: N/A (tracking not implemented)\n")
        risk_text.append(f"Max Drawdown: N/A (tracking not implemented)\n")
        risk_text.append(f"Total Exposure: ${(state.total_equity - state.cash_balance):,.2f}\n")
        
        return Panel(risk_text, title="[bold]Risk Metrics[/bold]", border_style="red")
    
    def _make_activity_panel(self) -> Panel:
        """Create the recent activity panel."""
        # In a real implementation, this would show recent trades, signals, etc.
        activity_text = Text()
        activity_text.append("Recent Activity:\n", style="bold")
        activity_text.append("• System initialized\n", style="dim")
        activity_text.append("• Paper trading mode: ACTIVE\n", style="green")
        activity_text.append("• Waiting for trading signals...\n", style="yellow")
        activity_text.append("• Last update: " + datetime.utcnow().strftime("%H:%M:%S") + "\n", style="dim")
        
        return Panel(activity_text, title="[bold]Activity Log[/bold]", border_style="blue")
    
    def _make_footer(self) -> Panel:
        """Create the footer panel."""
        footer_text = Text()
        footer_text.append("Controls: ", style="bold")
        footer_text.append("[Ctrl+C] Stop Dashboard", style="dim")
        return Panel(footer_text, style="grey70", box=box.ROUNDED)
    
    def _update_layout(self):
        """Update all layout components with latest data."""
        self.layout["header"].update(self._make_header())
        self.layout["main"]["left"]["positions"].update(self._make_positions_table())
        self.layout["main"]["left"]["performance"].update(self._make_performance_panel())
        self.layout["main"]["right"]["risk"].update(self._make_risk_panel())
        self.layout["main"]["right"]["activity"].update(self._make_activity_panel())
        self.layout["footer"].update(self._make_footer())
    
    def start(self):
        """Start the live dashboard display."""
        self.is_running = True
        self.live = Live(self.layout, refresh_per_second=1/self.refresh_rate, screen=True)
        self.live.start()
        
        try:
            while self.is_running:
                self._update_layout()
                time.sleep(self.refresh_rate)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the live dashboard display."""
        self.is_running = False
        if self.live:
            self.live.stop()

# Example usage (for testing)
if __name__ == "__main__":
    # Create a portfolio manager with some sample data
    pm = PortfolioManager(initial_cash=50000.0)
    
    # Add a sample position for demonstration
    from ..models.schemas import PortfolioPosition
    sample_pos = PortfolioPosition(
        ticker="AAPL",
        quantity=100,
        avg_cost=150.0,
        current_price=155.0,
        market_value=15500.0,
        unrealized_pnl=500.0
    )
    pm.state.positions.append(sample_pos)
    pm._update_equity()
    
    # Start the dashboard
    dashboard = RichDashboard(pm, refresh_rate=0.5)
    try:
        dashboard.start()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")