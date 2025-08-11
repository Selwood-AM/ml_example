from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import math


@dataclass
class DCFInputs:
    ticker: str
    starting_fcf: float
    forecast_years: int
    revenue_growth_rate: float
    ebit_margin: float
    reinvestment_rate: float
    working_capital_ratio: float
    tax_rate: float
    discount_rate: float
    terminal_growth_rate: float
    shares_outstanding: Optional[float]


@dataclass
class DCFOutputs:
    projected_fcfs: List[float]
    discount_factors: List[float]
    present_values: List[float]
    terminal_value: float
    terminal_value_pv: float
    enterprise_value: float
    equity_value: Optional[float]
    intrinsic_value_per_share: Optional[float]


class DCFModel:
    @staticmethod
    def project_fcfs(inputs: DCFInputs) -> List[float]:
        fcfs: List[float] = []
        fcf = inputs.starting_fcf
        for _ in range(inputs.forecast_years):
            fcf = fcf * (1 + inputs.revenue_growth_rate)
            ebit = fcf / max(inputs.ebit_margin, 1e-6)
            nopat = ebit * (1 - inputs.tax_rate)
            reinvestment = nopat * inputs.reinvestment_rate
            change_in_wc = nopat * inputs.working_capital_ratio
            fcf_next = nopat - reinvestment - change_in_wc
            fcfs.append(max(fcf_next, 0.0))
            fcf = fcfs[-1]
        return fcfs

    @staticmethod
    def discount_cash_flows(fcfs: List[float], discount_rate: float) -> List[float]:
        discount_factors = [(1 / ((1 + discount_rate) ** (t + 1))) for t in range(len(fcfs))]
        present_values = [fcf * df for fcf, df in zip(fcfs, discount_factors)]
        return present_values

    @staticmethod
    def compute_terminal_value(last_fcf: float, g: float, r: float) -> float:
        if r <= g:
            return float('inf')
        return last_fcf * (1 + g) / (r - g)

    @classmethod
    def run(cls, inputs: DCFInputs) -> DCFOutputs:
        fcfs = cls.project_fcfs(inputs)
        pvs = cls.discount_cash_flows(fcfs, inputs.discount_rate)
        last_fcf = fcfs[-1] if fcfs else 0.0
        tv = cls.compute_terminal_value(last_fcf, inputs.terminal_growth_rate, inputs.discount_rate)
        tv_pv = tv / ((1 + inputs.discount_rate) ** inputs.forecast_years)
        ev = sum(pvs) + tv_pv
        equity = None
        per_share = None
        if inputs.shares_outstanding and inputs.shares_outstanding > 0:
            equity = ev
            per_share = equity / inputs.shares_outstanding
        return DCFOutputs(
            projected_fcfs=fcfs,
            discount_factors=[1 / ((1 + inputs.discount_rate) ** (t + 1)) for t in range(len(fcfs))],
            present_values=pvs,
            terminal_value=tv,
            terminal_value_pv=tv_pv,
            enterprise_value=ev,
            equity_value=equity,
            intrinsic_value_per_share=per_share,
        )