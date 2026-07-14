import api from './client';
import type { PortfolioDiagnoseResponse } from './types';

export async function diagnosePortfolio(holdings: string[], days = 100): Promise<PortfolioDiagnoseResponse> {
  const { data } = await api.post<PortfolioDiagnoseResponse>('/portfolio/diagnose', { holdings, days });
  return data;
}
