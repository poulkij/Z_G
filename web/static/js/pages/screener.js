// 选股筛选页交互

async function runScreener() {
    const strategy = document.getElementById("strategy-select").value;
    const maxStocks = parseInt(document.getElementById("max-stocks").value) || 500;
    const container = document.getElementById("screener-results");
    container.innerHTML = '<p style="color:var(--text-dim)">筛选中...</p>';

    try {
        const data = await API.screener(strategy, maxStocks);
        if (data.results.length === 0) {
            container.innerHTML = '<p style="color:var(--text-dim)">无符合条件的股票</p>';
            return;
        }

        let html = `<p style="margin-bottom:0.5rem">共 ${data.total} 只符合条件</p>`;
        html += '<table class="data-table"><thead><tr><th>代码</th><th>名称</th><th>综合评分</th><th>B1</th><th>趋势</th><th>量价</th><th>风险</th><th>评级</th><th>理由</th></tr></thead><tbody>';
        data.results.forEach((s) => {
            const scoreColor = s.score >= 80 ? "var(--red)" : s.score >= 65 ? "var(--accent)" : s.score >= 50 ? "var(--text)" : "var(--text-dim)";
            html += `<tr style="cursor:pointer" onclick="location.href='/stock/${s.ts_code}'">
                <td>${s.ts_code}</td>
                <td>${s.name}</td>
                <td style="color:${scoreColor};font-weight:bold">${s.score.toFixed(1)}</td>
                <td>${s.b1_score.toFixed(0)}</td>
                <td>${s.trend_score.toFixed(0)}</td>
                <td>${s.volume_score.toFixed(0)}</td>
                <td>${s.risk_score.toFixed(0)}</td>
                <td style="font-size:0.8rem">${s.rating}</td>
                <td style="font-size:0.8rem;color:var(--text-dim)">${(s.reasons || []).join("; ")}</td>
            </tr>`;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<p style="color:var(--red)">筛选失败: ${e.message}</p>`;
    }
}
