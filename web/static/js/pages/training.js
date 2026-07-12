// 选股训练页交互 — 前端管理交易状态，localStorage 持久化

let trainPositions = JSON.parse(localStorage.getItem("trainPositions") || "[]");

function savePositions() {
    localStorage.setItem("trainPositions", JSON.stringify(trainPositions));
}

async function trainingScreen() {
    const date = document.getElementById("train-date").value.replace(/-/g, "");
    const select = document.getElementById("train-strategies");
    const strategies = Array.from(select.selectedOptions).map((o) => o.value);
    const minScore = parseFloat(document.getElementById("train-min-score").value) || 0;
    const container = document.getElementById("train-screen-result");
    container.innerHTML = '<p style="color:var(--text-dim)">筛选中...</p>';

    try {
        const data = await API.trainingScreen({
            date, strategies, min_score: minScore, days: 120,
        });

        if (data.results.length === 0) {
            container.innerHTML = '<div style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:1.5rem"><p style="color:var(--text-dim)">当日无符合条件的股票（扫描 ' + data.total_scanned + ' 只）</p></div>';
            return;
        }

        let html = '<div style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:1.5rem">';
        html += `<p style="margin-bottom:0.5rem">Step 2: 筛选结果（${data.results.length} 只符合，扫描 ${data.total_scanned}）</p>`;
        html += '<table class="data-table"><thead><tr><th>代码</th><th>名称</th><th>评分</th><th>评级</th><th>买入价</th><th>数量</th><th>操作</th></tr></thead><tbody>';
        data.results.forEach((s) => {
            html += `<tr>
                <td>${s.ts_code}</td>
                <td>${s.name}</td>
                <td style="color:var(--accent);font-weight:bold">${s.score.toFixed(1)}</td>
                <td style="font-size:0.8rem">${s.rating}</td>
                <td><input type="number" id="buy-price-${s.ts_code}" value="0" step="0.01" style="width:80px;background:var(--bg);border:1px solid var(--border);color:var(--text);padding:2px 4px;border-radius:2px"></td>
                <td><input type="number" id="buy-qty-${s.ts_code}" value="100" step="100" style="width:80px;background:var(--bg);border:1px solid var(--border);color:var(--text);padding:2px 4px;border-radius:2px"></td>
                <td><button class="btn" style="padding:2px 8px;font-size:0.8rem" onclick="buyStock('${s.ts_code}','${s.name}')">买入</button></td>
            </tr>`;
        });
        html += '</tbody></table></div>';
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<p style="color:var(--red)">筛选失败: ${e.message}</p>`;
    }
}

function buyStock(tsCode, name) {
    const price = parseFloat(document.getElementById(`buy-price-${tsCode}`).value) || 0;
    const qty = parseInt(document.getElementById(`buy-qty-${tsCode}`).value) || 0;
    if (price <= 0 || qty <= 0) {
        alert("请输入有效的买入价和数量");
        return;
    }

    trainPositions.push({
        ts_code: tsCode, name, entry_date: document.getElementById("train-date").value.replace(/-/g, ""),
        entry_price: price, quantity: qty,
    });
    savePositions();
    renderPositions();
}

function sellPosition(index) {
    const settleDate = document.getElementById("settle-date").value || document.getElementById("train-date").value;
    const sellPrice = parseFloat(prompt("输入卖出价:", trainPositions[index].entry_price)) || 0;
    if (sellPrice <= 0) return;

    const pos = trainPositions[index];
    pos.exit_date = settleDate.replace(/-/g, "");
    pos.exit_price = sellPrice;
    pos.pnl = (sellPrice - pos.entry_price) * pos.quantity;
    pos.pnl_pct = (sellPrice - pos.entry_price) / pos.entry_price;
    pos.settled = true;
    savePositions();
    renderPositions();
}

function removePosition(index) {
    trainPositions.splice(index, 1);
    savePositions();
    renderPositions();
}

function renderPositions() {
    const container = document.getElementById("train-positions");
    const body = document.getElementById("position-body");

    if (trainPositions.length === 0) {
        container.style.display = "none";
        return;
    }
    container.style.display = "block";

    body.innerHTML = trainPositions.map((p, i) => {
        const status = p.settled ? `<span style="color:${p.pnl >= 0 ? "var(--red)" : "var(--green)"}">${p.pnl >= 0 ? "+" : ""}${p.pnl.toFixed(2)} (${(p.pnl_pct * 100).toFixed(2)}%)</span>` : "持有中";
        const actions = p.settled
            ? `<button class="btn" style="padding:2px 8px;font-size:0.8rem;background:var(--border)" onclick="removePosition(${i})">删除</button>`
            : `<button class="btn" style="padding:2px 8px;font-size:0.8rem" onclick="sellPosition(${i})">卖出</button>
               <button class="btn" style="padding:2px 8px;font-size:0.8rem;background:var(--border)" onclick="removePosition(${i})">删除</button>`;
        return `<tr>
            <td>${p.ts_code}</td><td>${p.name}</td>
            <td>${p.entry_price.toFixed(2)}</td><td>${p.quantity}</td>
            <td>${status}</td><td>${actions}</td>
        </tr>`;
    }).join("");
}

function settleUp() {
    const container = document.getElementById("settle-result");
    const settled = trainPositions.filter((p) => p.settled);

    if (settled.length === 0) {
        container.innerHTML = '<p style="color:var(--text-dim)">无已结算的交易</p>';
        return;
    }

    const wins = settled.filter((p) => p.pnl > 0);
    const losses = settled.filter((p) => p.pnl < 0);
    const winRate = wins.length / settled.length;
    const avgPnl = settled.reduce((s, p) => s + p.pnl_pct, 0) / settled.length;
    const totalPnl = settled.reduce((s, p) => s + p.pnl, 0);

    // 计算最大回撤
    let peak = 0, cum = 0, maxDD = 0;
    settled.forEach((p) => { cum += p.pnl_pct; peak = Math.max(peak, cum); maxDD = Math.max(maxDD, peak - cum); });

    let html = '<div style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:1.5rem">';
    html += '<h3 style="color:var(--accent);margin-bottom:0.75rem">结算统计</h3>';
    html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:1rem;margin-bottom:1rem">';
    html += `<div><div style="color:var(--text-dim);font-size:0.8rem">总交易数</div><div style="font-size:1.5rem">${settled.length}</div></div>`;
    html += `<div><div style="color:var(--text-dim);font-size:0.8rem">盈利数</div><div style="font-size:1.5rem;color:var(--red)">${wins.length}</div></div>`;
    html += `<div><div style="color:var(--text-dim);font-size:0.8rem">亏损数</div><div style="font-size:1.5rem;color:var(--green)">${losses.length}</div></div>`;
    html += `<div><div style="color:var(--text-dim);font-size:0.8rem">胜率</div><div style="font-size:1.5rem;color:${winRate >= 0.5 ? "var(--red)" : "var(--text-dim)"}">${(winRate * 100).toFixed(1)}%</div></div>`;
    html += `<div><div style="color:var(--text-dim);font-size:0.8rem">平均收益</div><div style="font-size:1.5rem;color:${avgPnl >= 0 ? "var(--red)" : "var(--green)"}">${(avgPnl * 100).toFixed(2)}%</div></div>`;
    html += `<div><div style="color:var(--text-dim);font-size:0.8rem">最大回撤</div><div style="font-size:1.5rem;color:var(--green)">${(maxDD * 100).toFixed(1)}%</div></div>`;
    html += `<div><div style="color:var(--text-dim);font-size:0.8rem">总盈亏</div><div style="font-size:1.5rem;color:${totalPnl >= 0 ? "var(--red)" : "var(--green)"}">${totalPnl >= 0 ? "+" : ""}${totalPnl.toFixed(2)}</div></div>`;
    html += '</div>';

    // 交易明细
    html += '<table class="data-table"><thead><tr><th>代码</th><th>名称</th><th>买入价</th><th>卖出价</th><th>数量</th><th>盈亏</th><th>收益%</th></tr></thead><tbody>';
    settled.forEach((p) => {
        html += `<tr>
            <td>${p.ts_code}</td><td>${p.name}</td>
            <td>${p.entry_price.toFixed(2)}</td><td>${p.exit_price.toFixed(2)}</td>
            <td>${p.quantity}</td>
            <td style="color:${p.pnl >= 0 ? "var(--red)" : "var(--green)"}">${p.pnl >= 0 ? "+" : ""}${p.pnl.toFixed(2)}</td>
            <td style="color:${p.pnl_pct >= 0 ? "var(--red)" : "var(--green)"}">${(p.pnl_pct * 100).toFixed(2)}%</td>
        </tr>`;
    });
    html += '</tbody></table></div>';

    // 收益曲线
    html += '<div id="equity-chart" style="height:300px;margin-top:1rem"></div>';
    container.innerHTML = html;

    // 绘制收益曲线
    let cumPnl = 0;
    const equityData = settled.map((p, i) => {
        cumPnl += p.pnl;
        return [i + 1, +cumPnl.toFixed(2)];
    });
    const chart = echarts.init(document.getElementById("equity-chart"));
    chart.setOption({
        backgroundColor: "transparent",
        title: { text: "收益曲线", textStyle: { color: "#888", fontSize: 14 } },
        grid: { left: "5%", right: "5%", bottom: "10%" },
        xAxis: { type: "category", data: equityData.map((d) => d[0]), axisLine: { lineStyle: { color: "#2a2a4a" } }, axisLabel: { color: "#888" } },
        yAxis: { type: "value", axisLine: { lineStyle: { color: "#2a2a4a" } }, axisLabel: { color: "#888" }, splitLine: { lineStyle: { color: "#1a1a2e" } } },
        series: [{
            type: "line", data: equityData.map((d) => d[1]), smooth: true,
            areaStyle: { color: "rgba(233,69,96,0.2)" },
            lineStyle: { color: "#e94560", width: 2 },
            symbol: "circle", symbolSize: 6,
        }],
        tooltip: { trigger: "axis", backgroundColor: "#1a1a2e", borderColor: "#2a2a4a", textStyle: { color: "#e0e0e0" } },
    });
    window.addEventListener("resize", () => chart.resize());
}

function clearTraining() {
    trainPositions = [];
    savePositions();
    renderPositions();
    document.getElementById("train-screen-result").innerHTML = "";
    document.getElementById("settle-result").innerHTML = "";
}

document.addEventListener("DOMContentLoaded", () => {
    const today = new Date();
    const todayStr = today.toISOString().split("T")[0];
    if (!document.getElementById("settle-date").value) {
        document.getElementById("settle-date").value = todayStr;
    }
    renderPositions();
});
