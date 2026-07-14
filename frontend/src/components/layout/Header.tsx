import { useRef, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppStore } from '../../stores/appStore';
import { useGlobalShortcuts } from '../../lib/hooks';
import StockSearchInput from '../stock/StockSearchInput';

export default function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);
  const sidebarCollapsed = useAppStore((s) => s.sidebarCollapsed);
  const searchHistory = useAppStore((s) => s.searchHistory);
  const addSearchHistory = useAppStore((s) => s.addSearchHistory);
  const clearSearchHistory = useAppStore((s) => s.clearSearchHistory);
  const inputRef = useRef<HTMLInputElement>(null);

  const isDashboard = location.pathname === '/';

  // ⌘K / Ctrl+K 聚焦搜索框
  useGlobalShortcuts(
    useMemo(
      () => [
        {
          key: 'k',
          meta: true,
          handler: () => inputRef.current?.focus(),
        },
        {
          key: 'k',
          ctrl: true,
          handler: () => inputRef.current?.focus(),
        },
      ],
      [],
    ),
  );

  const goStock = (tsCode: string) => {
    addSearchHistory(tsCode);
    navigate(`/stock/${tsCode}`);
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-border/40 bg-bg-secondary/60 backdrop-blur-xl px-6 z-40 sticky top-0">
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? '展开侧栏' : '收起侧栏'}
          title={sidebarCollapsed ? '展开侧栏' : '收起侧栏'}
          className="text-text-muted hover:text-text-primary transition-colors px-1"
        >
          {sidebarCollapsed ? '☰' : '⟨'}
        </button>
        {/* 全局搜索框:Dashboard 页用 Hero 搜索框,这里隐藏避免重复 */}
        {!isDashboard && (
          <div className="flex items-center gap-2 relative w-80">
            <StockSearchInput
              inputRef={inputRef}
              formId="header-stock-search"
              className="flex-1"
              placeholder="输入代码或中文简称 (⌘K)"
              onNavigate={goStock}
              history={searchHistory}
              onHistoryPick={goStock}
              onClearHistory={clearSearchHistory}
            />
            <button
              type="submit"
              form="header-stock-search"
              className="rounded bg-accent-gold/20 px-3 py-1.5 text-sm text-accent-gold hover:bg-accent-gold/30 transition-colors shrink-0"
            >
              分析
            </button>
          </div>
        )}
      </div>
      <div className="text-xs text-text-muted flex items-center gap-3">
        {!isDashboard && (
          <kbd className="hidden md:inline rounded border border-border/60 bg-bg-primary px-1.5 py-0.5 text-[10px] text-text-muted font-mono">⌘K</kbd>
        )}
        <span>Z哥量化工具</span>
      </div>
    </header>
  );
}
