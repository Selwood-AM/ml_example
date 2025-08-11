# Financial Analyst Agent

A lightweight Python agent that builds financial models (starting with DCF) for public companies, fetches market and macro data, and exports an Excel workbook report.

## Features
- Data providers:
  - Yahoo Finance for price, shares, financials, and market data
  - FRED for macro series (e.g., risk-free rate)
  - SEC EDGAR for official filing data (company facts) to compute FCF and shares
- Models:
  - Discounted Cash Flow (DCF) model with scenario support
- Reporting:
  - Auto-generated Excel report with assumptions, outputs, and charts
  - Optional template fill: place values into your own Excel model via named ranges and a DCF table anchor
- Agent orchestration:
  - One-shot run to fetch data, build model, and generate report

## Quickstart
1) Create and activate a virtual environment
```
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies
```
pip install -r requirements.txt
```

3) Run a sample DCF build (Yahoo data)
```
python main.py --ticker AAPL --years 5 --growth 0.05 --margin 0.25 --capex 0.05 --wc 0.01 --rf FRED:DGS10 --erp 0.045 --terminal_g 0.02 --data_source yahoo
```

4) Run with official SEC data preference (US tickers)
```
export SEC_EMAIL="you@example.com"  # recommended by SEC for polite User-Agent
python main.py --ticker AAPL --years 5 --growth 0.05 --margin 0.25 --capex 0.05 --wc 0.01 --rf FRED:DGS10 --erp 0.045 --terminal_g 0.02 --data_source sec
```

5) Use your Excel template (named ranges + anchor)
- Add named ranges to the workbook matching our scalar fields. We check both literal and underscore-variants:
  - Ticker, Data_Source, Starting_FCF, Forecast_Years, Revenue_Growth, EBIT_Margin,
    Reinvestment_Rate, Working_Capital_Ratio, Tax_Rate, Discount_Rate,
    Terminal_Growth, Shares_Outstanding, Terminal_Value, Terminal_Value_PV,
    Enterprise_Value, Intrinsic_Value/Share
- Create a named range `DCF_Start` pointing to a single cell where the DCF table should start,
  or provide `--template_sheet_fallback` and `--template_cell_fallback`.

Example:
```
python main.py --ticker AAPL --years 5 --growth 0.05 --margin 0.25 \
  --capex 0.05 --wc 0.01 --rf FRED:DGS10 --erp 0.045 --terminal_g 0.02 \
  --data_source sec \
  --template ./my_template.xlsx --template_anchor DCF_Start \
  --template_sheet_fallback DCF --template_cell_fallback A1
```

This will generate an Excel file in `./reports`.

## Configuration
- FRED: If you exceed anonymous limits, set `FRED_API_KEY` in your environment.
- SEC: Set `SEC_EMAIL` for a compliant User-Agent to improve reliability.

## Notes
- This project is for educational purposes; validate outputs before making decisions.