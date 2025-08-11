from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
import requests

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


@dataclass
class SecCompanyFacts:
    cik: str
    facts: Dict[str, Any]


class SecProvider:
    def __init__(self, email: Optional[str] = None) -> None:
        # SEC requires a descriptive User-Agent. Include contact email if possible.
        self.email = email or os.getenv("SEC_EMAIL")
        self.session = requests.Session()
        ua = f"fin-analyst-agent/0.1 (+https://example.com; {self.email})" if self.email else "fin-analyst-agent/0.1"
        self.session.headers.update({
            "User-Agent": ua,
            "Accept": "application/json",
        })

    def _request_json(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        try:
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code != 200:
                return None
            return resp.json()
        except requests.RequestException:
            return None

    def get_cik_for_ticker(self, ticker: str) -> Optional[str]:
        data = self._request_json(SEC_TICKERS_URL)
        if not data:
            return None
        # Format: {"0": {"ticker": "AAPL", "cik_str": 320193, ...}, ...}
        ticker_upper = ticker.upper()
        for _, entry in data.items():
            if entry.get("ticker", "").upper() == ticker_upper:
                cik_str = str(entry.get("cik_str"))
                return cik_str.zfill(10)
        return None

    def get_company_facts(self, cik: str) -> Optional[SecCompanyFacts]:
        url = SEC_COMPANYFACTS_URL.format(cik=cik)
        data = self._request_json(url)
        if not data:
            return None
        return SecCompanyFacts(cik=cik, facts=data.get("facts", {}))

    @staticmethod
    def _select_latest_usd(fact_object: dict, preferred_units: List[str]) -> Optional[Tuple[float, str]]:
        # fact_object example: {"units": {"USD": [{"end": "2023-09-30", "val": 1000, "fy": 2023, "fp": "FY"}, ...]}}
        units = fact_object.get("units", {})
        series: List[dict] = []
        for unit in preferred_units:
            if unit in units:
                series = units[unit]
                break
        if not series:
            return None
        # Filter out nulls and prefer FY then most recent end date
        candidates = [o for o in series if o.get("val") is not None]
        if not candidates:
            return None
        # Sort: prefer FY over Qs; then by end date
        def sort_key(o: dict) -> Tuple[int, str]:
            fp = o.get("fp")
            is_fy = 1 if fp == "FY" else 0
            return (is_fy, o.get("end", ""))
        candidates.sort(key=sort_key)
        latest = candidates[-1]
        try:
            return float(latest.get("val")), latest.get("end")
        except Exception:
            return None

    def get_latest_fcf(self, cik: str) -> Optional[float]:
        cf = self.get_company_facts(cik)
        if not cf:
            return None
        facts = cf.facts.get("us-gaap", {})
        # Operating Cash Flow tags
        ocf_tags = [
            "NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        ]
        capex_tags = [
            "PaymentsToAcquirePropertyPlantAndEquipment",
            "PaymentsToAcquireProductiveAssets",
            "CapitalExpendituresIncurredButNotYetPaid",
        ]
        ocf_value = None
        for tag in ocf_tags:
            if tag in facts:
                sel = self._select_latest_usd(facts[tag], ["USD"])
                if sel:
                    ocf_value = sel[0]
                    break
        capex_value = None
        for tag in capex_tags:
            if tag in facts:
                sel = self._select_latest_usd(facts[tag], ["USD"])
                if sel:
                    capex_value = sel[0]
                    break
        if ocf_value is None or capex_value is None:
            return None
        return float(ocf_value) - float(capex_value)

    def get_shares_outstanding(self, cik: str) -> Optional[float]:
        cf = self.get_company_facts(cik)
        if not cf:
            return None
        facts = cf.facts.get("us-gaap", {})
        share_tags = [
            "CommonStockSharesOutstanding",
            "EntityCommonStockSharesOutstanding",
            "WeightedAverageNumberOfDilutedSharesOutstanding",
            "WeightedAverageNumberOfSharesOutstandingBasic",
        ]
        for tag in share_tags:
            if tag in facts:
                sel = self._select_latest_usd(facts[tag], ["shares", "SHARES"])
                if sel:
                    return float(sel[0])
        return None