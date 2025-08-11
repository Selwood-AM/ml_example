from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import os

from data_providers.yahoo_provider import YahooProvider
from data_providers.fred_provider import FredProvider
from data_providers.sec_provider import SecProvider
from models.dcf import DCFInputs, DCFModel
from reporting.excel_report import ExcelReportBuilder
from reporting.template_report import TemplateExcelReportBuilder


@dataclass
class RunConfig:
    ticker: str
    forecast_years: int = 5
    revenue_growth_rate: float = 0.05
    ebit_margin: float = 0.25
    reinvestment_rate: float = 0.05
    working_capital_ratio: float = 0.01
    tax_rate: float = 0.21
    discount_rate: Optional[float] = None
    risk_free_series: Optional[str] = None
    equity_risk_premium: Optional[float] = None
    beta_override: Optional[float] = None
    terminal_growth_rate: float = 0.02
    output_dir: str = "./reports"
    data_source: str = "yahoo"  # yahoo | sec
    template_path: Optional[str] = None
    template_anchor: str = "DCF_Start"
    template_sheet_fallback: Optional[str] = None
    template_cell_fallback: Optional[str] = None


class AnalystAgent:
    def __init__(self) -> None:
        self.yahoo = YahooProvider()
        self.fred = FredProvider()
        self.sec = SecProvider()

    def infer_discount_rate(self, ticker: str, rf_series: Optional[str], erp: Optional[float], beta_override: Optional[float]) -> float:
        rf = 0.04
        if rf_series and rf_series.startswith("FRED:"):
            series_id = rf_series.split(":", 1)[1]
            fred = self.fred.get_latest_value(series_id)
            if fred.latest_value is not None:
                rf = fred.latest_value / 100.0
        erp_value = erp if erp is not None else 0.045
        snapshot = self.yahoo.get_snapshot(ticker)
        beta = beta_override if beta_override is not None else (snapshot.beta or 1.0)
        return max(0.0, rf + beta * erp_value)

    def _get_official_data(self, ticker: str) -> tuple[Optional[float], Optional[float]]:
        cik = self.sec.get_cik_for_ticker(ticker)
        if not cik:
            return None, None
        fcf = self.sec.get_latest_fcf(cik)
        shares = self.sec.get_shares_outstanding(cik)
        return fcf, shares

    def run(self, cfg: RunConfig) -> str:
        os.makedirs(cfg.output_dir, exist_ok=True)

        starting_fcf: Optional[float] = None
        shares_outstanding: Optional[float] = None

        if cfg.data_source.lower() == "sec":
            fcf_official, shares_official = self._get_official_data(cfg.ticker)
            starting_fcf = fcf_official
            shares_outstanding = shares_official

        # Fallback to Yahoo if any piece missing
        snap = self.yahoo.get_snapshot(cfg.ticker)
        if shares_outstanding is None:
            shares_outstanding = snap.shares_outstanding
        if starting_fcf is None:
            starting_fcf = self.yahoo.get_trailing_fcf(cfg.ticker) or 1e9

        discount_rate = cfg.discount_rate or self.infer_discount_rate(
            cfg.ticker, cfg.risk_free_series, cfg.equity_risk_premium, cfg.beta_override
        )
        inputs = DCFInputs(
            ticker=cfg.ticker,
            starting_fcf=starting_fcf,
            forecast_years=cfg.forecast_years,
            revenue_growth_rate=cfg.revenue_growth_rate,
            ebit_margin=cfg.ebit_margin,
            reinvestment_rate=cfg.reinvestment_rate,
            working_capital_ratio=cfg.working_capital_ratio,
            tax_rate=cfg.tax_rate,
            discount_rate=discount_rate,
            terminal_growth_rate=cfg.terminal_growth_rate,
            shares_outstanding=shares_outstanding,
        )
        outputs = DCFModel.run(inputs)
        assumptions = {
            "Ticker": cfg.ticker,
            "Data Source": cfg.data_source,
            "Starting FCF": inputs.starting_fcf,
            "Forecast Years": inputs.forecast_years,
            "Revenue Growth": inputs.revenue_growth_rate,
            "EBIT Margin": inputs.ebit_margin,
            "Reinvestment Rate": inputs.reinvestment_rate,
            "Working Capital Ratio": inputs.working_capital_ratio,
            "Tax Rate": inputs.tax_rate,
            "Discount Rate": inputs.discount_rate,
            "Terminal Growth": inputs.terminal_growth_rate,
            "Shares Outstanding": inputs.shares_outstanding,
        }
        out_path = os.path.join(cfg.output_dir, f"{cfg.ticker.upper()}_DCF.xlsx")
        if cfg.template_path:
            report = TemplateExcelReportBuilder(cfg.template_path, out_path)
            return report.build(
                assumptions=assumptions,
                fcfs=outputs.projected_fcfs,
                pvs=outputs.present_values,
                tv=outputs.terminal_value,
                tv_pv=outputs.terminal_value_pv,
                ev=outputs.enterprise_value,
                per_share=outputs.intrinsic_value_per_share,
                dcf_anchor_name=cfg.template_anchor,
                dcf_sheet_fallback=cfg.template_sheet_fallback,
                dcf_cell_fallback=cfg.template_cell_fallback,
            )
        else:
            report = ExcelReportBuilder(out_path)
            return report.build(
                assumptions=assumptions,
                fcfs=outputs.projected_fcfs,
                pvs=outputs.present_values,
                tv=outputs.terminal_value,
                tv_pv=outputs.terminal_value_pv,
                ev=outputs.enterprise_value,
                per_share=outputs.intrinsic_value_per_share,
            )