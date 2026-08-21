#!/usr/bin/env python3
import os
import sys
# Add the parent directory of this script to the sys.path so we can import trading_bot_core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Autonomous Dual-Agent Trading Bot - Bursa Malaysia (MYX / KLSE) Entrypoint
==========================================================================
Launches the dual-agent trading engine locally with Bursa Malaysia (MYX)
market data, Moomoo Open API (FutuOpenD) & IBKR broker integration,
DeepSeek-R1 CoT risk auditing, and Malaysian institutional shark tape scanning.

Usage:
    python run_bot.py                 # Interactive runner
    python run_bot.py --auto          # Autonomous continuous loop
    python run_bot.py --scan 1155.KL  # Live Bursa Institutional Shark Tape (Maybank)
    python run_bot.py --test-auth     # Test Moomoo / Bursa Gateway & Ollama
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
from broker_gateway.bursa_malaysia_broker import BursaMalaysiaBroker
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

    # Inject Moomoo / Bursa environment variables
    futu_host = os.getenv("FUTU_OPEND_HOST", "127.0.0.1")
    futu_port = int(os.getenv("FUTU_OPEND_PORT", 11111))
    config.setdefault("broker", {})
    config["broker"]["host"] = futu_host
    config["broker"]["port"] = futu_port
    config["broker"]["type"] = "moomoo"
    config["broker"]["currency"] = "MYR"

    return config

def check_system_health(config: Dict[str, Any]):
    """Verify Ollama and Bursa Malaysia / Moomoo Gateway connections."""
    console.print("\n[bold cyan]═══ Bursa Malaysia (MYX) System Pre-Flight Checks ═══[/bold cyan]")
    
    # 1. Ollama Check
    ollama_url = config.get("model_routing", {}).get("ollama_base_url", "http://localhost:11434")
    ollama = OllamaClient(base_url=ollama_url)
    ollama_ok = ollama.is_available()
    
    if ollama_ok:
        models = ollama.get_available_models()
        console.print(f"[bold green]✔ Ollama Connected[/bold green] ({ollama_url}) - Models: {', '.join(models) if models else 'None'}")
    else:
        console.print(f"[bold yellow]⚠ Ollama Offline[/bold yellow] ({ollama_url}) - Ensure 'ollama serve' is running. Fallback heuristic active.")

    # 2. Bursa Malaysia Broker Gateway Check
    broker_cfg = config.get("broker", {})
    bursa = BursaMalaysiaBroker(broker_cfg)
    bursa_ok = bursa.connect()
    
    if bursa_ok:
        acc = bursa.get_account_info()
        console.print(f"[bold green]✔ Bursa Malaysia Gateway Active[/bold green] ({acc.get('broker')})")
        console.print(f"  • Account: [cyan]#{acc.get('account_number')}[/cyan] | Market: [bold green]{acc.get('market')}[/bold green]")
        console.print(f"  • Cash Balance: [bold green]RM {acc.get('cash_balance', 0):,.2f}[/bold green] | Total Equity: [bold green]RM {acc.get('total_equity', 0):,.2f}[/bold green]")
        console.print(f"  • Buying Power: [bold green]RM {acc.get('buying_power', 0):,.2f}[/bold green] | Currency: [yellow]MYR[/yellow]")
    else:
        console.print(f"[bold red]✘ Bursa Gateway Error[/bold red]: {bursa.get_last_error()}")

    console.print("[bold cyan]═════════════════════════════════════════════════════[/bold cyan]\n")
    return ollama_ok, bursa_ok

def run_shark_tape_scanner(ticker: str, config: Dict[str, Any]):
    """Run real-time institutional shark tape scanner on a Bursa Malaysia stock."""
    console.print(f"\n[bold magenta]🦈 Scanning Bursa Malaysia Institutional Tape for {ticker}...[/bold magenta]")
    broker_cfg = config.get("broker", {})
    bursa = BursaMalaysiaBroker(broker_cfg)
    
    scan = bursa.scan_shark_activity(ticker, lookback_minutes=30)
    
    table = Table(title=f"Bursa Malaysia Institutional Order Flow: {scan.get('ticker')}")
    table.add_column("Metric", style="cyan")
    table.add_column("Live Market Value", style="bold white")
    
    table.add_row("Current Price", f"RM {scan.get('current_price_myr', 0):.2f}")
    table.add_row("Institutional Shark Detected", "[bold green]YES (Whale Inflow)[/bold green]" if scan.get('shark_detected') else "[dim]NO[/dim]")
    table.add_row("Capital Flow Signature", f"[bold yellow]{scan.get('type')}[/bold yellow]")
    table.add_row("Cumulative Volume Delta (CVD)", f"{scan.get('delta_volume_shares', 0):+,d} shares ({scan.get('delta_volume_lots', 0):+,d} lots)")
    table.add_row("Institutional Buyer Pressure", f"{scan.get('buy_pressure_ratio', 0.5) * 100:.1f}%")
    table.add_row("Super-Large Inflow (Whale)", f"[bold green]RM {scan.get('super_large_inflow_myr', 0):,.2f}[/bold green]")
    table.add_row("Super-Large Outflow (Whale)", f"[bold red]RM {scan.get('super_large_outflow_myr', 0):,.2f}[/bold red]")
    
    console.print(table)
    
    if scan.get('block_trades'):
        b_table = Table(title=f"Recent Institutional Block Prints & Broker Queue ({scan.get('ticker')})")
        b_table.add_column("Time", style="dim")
        b_table.add_column("Side", style="bold")
        b_table.add_column("Broker / Institution", style="cyan")
        b_table.add_column("Price (RM)", style="green")
        b_table.add_column("Volume (Lots / Shares)", style="white")
        b_table.add_column("Notional Value (RM)", style="bold yellow")
        
        for b in scan['block_trades']:
            side_color = "[green]BUY[/green]" if b.get('side') == 'BUY' else "[red]SELL[/red]"
            b_table.add_row(
                str(b.get('timestamp')),
                side_color,
                str(b.get('broker_queue')),
                f"RM {b.get('price_myr'):.2f}",
                f"{b.get('lots'):,} lots ({b.get('shares'):,} shs)",
                f"RM {b.get('notional_myr', 0):,.2f}"
            )
        console.print(b_table)

def main():
    parser = argparse.ArgumentParser(description="Autonomous Dual-Agent Trading Bot - Bursa Malaysia")
    parser.add_argument("--auto", action="store_true", help="Run in continuous autonomous loop")
    parser.add_argument("--scan", type=str, default=None, help="Scan live Bursa Malaysia ticker (e.g. 5238.KL, 0138.KL, 0459.KL, 4677.KL)")
    parser.add_argument("--test-auth", action="store_true", help="Test Moomoo / Bursa Gateway and Ollama connectivity")
    parser.add_argument("--interval", type=int, default=10, help="Cycle interval in seconds for auto mode")
    args = parser.parse_args()

    config = load_config()

    if args.test_auth:
        check_system_health(config)
        return

    if args.scan:
        run_shark_tape_scanner(args.scan.upper(), config)
        return

    check_system_health(config)

    # Initialize Orchestrator
    orchestrator = Orchestrator(config)

    if args.auto:
        console.print(f"[bold green]Starting Bursa Malaysia Autonomous Trading Loop (Interval: {args.interval}s)... Press Ctrl+C to stop.[/bold green]")
        try:
            while True:
                orchestrator.run_fsm_cycle()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Shutting down bot safely...[/bold yellow]")
            orchestrator.stop()
    else:
        console.print(Panel(
            "[bold white]Autonomous Dual-Agent Trading Bot - Bursa Malaysia (MYX / KLSE)[/bold white]\n"
            "• System 1: Researcher / Generator (Fast Alpha & Malaysian Stock Tape Calling)\n"
            "• System 2: Critic Auditor (DeepSeek-R1 CoT Risk & ChromaDB Loss Memories)\n"
            "• Broker Gateway: Moomoo Malaysia (FutuOpenD) / IBKR MYX in Malaysian Ringgit (MYR)",
            title="Bursa Bot Online", border_style="cyan"
        ))
        
        while True:
            try:
                cmd = console.input("\n[bold cyan]Command ([r]un cycle, [s]can ticker, [p]ortfolio, [q]uit): [/bold cyan]").strip().lower()
                if cmd in ['q', 'exit', 'quit']:
                    break
                elif cmd in ['r', 'run', 'c', 'cycle']:
                    orchestrator.run_fsm_cycle()
                elif cmd.startswith('s ') or cmd == 's':
                    parts = cmd.split()
                    ticker = parts[1].upper() if len(parts) > 1 else console.input("Enter Bursa ticker (e.g. 5238.KL AAGB, 0138.KL ZETRIX, 0459.KL SUM, 4677.KL YTL): ").strip().upper()
                    run_shark_tape_scanner(ticker, config)
                elif cmd in ['p', 'portfolio']:
                    pos = orchestrator.broker.get_positions()
                    acc = orchestrator.broker.get_account_info()
                    console.print(f"Cash: RM {acc.get('cash_balance', 0):,.2f} | Total Equity: RM {acc.get('total_equity', 0):,.2f} | Open Positions: {len(pos)}")
                else:
                    console.print("[dim]Unknown command. Choose 'run', 'scan', 'portfolio', or 'quit'.[/dim]")
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    main()

