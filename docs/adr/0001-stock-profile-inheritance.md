# ADR-0001: Inheritance over composition for StockProfile

**Date**: 2026-07-11  
**Status**: Accepted

## Context

Four modules define their own dataclasses representing a stock's quantitative snapshot:

- `IndicatorResult` (indicators/core.py, 90 fields)
- `StockScore` (screener.py, 8 fields)
- `DiagnosisReport` (portfolio_diagnosis.py, 18 fields)
- `StockAssessment` (report.py, 18 fields)

These dataclasses share ~15 fields (KDJ, MACD, RSI, MA arrays, Bollinger, vol_ratio) but have zero inheritance. Field duplication causes two concrete pains:

1. `_dict_to_daily()` and `_daily_to_dict()` are duplicated across modules to convert between shared fields
2. Adding a field to the common set requires touching 4 separate dataclass definitions

We need to introduce a shared `StockProfile` base class. The choice is inheritance vs composition.

## Decision

**Inheritance.** `StockScore(StockProfile)`, `DiagnosisReport(StockProfile)`, `IndicatorResult(StockProfile)`, `StockAssessment(StockProfile)`.

## Alternatives considered

**Composition** (`StockScore` contains a `profile: StockProfile` field):
- Pro: Decouples profile fields from score fields — profile changes don't affect score callers
- Con: Callers must write `result.profile.k` instead of `result.k`, breaking every existing call site across ~10 modules and ~30 test files. The cost of retraining the codebase on a new access pattern outweighs the decoupling benefit for fields that are inherently read together.

## Consequences

- Positive: One place to define shared fields. Conversion functions collapse into `DailyData.from_dict()/to_dict()`.
- Positive: IDE autocomplete shows inherited fields without extra attribute access.
- Risk: If a consumer needs a fundamentally different profile shape in the future (e.g., different timeframes simultaneously), the inheritance hierarchy constrains it. Mitigation: composition can be introduced later inside a specific consumer without breaking the inheritance base — `StockProfile` stays flat.
