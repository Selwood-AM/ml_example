from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
import yfinance as yf
import pandas as pd


@dataclass
class YahooCompanySnapshot:
    ticker: str
    long_name: Optional[str]
    currency: str
    shares_outstanding: Optional[float]
    beta: Optional[float]
    market_cap: Optional[float]


class YahooProvider:
    def __init__(self) -> None:
        pass

    def get_snapshot(self, ticker: str) -> YahooCompanySnapshot:
        t = yf.Ticker(ticker)
        info: Dict[str, Any] = t.info or {}
        long_name = info.get("longName")
        currency = info.get("currency", "USD")
        shares_outstanding = float(info.get("sharesOutstanding")) if info.get("sharesOutstanding") is not None else None
        beta = float(info.get("beta")) if info.get("beta") is not None else None
        market_cap = float(info.get("marketCap")) if info.get("marketCap") is not None else None
        return YahooCompanySnapshot(
            ticker=ticker.upper(),
            long_name=long_name,
            currency=currency,
            shares_outstanding=shares_outstanding,
            beta=beta,
            market_cap=market_cap,
        )

    def get_trailing_fcf(self, ticker: str) -> Optional[float]:
        t = yf.Ticker(ticker)
        cf = t.cashflow
        if cf is None or cf.empty:
            return None
        latest = cf.iloc[:, 0]
        ocf = latest.get("Total Cash From Operating Activities")
        capex = latest.get("Capital Expenditures")
        if ocf is None or capex is None:
            return None
        try:
            return float(ocf) - float(capex)
        except Exception:
            return None

    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        t = yf.Ticker(ticker)
        hist = t.history(period=period)
        return hist