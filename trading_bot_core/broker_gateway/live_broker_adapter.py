"""
Live / Paper Broker Adapter
Provides seamless integration with Bursa Malaysia (Moomoo / FutuOpenD / IBKR MYX)
and Alpaca Markets Paper Trading APIs.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .bursa_malaysia_broker import BursaMalaysiaBroker
from .alpaca_broker import AlpacaBroker
from .base_broker import BaseBroker
from ..models.order_contracts import OrderContract, OrderAction, OrderType, OrderStatus

logger = logging.getLogger(__name__)

class LiveBrokerAdapter(BursaMalaysiaBroker):
    """
    Live / Paper broker adapter specialized for Bursa Malaysia (MYX / KLSE)
    and Moomoo Open API (FutuOpenD).
    Supports real-time tape reading, institutional shark / whale detection,
    broker queue Level 2 tracking, and automated paper execution in MYR.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        logger.info(f"LiveBrokerAdapter (Bursa Malaysia / Moomoo) initialized (Currency: {self.currency}, Initial Cash: RM {self.cash_balance:,.2f})")

