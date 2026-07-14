import api from './client';
import type { ScreenResult, StrategyInfo } from './types';

export async function fetchStrategies(): Promise<StrategyInfo[]> {
  const { data } = await api.get<StrategyInfo[]>('/screen/strategies');
  return data;
}

export interface ScreenConstraints {
  min_score?: number;
  min_b1_score?: number;
  min_trend_score?: number;
  min_volume_score?: number;
  max_risk_score?: number;
  industry?: string;
  exclude_st?: boolean;
  exclude_limit_up?: boolean;
  min_price?: number;
  max_price?: number;
}

export async function runScreen(
  strategy: string,
  limit = 20,
  constraints: ScreenConstraints = {},
): Promise<ScreenResult> {
  const { data } = await api.post<ScreenResult>('/screen/run', {
    strategy,
    limit,
    use_parallel: true,
    ...constraints,
  });
  return data;
}
