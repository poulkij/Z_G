import api from './client';
import type { ScreenerResponse, StockScore } from './types';

export async function screenerScreen(strategy: string, maxStocks = 500): Promise<ScreenerResponse> {
  const { data } = await api.get<ScreenerResponse>('/screener', { params: { strategy, max_stocks: maxStocks } });
  return data;
}

export async function getStockScore(tsCode: string): Promise<StockScore> {
  const { data } = await api.get<StockScore>(`/screener/score/${tsCode}`);
  return data;
}

export interface HistoricalScreenerParams {
  date: string;
  strategies?: string[];
  min_score?: number;
  days?: number;
  limit?: number;
}

export async function historicalScreener(params: HistoricalScreenerParams): Promise<ScreenerResponse> {
  const { data } = await api.post<ScreenerResponse>('/screener/historical', params);
  return data;
}
