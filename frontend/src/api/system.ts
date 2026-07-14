import api from './client';

export async function syncStock(tsCode: string, days = 730, indicators = true) {
  const { data } = await api.post('/system/sync/' + tsCode, null, { params: { days, indicators } });
  return data;
}
