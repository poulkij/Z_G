// 策略列表（含选股公式 + 分类）
export interface StrategyDef {
  alias: string;
  label: string;
  category: '买点' | '形态' | '阶段' | '风控';
  formula: string;
}

export const STRATEGIES: StrategyDef[] = [
  {
    alias: 'B1',
    label: 'B1 买点',
    category: '买点',
    formula: 'b1_score ≥ 50\n  · J 值超卖区（J < 20）\n  · 缩量回调至 BBI 附近\n  · 非蜈蚣图 · 沙漏分 ≥ 50',
  },
  {
    alias: 'B2',
    label: 'B2 确认',
    category: '买点',
    formula: '最近 5 日内命中 detect_b2\n  · 涨幅 ≥ 4%\n  · 放量（量比 > 1.5）\n  · J < 55\n  · 无上影线或上影极短\n  · 非蜈蚣图 · 沙漏分 ≥ 50',
  },
  {
    alias: 'B3',
    label: 'B3 共识',
    category: '买点',
    formula: '最近 5 日内命中 detect_b3\n  · B2 后小阳线确认\n  · 分歧转一致（均线收敛后同向）\n  · 非蜈蚣图 · 沙漏分 ≥ 50',
  },
  {
    alias: '完美图形',
    label: '完美图形',
    category: '形态',
    formula: '综合评分 ≥ 65\n  · 股价在 BBI 之上\n  · 缩量整理（量比 < 0.8）\n  · 均线多头排列（MA5 > MA10 > MA20）\n  · 非蜈蚣图 · 沙漏分 ≥ 50',
  },
  {
    alias: '超级B1',
    label: '超级B1',
    category: '买点',
    formula: '最近 5 日内命中 detect_sb1\n  · 前段放量下跌\n  · 缩量企稳\n  · J 值出现负值（J < 0）\n  · 非蜈蚣图 · 沙漏分 ≥ 50',
  },
  {
    alias: '长安战法',
    label: '长安战法',
    category: '买点',
    formula: '最近 5 日内命中 detect_changan\n  · B1 买点成立\n  · 放量长阳（涨幅 > 3%，量比 > 2）\n  · 缩半量分歧转一致\n  · 非蜈蚣图 · 沙漏分 ≥ 50',
  },
  {
    alias: '建仓波',
    label: '建仓波',
    category: '阶段',
    formula: 'detect_three_waves → 建仓波\n  · confidence ≥ 0.5\n  · 三波理论第一阶段\n  · 非蜈蚣图 · 沙漏分 ≥ 50',
  },
  {
    alias: '吸筹',
    label: '吸筹',
    category: '阶段',
    formula: 'detect_kirin_stage → 吸筹\n  · confidence ≥ 0.5\n  · 麒麟会第一阶段\n  · 非蜈蚣图 · 沙漏分 ≥ 50',
  },
  {
    alias: '安全',
    label: '安全',
    category: '风控',
    formula: '三波 ≠ 冲刺波\n  · 麒麟会 ∉ {派发, 回落}\n  · 低风险综合筛选\n  · 非蜈蚣图 · 沙漏分 ≥ 50',
  },
  {
    alias: '超跌',
    label: '超跌',
    category: '形态',
    formula: 'trend_score ≤ 40\n  · RSI6 < 20 或 WR5 > 80\n  · 偏离 MA20 过远\n  · 非蜈蚣图 · 沙漏分 ≥ 50',
  },
  {
    alias: '突破',
    label: '突破',
    category: '形态',
    formula: 'volume_score ≥ 70\n  · 放量突破关键阻力位\n  · 量比 > 2\n  · 非蜈蚣图 · 沙漏分 ≥ 50',
  },
];

// 全局硬过滤说明（所有战法共用）
export const HARD_FILTER_DESC = '硬过滤：蜈蚣图排除 · 沙漏分 < 50 排除';

// 信号颜色映射
export const SIGNAL_COLORS: Record<string, string> = {
  B1: '#22c55e',
  B2: '#3b82f6',
  B3: '#a855f7',
  SB1: '#06b6d4',
  S1: '#ef4444',
  S2: '#f97316',
  S3: '#eab308',
  BUY: '#22c55e',
  SELL: '#ef4444',
  HOLD: '#f59e0b',
  WATCH: '#64748b',
};

// 风险等级颜色
export const RISK_COLORS: Record<string, string> = {
  LOW: '#22c55e',
  MEDIUM: '#f59e0b',
  HIGH: '#f97316',
  CRITICAL: '#ef4444',
  UNKNOWN: '#64748b',
};

// 导航菜单
export const NAV_ITEMS = [
  { path: '/', label: '总览', icon: '◈' },
  { path: '/screen', label: '选股', icon: '◎' },
  { path: '/watchlist', label: '自选', icon: '★' },
  { path: '/backtest', label: '回测', icon: '⟲' },
  { path: '/portfolio', label: '体检', icon: '✚' },
  { path: '/training', label: '训练', icon: '▣' },
  { path: '/trades', label: '交易', icon: '⇄' },
  { path: '/settings', label: '设置', icon: '⚙' },
] as const;
