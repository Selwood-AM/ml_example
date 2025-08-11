from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional
import requests


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


@dataclass
class FredSeries:
    series_id: str
    latest_value: Optional[float]
    latest_date: Optional[str]


class FredProvider:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("FRED_API_KEY")

    def get_latest_value(self, series_id: str) -> FredSeries:
        params = {
            "series_id": series_id,
            "file_type": "json",
        }
        if self.api_key:
            params["api_key"] = self.api_key
        resp = requests.get(FRED_BASE, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        observations = data.get("observations", [])
        latest_value = None
        latest_date = None
        if observations:
            last = observations[-1]
            val = last.get("value")
            try:
                latest_value = float(val)
            except Exception:
                latest_value = None
            latest_date = last.get("date")
        return FredSeries(series_id=series_id, latest_value=latest_value, latest_date=latest_date)