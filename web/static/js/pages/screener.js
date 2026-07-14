// 选股筛选页交互

let _searchTimer = null;

async function runScreener() {
    const strategy = document.getElementById("strategy-select").value;
    const maxStocks = parseInt(document.getElementById("max-stocks").value) || 500;
    const dateStr = document.getElementById("screen-date").value;
    const container = document.getElementById("screener-results");
    container.innerHTML = '<p style="color:var(--text-dim)">筛选中...（全市场扫描，约 30 秒~3 分钟）</p>';

    try {
        let data;
        if (dateStr) {
            // 有日期 → 历史选股
            const yyyymmdd = dateStr.replace(/-/g, "");
            data = await API.historicalScreener({
                date: yyyymmdd,
                strategies: [strategy],
                min_score: 0,
                days: 150,
                limit: 100,
            });
        } else {
            // 无日期 → 最新选股
            data = await API.screener(strategy, maxStocks);
        }

        if (data.results.length === 0) {
            container.innerHTML = '<p style="color:var(--text-dim)">无符合条件的股票（换策略或多扫几只试试）</p>';
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

// ===== 股票搜索 =====

function searchStock() {
    const q = document.getElementById("stock-search-input").value.trim();
    if (!q) return;
    doSearch(q);
}

// 输入实时搜索（防抖 300ms）
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("stock-search-input");
    if (input) {
        input.addEventListener("input", () => {
            clearTimeout(_searchTimer);
            const q = input.value.trim();
            if (q.length < 1) {
                document.getElementById("search-dropdown").style.display = "none";
                return;
            }
            // 6 位纯数字代码：立即触发（唯一匹配会自动跳转）
            const delay = /^\d{6}$/.test(q) ? 0 : 300;
            _searchTimer = setTimeout(() => doSearch(q), delay);
        });
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                searchStock();
            }
        });
        // 失焦时延迟隐藏下拉（让点击事件先触发）
        document.addEventListener("click", (e) => {
            if (!e.target.closest(".stock-search")) {
                document.getElementById("search-dropdown").style.display = "none";
            }
        });
    }
});

async function doSearch(q) {
    const dropdown = document.getElementById("search-dropdown");
    try {
        const data = await API.searchStocks(q, 20);
        if (data.results.length === 0) {
            dropdown.innerHTML = '<div class="search-item" style="color:var(--text-dim)">无匹配股票</div>';
            dropdown.style.display = "block";
            return;
        }
        // 6 位纯数字代码且唯一匹配 → 直接跳转，不显示下拉
        if (/^\d{6}$/.test(q) && data.results.length === 1) {
            goToStock(data.results[0].ts_code);
            return;
        }
        dropdown.innerHTML = data.results.map((s) =>
            `<div class="search-item" onclick="goToStock('${s.ts_code}')">
                <span style="color:var(--accent)">${s.ts_code}</span>
                <span>${s.name}</span>
                <span style="color:var(--text-dim);font-size:0.8rem;margin-left:0.5rem">${s.industry}</span>
            </div>`
        ).join("");
        dropdown.style.display = "block";
    } catch (e) {
        dropdown.innerHTML = `<div class="search-item" style="color:var(--red)">搜索失败: ${e.message}</div>`;
        dropdown.style.display = "block";
    }
}

function goToStock(tsCode) {
    document.getElementById("search-dropdown").style.display = "none";
    location.href = `/stock/${tsCode}`;
}
