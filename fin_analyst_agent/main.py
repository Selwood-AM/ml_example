from __future__ import annotations

import argparse

from agent.orchestrator import AnalystAgent, RunConfig


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Financial Analyst Agent - DCF Builder")
    p.add_argument("--ticker", required=True)
    p.add_argument("--years", type=int, default=5)
    p.add_argument("--growth", type=float, default=0.05)
    p.add_argument("--margin", type=float, default=0.25)
    p.add_argument("--capex", type=float, default=0.05, help="Reinvestment rate proxy")
    p.add_argument("--wc", type=float, default=0.01, help="Working capital ratio proxy")
    p.add_argument("--tax", type=float, default=0.21)
    p.add_argument("--discount", type=float)
    p.add_argument("--rf", type=str, default="FRED:DGS10")
    p.add_argument("--erp", type=float, default=0.045)
    p.add_argument("--beta", type=float)
    p.add_argument("--terminal_g", type=float, default=0.02)
    p.add_argument("--out", type=str, default="./reports")
    p.add_argument("--data_source", type=str, default="yahoo", choices=["yahoo", "sec"], help="Prefer data from 'yahoo' or 'sec'")
    # Template options
    p.add_argument("--template", type=str, help="Path to an Excel template (.xlsx)")
    p.add_argument("--template_anchor", type=str, default="DCF_Start", help="Named range used as DCF table start")
    p.add_argument("--template_sheet_fallback", type=str, help="Sheet name fallback if anchor missing")
    p.add_argument("--template_cell_fallback", type=str, help="Cell like A1 where to place DCF table if anchor missing")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    agent = AnalystAgent()
    cfg = RunConfig(
        ticker=args.ticker,
        forecast_years=args.years,
        revenue_growth_rate=args.growth,
        ebit_margin=args.margin,
        reinvestment_rate=args.capex,
        working_capital_ratio=args.wc,
        tax_rate=args.tax,
        discount_rate=args.discount,
        risk_free_series=args.rf,
        equity_risk_premium=args.erp,
        beta_override=args.beta,
        terminal_growth_rate=args.terminal_g,
        output_dir=args.out,
        data_source=args.data_source,
        template_path=args.template,
        template_anchor=args.template_anchor,
        template_sheet_fallback=args.template_sheet_fallback,
        template_cell_fallback=args.template_cell_fallback,
    )
    path = agent.run(cfg)
    print(f"Report generated: {path}")


if __name__ == "__main__":
    main()