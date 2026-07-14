import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { trainingScreen, trainingKline } from '../api/training';
import type { TrainingScreenResponse, KLineRangeResponse, StockScore, KLineItem } from '../api/types';
import { STRATEGIES } from '../lib/constants';
import Card from '../components/ui/Card';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { formatNumber, formatPct, formatVolume } from '../lib/formatters';

function downloadJSON(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function Training() {
  const [screenDate, setScreenDate] = useState('');
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);
  const [minScore, setMinScore] = useState(60);
  const [screenDays, setScreenDays] = useState(120);
  const [screenResult, setScreenResult] = useState<TrainingScreenResponse | null>(null);

  const [klineCode, setKlineCode] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [klineResult, setKlineResult] = useState<KLineRangeResponse | null>(null);

  const screenMutation = useMutation({
    mutationFn: () =>
      trainingScreen({
        date: screenDate,
        strategies: selectedStrategies,
        min_score: minScore,
        days: screenDays,
      }),
    onSuccess: (data) => setScreenResult(data),
  });

  const klineMutation = useMutation({
    mutationFn: () =>
      trainingKline({ ts_code: klineCode, start_date: startDate, end_date: endDate }),
    onSuccess: (data) => setKlineResult(data),
  });

  const handleScreen = () => {
    if (!screenDate.trim()) return;
    screenMutation.mutate();
  };

  const handleKline = () => {
    if (!klineCode.trim() || !startDate.trim() || !endDate.trim()) return;
    klineMutation.mutate();
  };

  const toggleStrategy = (alias: string) => {
    setSelectedStrategies((prev) =>
      prev.includes(alias) ? prev.filter((s) => s !== alias) : [...prev, alias],
    );
  };

  const selectStock = (s: StockScore) => {
    setKlineCode(s.ts_code);
    setKlineResult(null);
  };

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold text-text-primary">训练数据导出</h1>

      <div className="grid grid-cols-2 gap-4">
        {/* ── Step 1 · 当日战法筛选 ── */}
        <Card title="Step 1 · 当日战法筛选">
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-text-muted mb-1">日期 (YYYYMMDD)</label>
              <input
                type="text"
                value={screenDate}
                onChange={(e) => setScreenDate(e.target.value)}
                placeholder="如 20260101"
                className="w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent-gold"
              />
            </div>

            <div>
              <label className="block text-xs text-text-muted mb-1">战法</label>
              <div className="flex flex-wrap gap-2">
                {STRATEGIES.map((s) => (
                  <label
                    key={s.alias}
                    className="flex items-center gap-1.5 text-xs text-text-secondary cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      className="accent-accent-gold"
                      checked={selectedStrategies.includes(s.alias)}
                      onChange={() => toggleStrategy(s.alias)}
                    />
                    {s.label}
                  </label>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex-1">
                <label className="block text-xs text-text-muted mb-1">最低分数</label>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={minScore}
                  onChange={(e) => setMinScore(Number(e.target.value))}
                  className="w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary outline-none focus:border-accent-gold"
                />
              </div>
              <div className="w-32">
                <label className="block text-xs text-text-muted mb-1">回看天数</label>
                <select
                  value={screenDays}
                  onChange={(e) => setScreenDays(Number(e.target.value))}
                  className="w-full rounded border border-border bg-bg-primary px-2 py-1.5 text-sm text-text-primary"
                >
                  {[60, 120, 150].map((n) => (
                    <option key={n} value={n}>{n} 天</option>
                  ))}
                </select>
              </div>
            </div>

            <button
              onClick={handleScreen}
              disabled={screenMutation.isPending || !screenDate.trim()}
              className="rounded-lg border border-accent-gold/40 bg-gradient-to-b from-accent-gold/30 to-accent-gold/15 px-5 py-2 text-sm font-bold tracking-wider text-accent-gold shadow-[0_0_20px_-8px_rgba(245,158,11,0.5)] transition-all hover:from-accent-gold/40 hover:to-accent-gold/25 hover:shadow-[0_0_24px_-6px_rgba(245,158,11,0.7)] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
            >
              {screenMutation.isPending ? '筛选中...' : '开始筛选'}
            </button>
          </div>

          {screenMutation.isPending && (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          )}

          {screenMutation.isError && !screenMutation.isPending && (
            <div className="mt-4 text-sm text-down">
              筛选失败：{(screenMutation.error as Error)?.message || '未知错误'}
            </div>
          )}

          {screenResult && !screenMutation.isPending && (
            <div className="mt-4 pt-4 border-t border-border/40">
              <div className="text-xs text-text-muted mb-2">
                <span className="text-text-primary font-bold">{screenResult.date}</span>
                {' · '}
                扫描 {screenResult.total_scanned} 只 · 命中 {screenResult.results.length} 只
              </div>
              {screenResult.results.length === 0 ? (
                <div className="text-center py-6 text-text-muted text-sm">无符合条件的股票</div>
              ) : (
                <div className="overflow-x-auto max-h-96 overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead className="sticky top-0 bg-bg-card">
                      <tr className="border-b border-border text-text-muted">
                        <th className="text-left py-1.5 px-2">代码</th>
                        <th className="text-left py-1.5 px-2">名称</th>
                        <th className="text-right py-1.5 px-2">总分</th>
                        <th className="text-left py-1.5 px-2">评级</th>
                      </tr>
                    </thead>
                    <tbody>
                      {screenResult.results.map((s) => (
                        <tr
                          key={s.ts_code}
                          onClick={() => selectStock(s)}
                          className={`border-b border-border/50 cursor-pointer hover:bg-bg-hover ${
                            klineCode === s.ts_code ? 'bg-accent-gold/10' : ''
                          }`}
                        >
                          <td className="py-1.5 px-2 font-mono text-accent-gold">{s.ts_code}</td>
                          <td className="py-1.5 px-2 text-text-primary">{s.name}</td>
                          <td className="py-1.5 px-2 text-right font-mono font-bold">
                            {formatNumber(s.score, 1)}
                          </td>
                          <td className="py-1.5 px-2 text-text-secondary">{s.rating}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* ── Step 2 · K线数据导出 ── */}
        <Card title="Step 2 · K线数据导出">
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-text-muted mb-1">
                股票代码
                {klineCode && (
                  <span className="ml-2 text-accent-gold font-mono">已选: {klineCode}</span>
                )}
              </label>
              <input
                type="text"
                value={klineCode}
                onChange={(e) => setKlineCode(e.target.value)}
                placeholder="如 600487.SH（点击左侧表格自动填入）"
                className="w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent-gold"
              />
            </div>

            <div className="flex items-center gap-3">
              <div className="flex-1">
                <label className="block text-xs text-text-muted mb-1">起始日期 (YYYYMMDD)</label>
                <input
                  type="text"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  placeholder="如 20260101"
                  className="w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent-gold"
                />
              </div>
              <div className="flex-1">
                <label className="block text-xs text-text-muted mb-1">结束日期 (YYYYMMDD)</label>
                <input
                  type="text"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  placeholder="如 20260601"
                  className="w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent-gold"
                />
              </div>
            </div>

            <button
              onClick={handleKline}
              disabled={
                klineMutation.isPending ||
                !klineCode.trim() ||
                !startDate.trim() ||
                !endDate.trim()
              }
              className="rounded-lg border border-accent-gold/40 bg-gradient-to-b from-accent-gold/30 to-accent-gold/15 px-5 py-2 text-sm font-bold tracking-wider text-accent-gold shadow-[0_0_20px_-8px_rgba(245,158,11,0.5)] transition-all hover:from-accent-gold/40 hover:to-accent-gold/25 hover:shadow-[0_0_24px_-6px_rgba(245,158,11,0.7)] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
            >
              {klineMutation.isPending ? '导出中...' : '导出K线'}
            </button>
          </div>

          {klineMutation.isPending && (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          )}

          {klineMutation.isError && !klineMutation.isPending && (
            <div className="mt-4 text-sm text-down">
              导出失败：{(klineMutation.error as Error)?.message || '未知错误'}
            </div>
          )}

          {klineResult && !klineMutation.isPending && (
            <div className="mt-4 pt-4 border-t border-border/40 space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-xs text-text-muted">
                  <span className="text-text-primary font-mono font-bold">{klineResult.ts_code}</span>
                  {' · '}
                  共 {klineResult.klines.length} 条 K 线
                </div>
                <button
                  onClick={() =>
                    downloadJSON(
                      klineResult.klines,
                      `${klineResult.ts_code}_${startDate}_${endDate}.json`,
                    )
                  }
                  disabled={klineResult.klines.length === 0}
                  className="rounded-lg border border-accent-gold/40 bg-gradient-to-b from-accent-gold/30 to-accent-gold/15 px-4 py-1.5 text-xs font-bold tracking-wider text-accent-gold shadow-[0_0_20px_-8px_rgba(245,158,11,0.5)] transition-all hover:from-accent-gold/40 hover:to-accent-gold/25 hover:shadow-[0_0_24px_-6px_rgba(245,158,11,0.7)] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
                >
                  下载 JSON
                </button>
              </div>

              {klineResult.klines.length === 0 ? (
                <div className="text-center py-6 text-text-muted text-sm">该区间无 K 线数据</div>
              ) : (
                <div className="overflow-x-auto max-h-96 overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead className="sticky top-0 bg-bg-card">
                      <tr className="border-b border-border text-text-muted">
                        <th className="text-left py-1.5 px-2">日期</th>
                        <th className="text-right py-1.5 px-2">开盘</th>
                        <th className="text-right py-1.5 px-2">收盘</th>
                        <th className="text-right py-1.5 px-2">最高</th>
                        <th className="text-right py-1.5 px-2">最低</th>
                        <th className="text-right py-1.5 px-2">成交量</th>
                        <th className="text-right py-1.5 px-2">涨跌幅</th>
                      </tr>
                    </thead>
                    <tbody>
                      {klineResult.klines.map((k: KLineItem) => (
                        <tr key={k.date} className="border-b border-border/50">
                          <td className="py-1.5 px-2 text-text-secondary">{k.date}</td>
                          <td className="py-1.5 px-2 text-right font-mono">{formatNumber(k.open)}</td>
                          <td className="py-1.5 px-2 text-right font-mono">{formatNumber(k.close)}</td>
                          <td className="py-1.5 px-2 text-right font-mono">{formatNumber(k.high)}</td>
                          <td className="py-1.5 px-2 text-right font-mono">{formatNumber(k.low)}</td>
                          <td className="py-1.5 px-2 text-right font-mono">{formatVolume(k.volume)}</td>
                          <td
                            className={`py-1.5 px-2 text-right font-mono ${
                              k.pct_chg > 0 ? 'text-up' : k.pct_chg < 0 ? 'text-down' : 'text-text-secondary'
                            }`}
                          >
                            {formatPct(k.pct_chg)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
