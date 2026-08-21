#!/usr/bin/env python3
import os
import sys
# Add the parent directory of this script to the sys.path so we can import trading_bot_core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Autonomous Dual-Agent Trading Bot - Alpaca NVDA Single-Stock Strategy Entrypoint
================================================================================
Launches the dual-agent trading engine targeting NVDA stocks using Alpaca
Markets Paper Trading API (v2) and Market Data API (v2).

Usage:
    python run_bot.py                 # Interactive runner
    python run_bot.py --auto          # Autonomous continuous loop
    python run_bot.py --scan NVDA     # Live Alpaca Institutional Tape for NVDA
    python run_bot.py --test-auth     # Test Alpaca Broker & Ollama
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, Any

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / "config" / ".env"
    if not env_path.exists():
        env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

# Local module imports
from controllers.orchestrator import Orchestrator
from controllers.llm_client import OllamaClient
from broker_gateway.alpaca_broker import AlpacaBroker
from broker_gateway.sandbox_broker import SandboxBroker

console = Console()

def load_config() -> Dict[str, Any]:
    """Load settings.yaml configuration file."""
    config_path = Path(__file__).parent / "config" / "settings.yaml"
    if not config_path.exists():
        rprint("[bold red]Error:[/] config/settings.yaml not found!")
        sys.exit(1)
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f) or {}

    config.setdefault("broker", {})
    config["broker"]["type"] = "alpaca"
    config["broker"]["currency"] = "USD"

    # Inject Alpaca keys from environment if available
    api_key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
    secret_key = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_API_SECRET_KEY")
    if api_key:
        config["broker"]["api_key"] = api_key
    if secret_key:
        config["broker"]["api_secret"] = secret_key

    # Hard restrict universe to NVDA only
    config["tickers"] = ["NVDA"]

    return config

def check_system_health(config: Dict[str, Any]):
    """Verify Ollama and Alpaca Broker Gateway connections."""
    console.print("\n[bold cyan]═══ Alpaca Market (NVDA) System Pre-Flight Checks ═══[/bold cyan]")
    
    # 1. Ollama Check
    ollama_url = config.get("model_routing", {}).get("ollama_base_url", "http://localhost:11434")
    ollama = OllamaClient(base_url=ollama_url)
    ollama_ok = ollama.is_available()
    
    if ollama_ok:
        models = ollama.get_available_models()
        console.print(f"[bold green]✔ Ollama Connected[/bold green] ({ollama_url}) - Models: {', '.join(models) if models else 'None'}")
    else:
        console.print(f"[bold yellow]⚠ Ollama Offline[/bold yellow] ({ollama_url}) - Ensure 'ollama serve' is running. Fallback heuristic active.")

    # 2. Alpaca Broker Gateway Check
    broker_cfg = config.get("broker", {})
    alpaca = AlpacaBroker(broker_cfg)
    alpaca_ok = alpaca.connect()
    
    if alpaca_ok:
        acc = alpaca.get_account_info()
        console.print(f"[bold green]✔ Alpaca Broker Gateway Active[/bold green]")
        console.print(f"  • Account: [cyan]#{acc.get('account_number')}[/cyan] | Paper Trading: [bold green]{acc.get('is_paper')}[/bold green]")
        console.print(f"  • Cash Balance: [bold green]${acc.get('cash_balance', 0):,.2f}[/bold green] | Total Equity: [bold green]${acc.get('total_equity', 0):,.2f}[/bold green]")
        console.print(f"  • Buying Power: [bold green]${acc.get('buying_power', 0):,.2f}[/bold green] | Currency: [yellow]USD[/yellow]")
    else:
        console.print(f"[bold red]✘ Alpaca Gateway Notice[/bold red]: {alpaca.get_last_error()}")
        console.print("[dim]Set ALPACA_API_KEY and ALPACA_SECRET_KEY in environment or .env for live paper execution.[/dim]")

    console.print("[bold cyan]═════════════════════════════════════════════════════[/bold cyan]\n")
    return ollama_ok, alpaca_ok

def run_shark_tape_scanner(ticker: str, config: Dict[str, Any]):
    """Run real-time institutional shark tape scanner on NVDA via Alpaca."""
    ticker = "NVDA"  # Force single stock NVDA
    console.print(f"\n[bold magenta]🦈 Scanning Alpaca Institutional Tape for {ticker}...[/bold magenta]")
    broker_cfg = config.get("broker", {})
    alpaca = AlpacaBroker(broker_cfg)
    
    scan = alpaca.scan_shark_activity(ticker, lookback_minutes=30)
    
    table = Table(title=f"Alpaca Institutional Order Flow: {scan.get('ticker')}")
    table.add_column("Metric", style="cyan")
    table.add_column("Live Market Value", style="bold white")
    
    table.add_row("Current Price", f"${scan.get('current_price_usd', scan.get('current_price_myr', 0)):.2f}")
    table.add_row("Institutional Shark Detected", "[bold green]YES (Whale Inflow)[/bold green]" if scan.get('shark_detected') else "[dim]NO[/dim]")
    table.add_row("Capital Flow Signature", f"[bold yellow]{scan.get('type')}[/bold yellow]")
    table.add_row("Cumulative Volume Delta (CVD)", f"{scan.get('delta_volume_shares', 0):+,d} shares")
    table.add_row("Institutional Buyer Pressure", f"{scan.get('buy_pressure_ratio', 0.5) * 100:.1f}%")
    table.add_row("Super-Large Inflow (Whale)", f"[bold green]${scan.get('super_large_inflow_usd', 0):,.2f}[/bold green]")
    table.add_row("Super-Large Outflow (Whale)", f"[bold red]${scan.get('super_large_outflow_usd', 0):,.2f}[/bold red]")
    
    console.print(table)
    
    if scan.get('block_trades'):
        b_table = Table(title=f"Recent Institutional Block Prints ({scan.get('ticker')})")
        b_table.add_column("Time", style="dim")
        b_table.add_column("Side", style="bold")
        b_table.add_column("Price ($)", style="green")
        b_table.add_column("Volume (Shares)", style="white")
        b_table.add_column("Notional Value ($)", style="bold yellow")
        
        for b in scan['block_trades']:
            side_color = "[green]BUY[/green]" if b.get('side') == 'BUY' else "[red]SELL[/red]"
            b_table.add_row(
                str(b.get('timestamp')),
                side_color,
                f"${b.get('price_usd', b.get('price', 0)):.2f}",
                f"{b.get('shares', 0):,} shs",
                f"${b.get('notional_usd', 0):,.2f}"
            )
        console.print(b_table)

def main():
    parser = argparse.ArgumentParser(description="Autonomous Dual-Agent Trading Bot - Alpaca NVDA")
    parser.add_argument("--auto", action="store_true", help="Run in continuous autonomous loop")
    parser.add_argument("--scan", type=str, default="NVDA", help="Scan live Alpaca NVDA ticker tape")
    parser.add_argument("--test-auth", action="store_true", help="Test Alpaca Gateway and Ollama connectivity")
    parser.add_argument("--interval", type=int, default=10, help="Cycle interval in seconds for auto mode")
    args = parser.parse_args()

    config = load_config()

    if args.test_auth:
        check_system_health(config)
        return

    if args.scan:
        run_shark_tape_scanner("NVDA", config)
        return

    check_system_health(config)

    # Initialize Orchestrator
    orchestrator = Orchestrator(config)

    if args.auto:
        console.print(f"[bold green]Starting Alpaca NVDA Autonomous Trading Loop (Interval: {args.interval}s)... Press Ctrl+C to stop.[/bold green]")
        try:
            while True:
                orchestrator.run_fsm_cycle()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Shutting down bot safely...[/bold yellow]")
            orchestrator.stop()
    else:
        console.print(Panel(
            "[bold white]Autonomous Dual-Agent Trading Bot - Alpaca NVDA Single Stock Strategy[/bold white]\n"
            "• System 1: Researcher / Generator (Fast Alpha & NVDA Order Flow Scanning)\n"
            "• System 2: Critic Auditor (DeepSeek-R1 CoT Risk & Portfolio Memory)\n"
            "• Broker Gateway: Alpaca Markets Paper Trading in USD",
            title="NVDA Trading Engine Online", border_style="cyan"
        ))
        
        while True:
            try:
                cmd = console.input("\n[bold cyan]Command ([r]un cycle, [s]can NVDA, [p]ortfolio, [q]uit): [/bold cyan]").strip().lower()
                if cmd in ['q', 'exit', 'quit']:
                    break
                elif cmd in ['r', 'run', 'c', 'cycle']:
                    orchestrator.run_fsm_cycle()
                elif cmd.startswith('s ') or cmd == 's':
                    run_shark_tape_scanner("NVDA", config)
                elif cmd in ['p', 'portfolio']:
                    pos = orchestrator.broker.get_positions()
                    acc = orchestrator.broker.get_account_info()
                    console.print(f"Cash: ${acc.get('cash_balance', 0):,.2f} | Total Equity: ${acc.get('total_equity', 0):,.2f} | Open Positions: {len(pos)}")
                else:
                    console.print("[dim]Unknown command. Choose 'run', 'scan', 'portfolio', or 'quit'.[/dim]")
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    main()
