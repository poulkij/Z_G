# Domain Glossary — zettaranc-skill

## Data Profile

**StockProfile** — A quantitative snapshot of one stock at one point in time. Contains the 15 most commonly shared fields: ts_code, name, trade_date, close, pct_chg, and core technical indicators (KDJ, MACD, RSI, MA, Bollinger, vol_ratio). Consumed by all scoring and reporting modules. Lives in `modules/profile.py`.

- **Avoid**: "stock data", "stock info", "stock result" — use "profile" to mean this specific snapshot type.

**Indicator** — A computed technical value derived from raw K-line data (e.g., KDJ_K, MACD_DIF, RSI_6). The `IndicatorResult` dataclass extends `StockProfile` with 75+ additional computed fields used internally by the indicators pipeline.

- **Avoid**: "signal" (that's a trading decision, not a computed value).

**Score** — A 0-100 rating assessing one dimension of a stock (trend, volume, risk, B1 opportunity). The `StockScore` dataclass extends `StockProfile` with composite scoring fields. Produced by `score_stock()` in `screener.py`.

- **Avoid**: "rating", "grade" — use "score".

**Diagnosis** — A holistic assessment of a held position including buy/sell signals, price position, trend status, stop-loss price, and a recommendation. The `DiagnosisReport` dataclass extends `StockProfile`. Produced by `diagnose_stock()` in `portfolio_diagnosis.py`.

- **Avoid**: "analysis" (that's the raw computation), "report" (that's the formatted output).

**Assessment** — A read-only profile assembled from pre-computed indicator cache, with Z 哥-themed commentary rules. The `StockAssessment` dataclass extends `StockProfile`. Used only by `report.py`.

- **Avoid**: confused with "score" or "diagnosis" — assessment is read-only from cache, not live-computed.

## Execution Pipeline

**analyze_stock** — The 28-step indicator computation pipeline in `data_layer.py`. Takes `(ts_code, days)` → returns `IndicatorResult`. This is the *only* function with this name after the refactor.

**score_stock** — (Formerly `screener.analyze_stock`) Takes `(ts_code, klines=None)` → returns `StockScore`. Multi-dimensional scoring (B1, trend, volume, risk) on top of raw indicators.

## Data Conversion

**DailyData** — The canonical K-line row type. Contains OHLCV + pct_chg fields. Provides `.from_dict()` and `.to_dict()` for conversion at the boundary between dict-based APIs (strategies, bridge) and dataclass-based APIs (indicators, screener).
