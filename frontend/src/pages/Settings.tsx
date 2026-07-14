import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api/client';
import { syncStock } from '../api/system';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ApiErrorState from '../components/ui/ApiErrorState';

export default function Settings() {
  const { data: health, isLoading: loadingHealth, isError: healthError, error: healthErr, refetch: refetchHealth } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await api.get('/system/health');
      return data;
    },
  });

  const { data: syncStatus, isLoading: loadingSync, isError: syncError, error: syncErr, refetch: refetchSync } = useQuery({
    queryKey: ['sync-status'],
    queryFn: async () => {
      const { data } = await api.get('/system/sync/status');
      return data;
    },
  });

  const queryClient = useQueryClient();
  const [syncCode, setSyncCode] = useState('');
  const [syncDays, setSyncDays] = useState(730);

  const syncMutation = useMutation({
    mutationFn: (code: string) => syncStock(code, syncDays),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-status'] });
    },
  });

  const handleSync = () => {
    if (!syncCode.trim()) return;
    let code = syncCode.trim().toUpperCase();
    if (/^\d{6}$/.test(code)) {
      code = code.startsWith('6') ? `${code}.SH` : `${code}.SZ`;
    }
    setSyncCode(code);
    syncMutation.mutate(code);
  };

  if (loadingHealth || loadingSync) {
    return <div className="flex items-center justify-center h-96"><LoadingSpinner size="lg" /></div>;
  }

  if (healthError || syncError) {
    const err = (healthErr || syncErr) as Error | null;
    return (
      <ApiErrorState
        message={err?.message || '加载系统状态失败'}
        onRetry={() => { refetchHealth(); refetchSync(); }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold text-text-primary">系统设置</h1>

      {/* System Info */}
      <Card title="系统状态">
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-text-muted">状态</span>
            <Badge variant="success">{health?.status || 'unknown'}</Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-text-muted">数据模式</span>
            <span className="text-text-primary">{health?.data_mode || '--'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-text-muted">数据库</span>
            <Badge variant={health?.db_exists ? 'success' : 'danger'}>
              {health?.db_exists ? '已连接' : '未找到'}
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-text-muted">API 版本</span>
            <span className="text-text-primary">{health?.version || '--'}</span>
          </div>
        </div>
      </Card>

      {/* Sync Status */}
      <Card title="数据同步记录">
        {!syncStatus || syncStatus.logs.length === 0 ? (
          <div className="text-center py-8 text-text-muted">暂无同步记录</div>
        ) : (
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-bg-card">
                <tr className="border-b border-border text-text-muted">
                  <th className="text-left py-1.5 px-2">类型</th>
                  <th className="text-left py-1.5 px-2">代码</th>
                  <th className="text-left py-1.5 px-2">最后日期</th>
                  <th className="text-left py-1.5 px-2">状态</th>
                  <th className="text-left py-1.5 px-2">消息</th>
                </tr>
              </thead>
              <tbody>
                {syncStatus.logs.map((log: Record<string, string>, i: number) => (
                  <tr key={i} className="border-b border-border/50">
                    <td className="py-1.5 px-2 text-text-secondary">{log.data_type}</td>
                    <td className="py-1.5 px-2 font-mono text-accent-gold">{log.ts_code || '--'}</td>
                    <td className="py-1.5 px-2 text-text-secondary">{log.last_date || '--'}</td>
                    <td className="py-1.5 px-2">
                      <Badge variant={log.status === 'success' ? 'success' : 'danger'}>
                        {log.status}
                      </Badge>
                    </td>
                    <td className="py-1.5 px-2 text-text-muted max-w-64 truncate">{log.message || '--'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card title="数据同步">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block text-xs text-text-muted mb-1">股票代码</label>
            <input
              type="text"
              value={syncCode}
              onChange={(e) => setSyncCode(e.target.value)}
              placeholder="如 600487.SH"
              className="w-full rounded border border-border bg-bg-primary px-3 py-1.5 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent-gold"
            />
          </div>
          <div className="w-32">
            <label className="block text-xs text-text-muted mb-1">同步天数</label>
            <select
              value={syncDays}
              onChange={(e) => setSyncDays(Number(e.target.value))}
              className="w-full rounded border border-border bg-bg-primary px-2 py-1.5 text-sm text-text-primary"
            >
              {[365, 730, 1000].map((n) => (
                <option key={n} value={n}>{n} 天</option>
              ))}
            </select>
          </div>
          <div className="flex items-end gap-3">
            <button
              onClick={handleSync}
              disabled={syncMutation.isPending || !syncCode.trim()}
              className="rounded-lg border border-accent-gold/40 bg-gradient-to-b from-accent-gold/30 to-accent-gold/15 px-5 py-2 text-sm font-bold tracking-wider text-accent-gold shadow-[0_0_20px_-8px_rgba(245,158,11,0.5)] transition-all hover:from-accent-gold/40 hover:to-accent-gold/25 hover:shadow-[0_0_24px_-6px_rgba(245,158,11,0.7)] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
            >
              {syncMutation.isPending ? '同步中...' : '▶ 开始同步'}
            </button>
          </div>
        </div>

        {syncMutation.isPending && (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="md" />
          </div>
        )}

        {syncMutation.isSuccess && !syncMutation.isPending && (
          <div className="mt-3 rounded border border-border/50 bg-bg-primary p-3 text-sm text-up">
            ✓ 同步成功：{syncCode}（{syncDays} 天）已完成
          </div>
        )}

        {syncMutation.isError && !syncMutation.isPending && (
          <div className="mt-3 rounded border border-border/50 bg-bg-primary p-3 text-sm text-down">
            ✗ 同步失败：{(syncMutation.error as Error)?.message || '未知错误'}
          </div>
        )}
      </Card>
    </div>
  );
}
