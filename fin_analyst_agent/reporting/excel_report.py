from __future__ import annotations

from typing import List
import pandas as pd


class ExcelReportBuilder:
    def __init__(self, output_path: str) -> None:
        self.output_path = output_path

    def build(self, assumptions: dict, fcfs: List[float], pvs: List[float], tv: float, tv_pv: float, ev: float, per_share: float | None) -> str:
        with pd.ExcelWriter(self.output_path, engine="xlsxwriter") as writer:
            pd.DataFrame({"Assumption": list(assumptions.keys()), "Value": list(assumptions.values())}).to_excel(writer, sheet_name="Assumptions", index=False)
            flows_df = pd.DataFrame({
                "Year": list(range(1, len(fcfs) + 1)),
                "FCF": fcfs,
                "PV of FCF": pvs,
            })
            flows_df.to_excel(writer, sheet_name="DCF", index=False)
            summary_df = pd.DataFrame({
                "Metric": ["Terminal Value", "Terminal Value PV", "Enterprise Value", "Intrinsic Value/Share"],
                "Value": [tv, tv_pv, ev, per_share],
            })
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
        return self.output_path