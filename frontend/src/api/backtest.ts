import api from './client';
import type { BacktestResult, TuneResult, HistoricalScreenResult } from './types';

export interface BacktestParams {
  ts_code: string;
  days?: number;
  stop_loss_pct?: number;
  take_profit_pct?: number;
}

export async function runBacktest(params: BacktestParams): Promise<BacktestResult> {
  const { data } = await api.post<BacktestResult>('/backtest', params);
  return data;
}

export interface TuneParams {
  ts_code: string;
  param_grid: Record<string, number[]>;
  days?: number;
  score_metric?: string;
}

export async function tuneBacktest(params: TuneParams): Promise<TuneResult> {
  const { data } = await api.post<TuneResult>('/backtest/tune', params);
  return data;
}

export interface HistoricalScreenParams {
  date_range: { end: string };
  criteria: { strategies?: string[]; min_score?: number };
}

export async function historicalScreen(params: HistoricalScreenParams): Promise<HistoricalScreenResult> {
  const { data } = await api.post<HistoricalScreenResult>('/backtest/screener', params);
  return data;
}
