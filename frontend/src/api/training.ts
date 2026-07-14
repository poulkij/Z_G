import api from './client';
import type { TrainingScreenResponse, KLineRangeResponse } from './types';

export interface TrainingScreenParams {
  date: string;
  strategies?: string[];
  min_score?: number;
  days?: number;
}

export async function trainingScreen(params: TrainingScreenParams): Promise<TrainingScreenResponse> {
  const { data } = await api.post<TrainingScreenResponse>('/training/screen', params);
  return data;
}

export interface KLineRangeParams {
  ts_code: string;
  start_date: string;
  end_date: string;
}

export async function trainingKline(params: KLineRangeParams): Promise<KLineRangeResponse> {
  const { data } = await api.post<KLineRangeResponse>('/training/kline', params);
  return data;
}
