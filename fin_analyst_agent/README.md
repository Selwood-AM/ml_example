# Financial Analyst Agent

A lightweight Python agent that builds financial models (starting with DCF) for public companies, fetches market and macro data, and exports an Excel workbook report.

## Features
- Data providers:
  - Yahoo Finance for price, shares, financials, and market data
  - FRED for macro series (e.g., risk-free rate)
- Models:
  - Discounted Cash Flow (DCF) model with scenario support
- Reporting:
  - Auto-generated Excel report with assumptions, outputs, and charts
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

3) Run a sample DCF build
```
python main.py --ticker AAPL --years 5 --growth 0.05 --margin 0.25 --capex 0.05 --wc 0.01 --rf FRED:DGS10 --erp 0.045 --terminal_g 0.02
```

This will generate an Excel file in `./reports`.

## Configuration
- FRED: If you exceed anonymous limits, set `FRED_API_KEY` in your environment.

## Notes
- This project is for educational purposes; validate outputs before making decisions.