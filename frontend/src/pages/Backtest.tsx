import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  runBacktest,
  tuneBacktest,
  historicalScreen,
  type BacktestParams,
  type TuneParams,
  type HistoricalScreenParams,
} from '../api/backtest';
import type { BacktestResult, TuneResult, HistoricalScreenResult } from '../api/types';
import { STRATEGIES } from '../lib/constants';
import Card from '../components/ui/Card';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { formatNumber, formatPct } from '../lib/formatters';

const INPUT_CLASS =
  'w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent-gold';
const SELECT_CLASS =
  'w-full rounded border border-border bg-bg-primary px-2 py-1.5 text-sm text-text-primary';
const GOLD_BTN =
  'rounded-lg border border-accent-gold/40 bg-gradient-to-b from-accent-gold/30 to-accent-gold/15 px-5 py-2 text-sm font-bold tracking-wider text-accent-gold shadow-[0_0_20px_-8px_rgba(245,158,11,0.5)] transition-all hover:from-accent-gold/40 hover:to-accent-gold/25 hover:shadow-[0_0_24px_-6px_rgba(245,158,11,0.7)] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none';
const DAYS_OPTIONS = [120, 250, 365, 500, 730];

function normalizeCode(code: string): string {
  const c = code.trim().toUpperCase();
  if (/^\d{6}$/.test(c)) return c.startsWith('6') ? `${c}.SH` : `${c}.SZ`;
  return c;
}

function buildRange(min: number, max: number, step: number): number[] {
  const arr: number[] = [];
  const count = Math.round((max - min) / step);
  for (let i = 0; i <= count; i++) arr.push(Number((min + i * step).toFixed(4)));
  return arr;
}

function formatScore(metric: string, score: number): string {
  if (metric === 'win_rate') return `${(score * 100).toFixed(1)}%`;
  if (metric === 'total_return') return formatPct(score);
  return formatNumber(score);
}

function renderCellByKey(key: string, v: unknown): string {
  if (typeof v === 'number') {
    if (key === 'win_rate') return `${(v * 100).toFixed(1)}%`;
    if (key.includes('pct') || key === 'total_return' || key === 'max_drawdown' || key === 'avg_return')
      return formatPct(v);
    return formatNumber(v);
  }
  if (v === null || v === undefined) return '--';
  return String(v);
}

function RangeField({
  label,
  min,
  max,
  step,
  value,
  onChange,
  display,
}: {
  label: string;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (v: number) => void;
  display?: (v: number) => string;
}) {
  const fmt = display ?? ((v: number) => String(v));
  const count = Math.round((value - min) / step) + 1;
  return (
    <div>
      <div className="flex justify-between text-xs text-text-muted mb-1">
        <span>{label}</span>
        <span className="font-mono text-text-secondary">
          {fmt(min)} → {fmt(value)} · {count} 值
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-accent-gold"
      />
    </div>
  );
}

function ErrorBlock({ error }: { error: unknown }) {
  const msg = error instanceof Error ? error.message : '请求失败';
  return (
    <Card>
      <div className="text-sm text-down">{msg}</div>
    </Card>
  );
}

function SingleBacktest() {
  const [tsCode, setTsCode] = useState('');
  const [days, setDays] = useState(250);
  const [stopLoss, setStopLoss] = useState(0.07);
  const [takeProfit, setTakeProfit] = useState(0.15);
  const [result, setResult] = useState<BacktestResult | null>(null);

  const mutation = useMutation({
    mutationFn: (params: BacktestParams) => runBacktest(params),
    onSuccess: (data) => setResult(data),
  });

  const handleRun = () => {
    if (!tsCode.trim()) return;
    const code = normalizeCode(tsCode);
    setTsCode(code);
    mutation.mutate({
      ts_code: code,
      days,
      stop_loss_pct: stopLoss,
      take_profit_pct: takeProfit,
    });
  };

  const cards = result
    ? [
        {
          label: '总收益',
          value: formatPct(result.total_return),
          color: result.total_return >= 0 ? '#ef4444' : '#22c55e',
        },
        { label: '胜率', value: `${(result.win_rate * 100).toFixed(1)}%`, color: '#f59e0b' },
        { label: '盈亏比', value: formatNumber(result.profit_factor), color: '#3b82f6' },
        { label: '最大回撤', value: formatPct(-Math.abs(result.max_drawdown)), color: '#ef4444' },
        {
          label: '平均收益',
          value: formatPct(result.avg_return),
          color: result.avg_return >= 0 ? '#ef4444' : '#22c55e',
        },
        { label: '交易次数', value: String(result.total_trades), color: '#06b6d4' },
      ]
    : [];

  return (
    <div className="space-y-4">
      <Card title="回测配置">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[180px]">
            <label className="block text-xs text-text-muted mb-1">股票代码</label>
            <input
              type="text"
              value={tsCode}
              onChange={(e) => setTsCode(e.target.value)}
              placeholder="如 600487.SH"
              className={INPUT_CLASS}
            />
          </div>
          <div className="w-32">
            <label className="block text-xs text-text-muted mb-1">回测天数</label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className={SELECT_CLASS}
            >
              {DAYS_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  {n} 天
                </option>
              ))}
            </select>
          </div>
          <div className="w-32">
            <label className="block text-xs text-text-muted mb-1">止损位</label>
            <input
              type="number"
              step={0.01}
              min={0}
              max={1}
              value={stopLoss}
              onChange={(e) => setStopLoss(Number(e.target.value))}
              className={INPUT_CLASS}
            />
          </div>
          <div className="w-32">
            <label className="block text-xs text-text-muted mb-1">止盈位</label>
            <input
              type="number"
              step={0.01}
              min={0}
              max={1}
              value={takeProfit}
              onChange={(e) => setTakeProfit(Number(e.target.value))}
              className={INPUT_CLASS}
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleRun}
              disabled={mutation.isPending || !tsCode.trim()}
              className={GOLD_BTN}
            >
              {mutation.isPending ? '回测中...' : '▶ 开始回测'}
            </button>
          </div>
        </div>
      </Card>

      {mutation.isPending && (
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {mutation.isError && <ErrorBlock error={mutation.error} />}

      {result && !mutation.isPending && (
        <>
          <div className="grid grid-cols-6 gap-3">
            {cards.map((item) => (
              <Card key={item.label}>
                <div className="text-center">
                  <div className="text-xs text-text-muted">{item.label}</div>
                  <div className="text-lg font-bold mt-1" style={{ color: item.color }}>
                    {item.value}
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <Card title={`交易明细 (${result.trades.length} 笔)`}>
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-bg-card">
                  <tr className="border-b border-border text-text-muted">
                    <th className="text-left py-1.5 px-2">买入日期</th>
                    <th className="text-right py-1.5 px-2">买入价</th>
                    <th className="text-left py-1.5 px-2">卖出日期</th>
                    <th className="text-right py-1.5 px-2">卖出价</th>
                    <th className="text-right py-1.5 px-2">盈亏%</th>
                    <th className="text-right py-1.5 px-2">持仓天数</th>
                    <th className="text-left py-1.5 px-2">退出原因</th>
                  </tr>
                </thead>
                <tbody>
                  {result.trades.map((t, i) => (
                    <tr key={i} className="border-b border-border/50">
                      <td className="py-1.5 px-2 text-text-secondary">{t.entry_date}</td>
                      <td className="py-1.5 px-2 text-right font-mono">{formatNumber(t.entry_price)}</td>
                      <td className="py-1.5 px-2 text-text-secondary">{t.exit_date || '--'}</td>
                      <td className="py-1.5 px-2 text-right font-mono">
                        {t.exit_price != null ? formatNumber(t.exit_price) : '--'}
                      </td>
                      <td
                        className={`py-1.5 px-2 text-right font-mono font-bold ${
                          t.pnl_pct >= 0 ? 'text-up' : 'text-down'
                        }`}
                      >
                        {formatPct(t.pnl_pct)}
                      </td>
                      <td className="py-1.5 px-2 text-right">{t.hold_days}</td>
                      <td className="py-1.5 px-2 text-text-muted">{t.exit_reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function TuneBacktest() {
  const [tsCode, setTsCode] = useState('');
  const [days, setDays] = useState(250);
  const [scoreMetric, setScoreMetric] = useState('win_rate');
  const [slMax, setSlMax] = useState(0.1);
  const [tpMax, setTpMax] = useState(0.2);
  const [mhdMax, setMhdMax] = useState(20);
  const [result, setResult] = useState<TuneResult | null>(null);

  const mutation = useMutation({
    mutationFn: (params: TuneParams) => tuneBacktest(params),
    onSuccess: (data) => setResult(data),
  });

  const handleRun = () => {
    if (!tsCode.trim()) return;
    const code = normalizeCode(tsCode);
    setTsCode(code);
    const param_grid = {
      stop_loss_pct: buildRange(0.03, slMax, 0.01),
      take_profit_pct: buildRange(0.05, tpMax, 0.05),
      max_hold_days: buildRange(5, mhdMax, 5),
    };
    mutation.mutate({ ts_code: code, param_grid, days, score_metric: scoreMetric });
  };

  const pctDisplay = (v: number) => `${(v * 100).toFixed(0)}%`;
  const resultKeys = result && result.all_results.length > 0 ? Object.keys(result.all_results[0]) : [];

  return (
    <div className="space-y-4">
      <Card title="调优配置">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[180px]">
            <label className="block text-xs text-text-muted mb-1">股票代码</label>
            <input
              type="text"
              value={tsCode}
              onChange={(e) => setTsCode(e.target.value)}
              placeholder="如 600487.SH"
              className={INPUT_CLASS}
            />
          </div>
          <div className="w-32">
            <label className="block text-xs text-text-muted mb-1">回测天数</label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className={SELECT_CLASS}
            >
              {DAYS_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  {n} 天
                </option>
              ))}
            </select>
          </div>
          <div className="w-40">
            <label className="block text-xs text-text-muted mb-1">评分指标</label>
            <select
              value={scoreMetric}
              onChange={(e) => setScoreMetric(e.target.value)}
              className={SELECT_CLASS}
            >
              <option value="win_rate">胜率 win_rate</option>
              <option value="profit_factor">盈亏比 profit_factor</option>
              <option value="total_return">总收益 total_return</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={handleRun}
              disabled={mutation.isPending || !tsCode.trim()}
              className={GOLD_BTN}
            >
              {mutation.isPending ? '调优中...' : '▶ 开始调优'}
            </button>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <RangeField
            label="止损位 stop_loss_pct"
            min={0.03}
            max={0.15}
            step={0.01}
            value={slMax}
            onChange={setSlMax}
            display={pctDisplay}
          />
          <RangeField
            label="止盈位 take_profit_pct"
            min={0.05}
            max={0.3}
            step={0.05}
            value={tpMax}
            onChange={setTpMax}
            display={pctDisplay}
          />
          <RangeField
            label="最大持仓天数 max_hold_days"
            min={5}
            max={30}
            step={5}
            value={mhdMax}
            onChange={setMhdMax}
          />
        </div>
      </Card>

      {mutation.isPending && (
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {mutation.isError && <ErrorBlock error={mutation.error} />}

      {result && !mutation.isPending && (
        <>
          <Card highlight title="最佳参数">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(result.best_params).map(([k, v]) => (
                <div key={k} className="rounded border border-border/40 bg-bg-primary/50 px-3 py-2">
                  <div className="text-xs text-text-muted">{k}</div>
                  <div className="text-sm font-mono font-bold text-accent-gold mt-0.5">
                    {k.includes('pct') ? formatPct(v) : formatNumber(v)}
                  </div>
                </div>
              ))}
              <div className="rounded border border-accent-gold/40 bg-accent-gold/10 px-3 py-2">
                <div className="text-xs text-text-muted">best_score ({scoreMetric})</div>
                <div className="text-sm font-mono font-bold text-accent-gold mt-0.5">
                  {formatScore(scoreMetric, result.best_score)}
                </div>
              </div>
            </div>
          </Card>

          <Card title={`全部结果 (${result.all_results.length} 组合)`}>
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-bg-card">
                  <tr className="border-b border-border text-text-muted">
                    {resultKeys.map((k) => (
                      <th key={k} className="text-right py-1.5 px-2 whitespace-nowrap">
                        {k}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.all_results.map((row, i) => (
                    <tr key={i} className="border-b border-border/50">
                      {resultKeys.map((k) => (
                        <td key={k} className="text-right py-1.5 px-2 font-mono">
                          {renderCellByKey(k, row[k])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function HistoricalScreenTab() {
  const [date, setDate] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [minScore, setMinScore] = useState(60);
  const [result, setResult] = useState<HistoricalScreenResult | null>(null);

  const mutation = useMutation({
    mutationFn: (params: HistoricalScreenParams) => historicalScreen(params),
    onSuccess: (data) => setResult(data),
  });

  const handleRun = () => {
    if (!date.trim()) return;
    mutation.mutate({
      date_range: { end: date.trim() },
      criteria: { strategies: selected, min_score: minScore },
    });
  };

  const toggle = (alias: string) =>
    setSelected((prev) =>
      prev.includes(alias) ? prev.filter((s) => s !== alias) : [...prev, alias]
    );

  return (
    <div className="space-y-4">
      <Card title="选股回测配置">
        <div className="flex flex-wrap items-end gap-4">
          <div className="w-40">
            <label className="block text-xs text-text-muted mb-1">截止日期</label>
            <input
              type="text"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              placeholder="YYYYMMDD"
              className={INPUT_CLASS}
            />
          </div>
          <div className="w-32">
            <label className="block text-xs text-text-muted mb-1">最低评分</label>
            <input
              type="number"
              min={0}
              max={100}
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className={INPUT_CLASS}
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleRun}
              disabled={mutation.isPending || !date.trim()}
              className={GOLD_BTN}
            >
              {mutation.isPending ? '筛选中...' : '▶ 开始筛选'}
            </button>
          </div>
        </div>

        <div className="mt-4">
          <div className="text-xs text-text-muted mb-2">
            战法选择 ({selected.length}/{STRATEGIES.length})
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {STRATEGIES.map((s) => (
              <label
                key={s.alias}
                className={`flex items-center gap-2 rounded border px-2 py-1.5 text-xs cursor-pointer transition-colors ${
                  selected.includes(s.alias)
                    ? 'border-accent-gold/50 bg-accent-gold/10 text-text-primary'
                    : 'border-border bg-bg-primary text-text-secondary hover:border-border/80'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selected.includes(s.alias)}
                  onChange={() => toggle(s.alias)}
                  className="accent-accent-gold"
                />
                <span>{s.label}</span>
              </label>
            ))}
          </div>
        </div>
      </Card>

      {mutation.isPending && (
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {mutation.isError && <ErrorBlock error={mutation.error} />}

      {result && !mutation.isPending && (
        <Card title={`筛选结果 (扫描 ${result.total_scanned} · 命中 ${result.results.length})`}>
          {result.results.length === 0 ? (
            <div className="text-sm text-text-muted py-8 text-center">无命中个股</div>
          ) : (
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-bg-card">
                  <tr className="border-b border-border text-text-muted">
                    <th className="text-left py-1.5 px-2">代码</th>
                    <th className="text-left py-1.5 px-2">名称</th>
                    <th className="text-right py-1.5 px-2">评分</th>
                    <th className="text-left py-1.5 px-2">评级</th>
                  </tr>
                </thead>
                <tbody>
                  {result.results.map((r) => (
                    <tr key={r.ts_code} className="border-b border-border/50">
                      <td className="py-1.5 px-2 text-text-secondary">{r.ts_code}</td>
                      <td className="py-1.5 px-2 text-text-primary">{r.name}</td>
                      <td className="py-1.5 px-2 text-right font-mono font-bold text-accent-gold">
                        {formatNumber(r.score)}
                      </td>
                      <td className="py-1.5 px-2 text-text-secondary">{r.rating}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

export default function Backtest() {
  const [tab, setTab] = useState<'single' | 'tune' | 'historical'>('single');
  const tabs: Array<{ key: typeof tab; label: string }> = [
    { key: 'single', label: '单股回测' },
    { key: 'tune', label: '参数调优' },
    { key: 'historical', label: '选股回测' },
  ];

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold text-text-primary">策略回测</h1>

      <div className="flex gap-4 border-b border-border">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              tab === t.key
                ? 'text-accent-gold border-b-2 border-accent-gold'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'single' && <SingleBacktest />}
      {tab === 'tune' && <TuneBacktest />}
      {tab === 'historical' && <HistoricalScreenTab />}
    </div>
  );
}
