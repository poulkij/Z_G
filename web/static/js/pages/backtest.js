// 回测页交互

async function runBacktest() {
    const tsCode = document.getElementById("bt-ts-code").value.trim();
    const days = parseInt(document.getElementById("bt-days").value) || 240;
    const stopLoss = parseFloat(document.getElementById("bt-stop-loss").value) || 0.07;
    const takeProfit = parseFloat(document.getElementById("bt-take-profit").value) || 0.15;
    const container = document.getElementById("backtest-result");
    document.getElementById("tune-result").innerHTML = "";
    container.innerHTML = '<p style="color:var(--text-dim)">回测中...</p>';

    try {
        const data = await API.backtest({
            ts_code: tsCode, days, stop_loss_pct: stopLoss, take_profit_pct: takeProfit,
        });

        const winRateColor = data.win_rate >= 0.5 ? "var(--red)" : data.win_rate >= 0.3 ? "var(--accent)" : "var(--text-dim)";
        let html = '<div style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:1.5rem">';
        html += `<h3 style="color:var(--accent);margin-bottom:0.75rem">${data.ts_code} 回测结果</h3>`;
        html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:1rem;margin-bottom:1rem">';
        html += `<div><div style="color:var(--text-dim);font-size:0.8rem">总交易次数</div><div style="font-size:1.5rem">${data.total_trades}</div></div>`;
        html += `<div><div style="color:var(--text-dim);font-size:0.8rem">盈利次数</div><div style="font-size:1.5rem;color:var(--red)">${data.win_trades}</div></div>`;
        html += `<div><div style="color:var(--text-dim);font-size:0.8rem">亏损次数</div><div style="font-size:1.5rem;color:var(--green)">${data.loss_trades}</div></div>`;
        html += `<div><div style="color:var(--text-dim);font-size:0.8rem">胜率</div><div style="font-size:1.5rem;color:${winRateColor}">${(data.win_rate * 100).toFixed(1)}%</div></div>`;
        html += `<div><div style="color:var(--text-dim);font-size:0.8rem">盈亏比</div><div style="font-size:1.5rem">${data.profit_factor.toFixed(2)}</div></div>`;
        html += `<div><div style="color:var(--text-dim);font-size:0.8rem">最大回撤</div><div style="font-size:1.5rem;color:var(--green)">${(data.max_drawdown * 100).toFixed(1)}%</div></div>`;
        html += `<div><div style="color:var(--text-dim);font-size:0.8rem">总收益率</div><div style="font-size:1.5rem;color:${data.total_return >= 0 ? "var(--red)" : "var(--green)"}">${(data.total_return * 100).toFixed(2)}%</div></div>`;
        html += '</div>';

        if (data.trades.length > 0) {
            html += '<table class="data-table"><thead><tr><th>买入日期</th><th>买入价</th><th>卖出日期</th><th>卖出价</th><th>收益%</th><th>持仓天</th><th>退出原因</th></tr></thead><tbody>';
            data.trades.forEach((t) => {
                const pnlColor = t.pnl_pct >= 0 ? "var(--red)" : "var(--green)";
                html += `<tr>
                    <td>${t.entry_date}</td><td>${t.entry_price.toFixed(2)}</td>
                    <td>${t.exit_date || "-"}</td><td>${t.exit_price ? t.exit_price.toFixed(2) : "-"}</td>
                    <td style="color:${pnlColor}">${(t.pnl_pct * 100).toFixed(2)}%</td>
                    <td>${t.hold_days}</td><td style="font-size:0.8rem">${t.exit_reason}</td>
                </tr>`;
            });
            html += '</tbody></table>';
        }
        html += '</div>';
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<p style="color:var(--red)">回测失败: ${e.message}</p>`;
    }
}

async function runTune() {
    const tsCode = document.getElementById("bt-ts-code").value.trim();
    const days = parseInt(document.getElementById("bt-days").value) || 240;
    const container = document.getElementById("tune-result");
    document.getElementById("backtest-result").innerHTML = "";
    container.innerHTML = '<p style="color:var(--text-dim)">参数调优中...</p>';

    const paramGrid = {
        stop_loss_pct: [0.03, 0.05, 0.07, 0.10, 0.15],
        take_profit_pct: [0.08, 0.10, 0.15, 0.20, 0.30],
    };

    try {
        const data = await API.tuneBacktest({
            ts_code: tsCode, param_grid: paramGrid, days, score_metric: "win_rate",
        });

        let html = '<div style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:1.5rem">';
        html += `<h3 style="color:var(--accent);margin-bottom:0.75rem">参数调优结果</h3>`;
        html += `<p style="margin-bottom:0.5rem">最优参数: 止损=${data.best_params.stop_loss_pct}, 止盈=${data.best_params.take_profit_pct}, 胜率=${(data.best_score * 100).toFixed(1)}%</p>`;
        html += '<table class="data-table"><thead><tr><th>止损</th><th>止盈</th><th>胜率</th><th>总收益</th><th>最大回撤</th><th>交易数</th></tr></thead><tbody>';
        data.all_results.forEach((r) => {
            html += `<tr>
                <td>${r.params.stop_loss_pct}</td>
                <td>${r.params.take_profit_pct}</td>
                <td style="color:${r.score >= 0.5 ? "var(--red)" : "var(--text-dim)"}">${(r.score * 100).toFixed(1)}%</td>
                <td>${(r.total_return * 100).toFixed(2)}%</td>
                <td>${(r.max_drawdown * 100).toFixed(1)}%</td>
                <td>${r.total_trades}</td>
            </tr>`;
        });
        html += '</tbody></table></div>';
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<p style="color:var(--red)">调优失败: ${e.message}</p>`;
    }
}
