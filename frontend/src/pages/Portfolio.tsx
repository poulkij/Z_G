import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { diagnosePortfolio } from '../api/portfolio';
import type { DiagnosisFull } from '../api/types';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { formatNumber } from '../lib/formatters';

const RISK_COLORS: Record<string, string> = {
  LOW: '#22c55e', MEDIUM: '#f59e0b', HIGH: '#f97316', CRITICAL: '#ef4444', UNKNOWN: '#64748b',
};

const RISK_BADGE: Record<string, 'success' | 'warning' | 'danger' | 'default'> = {
  LOW: 'success', MEDIUM: 'warning', HIGH: 'danger', CRITICAL: 'danger', UNKNOWN: 'default',
};

function parseCodes(text: string): string[] {
  return text.split(/[\n,，\s]+/)
    .map(s => s.trim().toUpperCase())
    .filter(s => s.length > 0)
    .map(s => /^\d{6}$/.test(s) ? (s.startsWith('6') ? `${s}.SH` : `${s}.SZ`) : s);
}

export default function Portfolio() {
  const navigate = useNavigate();
  const [codesText, setCodesText] = useState('');
  const [days, setDays] = useState(100);
  const [results, setResults] = useState<DiagnosisFull[]>([]);

  const mutation = useMutation({
    mutationFn: () => diagnosePortfolio(parseCodes(codesText), days),
    onSuccess: (data) => setResults(data.results),
  });

  const handleDiagnose = () => {
    if (!codesText.trim()) return;
    mutation.mutate();
  };

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold text-text-primary">组合体检</h1>

      <Card title="持仓输入">
        <div className="flex flex-col gap-4">
          <div>
            <label className="block text-xs text-text-muted mb-1">股票代码（每行一个，或逗号分隔）</label>
            <textarea
              value={codesText}
              onChange={(e) => setCodesText(e.target.value)}
              placeholder="600487.SH, 300750.SZ, 000001"
              rows={5}
              className="w-full rounded border border-border bg-bg-primary px-3 py-2 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent-gold font-mono"
            />
          </div>
          <div className="flex items-end gap-4">
            <div className="w-32">
              <label className="block text-xs text-text-muted mb-1">诊断天数</label>
              <select
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="w-full rounded border border-border bg-bg-primary px-2 py-1.5 text-sm text-text-primary"
              >
                {[60, 100, 150, 250].map((n) => (
                  <option key={n} value={n}>{n} 天</option>
                ))}
              </select>
            </div>
            <button
              onClick={handleDiagnose}
              disabled={mutation.isPending || !codesText.trim()}
              className="rounded-lg border border-accent-gold/40 bg-gradient-to-b from-accent-gold/30 to-accent-gold/15 px-5 py-2 text-sm font-bold tracking-wider text-accent-gold shadow-[0_0_20px_-8px_rgba(245,158,11,0.5)] transition-all hover:from-accent-gold/40 hover:to-accent-gold/25 hover:shadow-[0_0_24px_-6px_rgba(245,158,11,0.7)] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
            >
              {mutation.isPending ? '诊断中...' : '▶ 开始诊断'}
            </button>
          </div>
        </div>
      </Card>

      {mutation.isPending && (
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {mutation.isError && !mutation.isPending && (
        <Card>
          <div className="flex flex-col items-center text-center py-8">
            <div className="text-3xl mb-3 text-accent-red opacity-70">⚠</div>
            <div className="text-sm font-bold text-text-primary mb-1">诊断失败</div>
            <div className="text-xs text-text-muted mb-4 max-w-sm">
              {(mutation.error as Error)?.message || '后端服务暂时不可用，请稍后重试。'}
            </div>
            <button
              onClick={handleDiagnose}
              className="rounded-lg border border-accent-gold/40 bg-gradient-to-b from-accent-gold/30 to-accent-gold/15 px-5 py-2 text-sm font-bold tracking-wider text-accent-gold"
            >
              重试
            </button>
          </div>
        </Card>
      )}

      {results.length > 0 && !mutation.isPending && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {results.map((d) => {
            const risk = d.risk_level || 'UNKNOWN';
            const riskColor = RISK_COLORS[risk] ?? RISK_COLORS.UNKNOWN;
            const badgeVariant = RISK_BADGE[risk] ?? 'default';
            return (
              <Card key={d.ts_code}>
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="font-mono text-sm text-accent-gold">{d.ts_code}</div>
                      <div className="text-base font-bold text-text-primary">{d.name}</div>
                      <div className="text-xs text-text-muted mt-0.5">现价 ¥{formatNumber(d.price)}</div>
                    </div>
                    <Badge variant={badgeVariant}>{risk}</Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <Metric label="价格位置" value={d.price_position} />
                    <Metric label="趋势状态" value={d.trend_status} />
                    <Metric label="麒麟阶段" value={d.kirin_phase} />
                    <Metric label="卖出评分" value={`${d.sell_score} · ${d.sell_score_desc}`} />
                  </div>

                  {(d.stop_loss !== null || d.target_price !== null) && (
                    <div className="flex items-center gap-4 text-xs pt-1 border-t border-border/30">
                      {d.stop_loss !== null && (
                        <span className="text-text-secondary">止损 <span className="font-mono text-down">¥{formatNumber(d.stop_loss)}</span></span>
                      )}
                      {d.target_price !== null && (
                        <span className="text-text-secondary">目标 <span className="font-mono text-up">¥{formatNumber(d.target_price)}</span></span>
                      )}
                    </div>
                  )}

                  <div
                    className="rounded-md border px-3 py-2 text-xs leading-relaxed"
                    style={{ color: riskColor, borderColor: `${riskColor}40`, backgroundColor: `${riskColor}12` }}
                  >
                    {d.recommendation}
                  </div>

                  <div className="flex items-center gap-2 pt-1">
                    <Badge variant="success">买点 {d.buy_signals.length}</Badge>
                    <Badge variant="danger">卖点 {d.exit_signals.length}</Badge>
                    <button
                      onClick={() => navigate(`/stock/${d.ts_code}`)}
                      className="ml-auto text-xs text-accent-blue hover:underline"
                    >
                      详细分析
                    </button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-text-muted text-[10px]">{label}</div>
      <div className="text-text-secondary">{value || '--'}</div>
    </div>
  );
}
