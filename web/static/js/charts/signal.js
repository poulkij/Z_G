// 信号标注 — 在 K 线主图上标记买卖点

function addSignalsToChart(chart, klines, signals) {
    if (!signals || signals.length === 0) return;

    const dateSet = new Set(klines.map((k) => k.date));
    const buyPoints = [];
    const sellPoints = [];

    signals.forEach((sig) => {
        if (!dateSet.has(sig.trade_date)) return;
        if (sig.action === "BUY") {
            buyPoints.push({
                coord: [sig.trade_date, sig.price],
                itemStyle: { color: "#e74c3c" },
                label: { show: true, formatter: sig.strategy, color: "#e74c3c", fontSize: 9, position: "bottom" },
            });
        } else if (sig.action === "SELL") {
            sellPoints.push({
                coord: [sig.trade_date, sig.price],
                itemStyle: { color: "#00b386" },
                label: { show: true, formatter: sig.strategy, color: "#00b386", fontSize: 9, position: "top" },
            });
        }
    });

    const currentSeries = chart.getOption().series;
    if (currentSeries[0]) {
        currentSeries[0].markPoint = {
            data: [...buyPoints, ...sellPoints],
            symbol: "pin",
            symbolSize: 12,
        };
        chart.setOption({ series: currentSeries });
    }
}

function renderSignalList(containerId, signals) {
    const ul = document.getElementById(containerId);
    if (!signals || signals.length === 0) {
        ul.innerHTML = '<li style="color:var(--text-dim)">暂无信号</li>';
        return;
    }
    ul.innerHTML = signals
        .map((s) => {
            const cls = s.action === "BUY" ? "signal-buy" : s.action === "SELL" ? "signal-sell" : "";
            return `<li class="${cls}">
                <span>${s.trade_date} ${s.strategy}</span>
                <span>${s.action} ${(s.price || 0).toFixed(2)}</span>
            </li>`;
        })
        .join("");
}
