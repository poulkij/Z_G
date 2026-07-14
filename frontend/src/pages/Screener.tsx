import { useState, useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { runScreen, type ScreenConstraints } from '../api/screen';
import { screenerScreen, historicalScreener } from '../api/screener';
import type { ScreenResult, StockScore, ScreenerResponse } from '../api/types';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ApiErrorState from '../components/ui/ApiErrorState';
import { STRATEGIES, HARD_FILTER_DESC } from '../lib/constants';
import { formatNumber } from '../lib/formatters';

const CATEGORY_COLORS: Record<string, string> = {
  买点: 'text-accent-green bg-accent-green/10 border-accent-green/30',
  形态: 'text-accent-blue bg-accent-blue/10 border-accent-blue/30',
  阶段: 'text-accent-purple bg-accent-purple/10 border-accent-purple/30',
  风控: 'text-accent-gold bg-accent-gold/10 border-accent-gold/30',
};

const DEFAULT_CONSTRAINTS: ScreenConstraints = {
  min_score: 0,
  min_b1_score: 0,
  min_trend_score: 0,
  min_volume_score: 0,
  max_risk_score: 100,
  industry: '',
  exclude_st: true,
  exclude_limit_up: false,
  min_price: 0,
  max_price: 0,
};

const MANC_STRATEGIES: Array<{ value: string; label: string }> = [
  { value: 'b1', label: 'B1 买点' },
  { value: 'b2', label: 'B2 确认' },
  { value: 'b3', label: 'B3 共识' },
  { value: 'perfect', label: '完美图形' },
  { value: 'safe', label: '安全' },
];

export default function Screener() {
  const [tab, setTab] = useState<'strategy' | 'manchester' | 'historical'>('strategy');

  const [selected, setSelected] = useState('B1');
  const [limit, setLimit] = useState(20);
  const [ran, setRan] = useState(false);
  const [showConstraints, setShowConstraints] = useState(false);
  const [constraints, setConstraints] = useState<ScreenConstraints>(DEFAULT_CONSTRAINTS);

  const [mancStrategy, setMancStrategy] = useState('b1');
  const [mancMaxStocks, setMancMaxStocks] = useState(500);

  const [histDate, setHistDate] = useState('');
  const [histStrategies, setHistStrategies] = useState<string[]>([]);
  const [histMinScore, setHistMinScore] = useState(0);
  const [histDays, setHistDays] = useState(250);
  const [histLimit, setHistLimit] = useState(100);

  const currentStrategy = useMemo(
    () => STRATEGIES.find((s) => s.alias === selected) ?? STRATEGIES[0],
    [selected],
  );

  const activeConstraintCount = useMemo(() => {
    let n = 0;
    if (constraints.min_score && constraints.min_score > 0) n++;
    if (constraints.min_b1_score && constraints.min_b1_score > 0) n++;
    if (constraints.min_trend_score && constraints.min_trend_score > 0) n++;
    if (constraints.min_volume_score && constraints.min_volume_score > 0) n++;
    if (constraints.max_risk_score !== undefined && constraints.max_risk_score < 100) n++;
    if (constraints.industry && constraints.industry.trim()) n++;
    if (constraints.exclude_st) n++;
    if (constraints.exclude_limit_up) n++;
    if (constraints.min_price && constraints.min_price > 0) n++;
    if (constraints.max_price && constraints.max_price > 0) n++;
    return n;
  }, [constraints]);

  const { data: result, isLoading, isError, error, refetch } = useQuery<ScreenResult>({
    queryKey: ['screen', selected, limit, constraints],
    queryFn: () => runScreen(selected, limit, constraints),
    enabled: false,
  });

  const manchesterMutation = useMutation<ScreenerResponse, Error>({
    mutationFn: () => screenerScreen(mancStrategy, mancMaxStocks),
  });

  const historicalMutation = useMutation<ScreenerResponse, Error>({
    mutationFn: () =>
      historicalScreener({
        date: histDate,
        strategies: histStrategies.length > 0 ? histStrategies : undefined,
        min_score: histMinScore,
        days: histDays,
        limit: histLimit,
      }),
  });

  const handleRun = async () => {
    setRan(true);
    await refetch();
  };

  const updateConstraint = <K extends keyof ScreenConstraints>(
    key: K,
    value: ScreenConstraints[K],
  ) => {
    setConstraints((c) => ({ ...c, [key]: value }));
  };

  const toggleHistStrategy = (alias: string) => {
    setHistStrategies((prev) =>
      prev.includes(alias) ? prev.filter((s) => s !== alias) : [...prev, alias],
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-text-primary">选股筛选</h1>
      </div>

      <div className="flex items-center gap-1 border-b border-border">
        {([['strategy', '战法选股'], ['manchester', '曼城评分'], ['historical', '历史选股']] as const).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${tab === key ? 'text-accent-gold border-b-2 border-accent-gold' : 'text-text-muted hover:text-text-primary'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'strategy' && (
        <>
          <Card>
            <div className="flex flex-wrap gap-2 mb-4">
              {STRATEGIES.map((s) => (
                <button
                  key={s.alias}
                  onClick={() => setSelected(s.alias)}
                  className={`px-3 py-1.5 rounded text-sm transition-colors flex items-center gap-1.5 ${
                    selected === s.alias
                      ? 'bg-accent-gold/20 text-accent-gold border border-accent-gold/50'
                      : 'bg-bg-hover text-text-secondary border border-border hover:text-text-primary'
                  }`}
                >
                  {s.label}
                  <span
                    className={`text-[9px] px-1 py-0.5 rounded border ${
                      selected === s.alias
                        ? 'border-accent-gold/30 text-accent-gold/80'
                        : CATEGORY_COLORS[s.category] ?? 'text-text-muted border-border'
                    }`}
                  >
                    {s.category}
                  </span>
                </button>
              ))}
            </div>

            <div className="rounded-lg border border-border/40 bg-bg-secondary/50 p-4 mb-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-text-primary">{currentStrategy.label} · 选股公式</span>
                  <span
                    className={`text-[9px] px-1.5 py-0.5 rounded border ${CATEGORY_COLORS[currentStrategy.category]}`}
                  >
                    {currentStrategy.category}
                  </span>
                </div>
                <span className="text-[10px] text-text-muted font-mono">criteria: {currentStrategy.alias}</span>
              </div>
              <pre className="text-xs text-text-secondary font-mono whitespace-pre-wrap leading-relaxed">
{currentStrategy.formula}
              </pre>
              <div className="mt-2 pt-2 border-t border-border/30 text-[10px] text-text-muted">
                {HARD_FILTER_DESC}
              </div>
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-muted">数量</span>
                <select
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  className="rounded border border-border bg-bg-primary px-2 py-1 text-sm text-text-primary"
                >
                  {[10, 20, 50, 100].map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={() => setShowConstraints((v) => !v)}
                className={`px-3 py-1.5 rounded text-sm border transition-colors flex items-center gap-1.5 ${
                  showConstraints
                    ? 'bg-accent-blue/20 text-accent-blue border-accent-blue/50'
                    : 'bg-bg-hover text-text-secondary border-border hover:text-text-primary'
                }`}
              >
                约束{activeConstraintCount > 0 && (
                  <span className="text-[10px] bg-accent-gold/30 text-accent-gold px-1.5 rounded-full">
                    {activeConstraintCount}
                  </span>
                )}
                <span className="text-[10px]">{showConstraints ? '▲' : '▼'}</span>
              </button>
              <Button onClick={handleRun} disabled={isLoading}>
                {isLoading ? '筛选中...' : '开始筛选'}
              </Button>
            </div>

            {showConstraints && (
              <div className="mt-4 pt-4 border-t border-border/40 space-y-4">
                <div className="text-xs font-bold text-text-primary mb-2">评分约束</div>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  <ConstraintSlider
                    label="最低综合分"
                    value={constraints.min_score ?? 0}
                    onChange={(v) => updateConstraint('min_score', v)}
                  />
                  <ConstraintSlider
                    label="最低 B1 分"
                    value={constraints.min_b1_score ?? 0}
                    onChange={(v) => updateConstraint('min_b1_score', v)}
                  />
                  <ConstraintSlider
                    label="最低趋势分"
                    value={constraints.min_trend_score ?? 0}
                    onChange={(v) => updateConstraint('min_trend_score', v)}
                  />
                  <ConstraintSlider
                    label="最低量价分"
                    value={constraints.min_volume_score ?? 0}
                    onChange={(v) => updateConstraint('min_volume_score', v)}
                  />
                  <ConstraintSlider
                    label="最高风险分"
                    value={constraints.max_risk_score ?? 100}
                    max={100}
                    onChange={(v) => updateConstraint('max_risk_score', v)}
                  />
                </div>

                <div className="text-xs font-bold text-text-primary mb-2">基础约束</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-text-muted block mb-1">行业（逗号分隔，如 有色金属,白酒）</label>
                    <input
                      type="text"
                      value={constraints.industry ?? ''}
                      onChange={(e) => updateConstraint('industry', e.target.value)}
                      placeholder="留空=不限"
                      className="w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent-gold"
                    />
                  </div>
                  <div className="flex items-end gap-3">
                    <div className="flex-1">
                      <label className="text-xs text-text-muted block mb-1">最低股价</label>
                      <input
                        type="number"
                        min={0}
                        step={1}
                        value={constraints.min_price ?? 0}
                        onChange={(e) => updateConstraint('min_price', Number(e.target.value))}
                        placeholder="0"
                        className="w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent-gold"
                      />
                    </div>
                    <div className="flex-1">
                      <label className="text-xs text-text-muted block mb-1">最高股价</label>
                      <input
                        type="number"
                        min={0}
                        step={1}
                        value={constraints.max_price ?? 0}
                        onChange={(e) => updateConstraint('max_price', Number(e.target.value))}
                        placeholder="0=不限"
                        className="w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent-gold"
                      />
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                    <input
                      type="checkbox"
                      checked={constraints.exclude_st ?? true}
                      onChange={(e) => updateConstraint('exclude_st', e.target.checked)}
                      className="accent-accent-gold"
                    />
                    排除 ST / *ST
                  </label>
                  <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                    <input
                      type="checkbox"
                      checked={constraints.exclude_limit_up ?? false}
                      onChange={(e) => updateConstraint('exclude_limit_up', e.target.checked)}
                      className="accent-accent-gold"
                    />
                    排除当日涨停
                  </label>
                  <button
                    onClick={() => setConstraints(DEFAULT_CONSTRAINTS)}
                    className="ml-auto text-xs text-text-muted hover:text-accent-red transition-colors"
                  >
                    重置约束
                  </button>
                </div>
              </div>
            )}
          </Card>

          {isLoading && (
            <div className="flex items-center justify-center py-16">
              <LoadingSpinner size="lg" />
            </div>
          )}

          {ran && isError && !isLoading && (
            <ApiErrorState
              message={(error as Error)?.message || '筛选失败'}
              onRetry={() => refetch()}
            />
          )}

          {!ran && !result && (
            <Card>
              <div className="flex flex-col items-center text-center py-8">
                <div className="text-3xl mb-3 text-accent-gold opacity-60">◎</div>
                <div className="text-sm font-bold text-text-primary mb-1">选择战法开始筛选</div>
                <div className="text-xs text-text-muted max-w-md">在上方选择战法(如 B1 / B2 / 长安战法 等),可展开"约束"添加评分/行业/价格等过滤条件,设定数量后点击"开始筛选",系统会扫描全市场命中该战法的个股。</div>
              </div>
            </Card>
          )}

          {ran && result && !isLoading && (
            <Card title={`筛选结果 — ${result.strategy} (${result.count} 只)`}>
              {result.stocks.length === 0 ? (
                <div className="text-center py-8 text-text-muted">
                  无符合条件的股票
                  {activeConstraintCount > 0 && (
                    <div className="text-xs mt-2">当前有 {activeConstraintCount} 个约束生效，可尝试放宽约束</div>
                  )}
                </div>
              ) : (
                <ScoreTable stocks={result.stocks} />
              )}
            </Card>
          )}
        </>
      )}

      {tab === 'manchester' && (
        <>
          <Card>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div>
                <label className="text-xs text-text-muted block mb-1">策略</label>
                <select
                  value={mancStrategy}
                  onChange={(e) => setMancStrategy(e.target.value)}
                  className="w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary"
                >
                  {MANC_STRATEGIES.map((s) => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-text-muted block mb-1">最大股票数</label>
                <select
                  value={mancMaxStocks}
                  onChange={(e) => setMancMaxStocks(Number(e.target.value))}
                  className="w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary"
                >
                  {[100, 300, 500].map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>
              <Button
                onClick={() => manchesterMutation.mutate()}
                disabled={manchesterMutation.isPending}
              >
                {manchesterMutation.isPending ? '评分中...' : '开始评分'}
              </Button>
            </div>
          </Card>

          {manchesterMutation.isPending && (
            <div className="flex items-center justify-center py-16">
              <LoadingSpinner size="lg" />
            </div>
          )}

          {manchesterMutation.isError && !manchesterMutation.isPending && (
            <ApiErrorState
              message={manchesterMutation.error?.message || '评分失败'}
              onRetry={() => manchesterMutation.mutate()}
            />
          )}

          {!manchesterMutation.data && !manchesterMutation.isPending && !manchesterMutation.isError && (
            <Card>
              <div className="flex flex-col items-center text-center py-8">
                <div className="text-3xl mb-3 text-accent-gold opacity-60">◎</div>
                <div className="text-sm font-bold text-text-primary mb-1">选择策略开始评分</div>
                <div className="text-xs text-text-muted max-w-md">选择策略和最大股票数,点击"开始评分"对全市场个股进行曼城评分排序。</div>
              </div>
            </Card>
          )}

          {manchesterMutation.data && !manchesterMutation.isPending && (
            <Card title={`评分结果 (${manchesterMutation.data.total} 只)`}>
              {manchesterMutation.data.results.length === 0 ? (
                <div className="text-center py-8 text-text-muted">无符合条件的股票</div>
              ) : (
                <ScoreTable stocks={manchesterMutation.data.results} />
              )}
            </Card>
          )}
        </>
      )}

      {tab === 'historical' && (
        <>
          <Card>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="text-xs text-text-muted block mb-1">日期 (YYYYMMDD)</label>
                <input
                  type="text"
                  value={histDate}
                  onChange={(e) => setHistDate(e.target.value)}
                  placeholder="如 20260101"
                  maxLength={8}
                  className="w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent-gold"
                />
              </div>
              <div>
                <label className="text-xs text-text-muted block mb-1">最低综合分</label>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={histMinScore}
                  onChange={(e) => setHistMinScore(Number(e.target.value))}
                  className="w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary outline-none focus:border-accent-gold"
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="text-xs text-text-muted block mb-2">战法 (可多选，不选=全部)</label>
              <div className="flex flex-wrap gap-2">
                {STRATEGIES.map((s) => (
                  <label
                    key={s.alias}
                    className={`px-3 py-1.5 rounded text-sm border cursor-pointer transition-colors flex items-center gap-1.5 ${
                      histStrategies.includes(s.alias)
                        ? 'bg-accent-gold/20 text-accent-gold border-accent-gold/50'
                        : 'bg-bg-hover text-text-secondary border-border hover:text-text-primary'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={histStrategies.includes(s.alias)}
                      onChange={() => toggleHistStrategy(s.alias)}
                      className="accent-accent-gold"
                    />
                    {s.label}
                  </label>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-muted">回看天数</span>
                <select
                  value={histDays}
                  onChange={(e) => setHistDays(Number(e.target.value))}
                  className="rounded border border-border bg-bg-primary px-2 py-1 text-sm text-text-primary"
                >
                  {[120, 150, 250].map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-muted">返回数量</span>
                <select
                  value={histLimit}
                  onChange={(e) => setHistLimit(Number(e.target.value))}
                  className="rounded border border-border bg-bg-primary px-2 py-1 text-sm text-text-primary"
                >
                  {[50, 100, 200].map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>
              <Button
                onClick={() => historicalMutation.mutate()}
                disabled={!histDate || historicalMutation.isPending}
              >
                {historicalMutation.isPending ? '筛选中...' : '开始筛选'}
              </Button>
            </div>
          </Card>

          {historicalMutation.isPending && (
            <div className="flex items-center justify-center py-16">
              <LoadingSpinner size="lg" />
            </div>
          )}

          {historicalMutation.isError && !historicalMutation.isPending && (
            <ApiErrorState
              message={historicalMutation.error?.message || '历史筛选失败'}
              onRetry={() => historicalMutation.mutate()}
            />
          )}

          {!historicalMutation.data && !historicalMutation.isPending && !historicalMutation.isError && (
            <Card>
              <div className="flex flex-col items-center text-center py-8">
                <div className="text-3xl mb-3 text-accent-gold opacity-60">◎</div>
                <div className="text-sm font-bold text-text-primary mb-1">填写条件开始历史筛选</div>
                <div className="text-xs text-text-muted max-w-md">输入历史日期(YYYYMMDD格式),选择战法和评分条件,回溯该日期全市场战法命中情况。</div>
              </div>
            </Card>
          )}

          {historicalMutation.data && !historicalMutation.isPending && (
            <Card title={`历史筛选结果 (${historicalMutation.data.total} 只)`}>
              {historicalMutation.data.results.length === 0 ? (
                <div className="text-center py-8 text-text-muted">无符合条件的股票</div>
              ) : (
                <ScoreTable stocks={historicalMutation.data.results} />
              )}
            </Card>
          )}
        </>
      )}
    </div>
  );
}

function ScoreTable({ stocks }: { stocks: StockScore[] }) {
  const navigate = useNavigate();
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-text-muted">
            <th className="text-left py-2 px-2">代码</th>
            <th className="text-left py-2 px-2">名称</th>
            <th className="text-right py-2 px-2">总分</th>
            <th className="text-right py-2 px-2">B1</th>
            <th className="text-right py-2 px-2">趋势</th>
            <th className="text-right py-2 px-2">量价</th>
            <th className="text-right py-2 px-2">风险</th>
            <th className="text-left py-2 px-2">评级</th>
            <th className="text-left py-2 px-2">操作</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((s) => (
            <tr key={s.ts_code} className="border-b border-border/50 hover:bg-bg-hover/50">
              <td className="py-2 px-2 font-mono text-accent-gold">{s.ts_code}</td>
              <td className="py-2 px-2 text-text-primary">{s.name}</td>
              <td className="py-2 px-2 text-right font-mono font-bold">{formatNumber(s.score, 1)}</td>
              <td className="py-2 px-2 text-right font-mono">{formatNumber(s.b1_score, 1)}</td>
              <td className="py-2 px-2 text-right font-mono">{formatNumber(s.trend_score, 1)}</td>
              <td className="py-2 px-2 text-right font-mono">{formatNumber(s.volume_score, 1)}</td>
              <td className="py-2 px-2 text-right font-mono">{formatNumber(s.risk_score, 1)}</td>
              <td className="py-2 px-2 text-text-secondary">{s.rating}</td>
              <td className="py-2 px-2">
                <button
                  onClick={() => navigate(`/stock/${s.ts_code}`)}
                  className="text-xs text-accent-blue hover:underline"
                >
                  分析
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ConstraintSlider({
  label,
  value,
  max = 100,
  step = 5,
  onChange,
}: {
  label: string;
  value: number;
  max?: number;
  step?: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="text-xs text-text-muted">{label}</label>
        <span className="text-xs font-mono text-accent-gold tabular-nums">{value}</span>
      </div>
      <input
        type="range"
        min={0}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-accent-gold"
      />
    </div>
  );
}
