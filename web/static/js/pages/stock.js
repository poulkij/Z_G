// 个股看板交互逻辑

let mainChart = null;
let subCharts = [];
let radarChart = null;

async function loadStock(tsCode) {
    if (!tsCode) return;

    history.pushState({}, "", `/stock/${tsCode}`);
    document.getElementById("stock-code").textContent = tsCode;

    const data = await API.getStockAnalysis(tsCode, 120);

    document.getElementById("stock-name").textContent = data.name || "";

    if (!mainChart) mainChart = createKlineChart("main-chart");
    updateKlineChart(mainChart, data.klines, data.indicators);

    addSignalsToChart(mainChart, data.klines, data.signals);
    renderSignalList("signal-list", data.signals);

    subCharts = renderSubWindows("sub-windows");
    updateSubCharts(subCharts, data.klines, data.indicators);

    if (!radarChart) radarChart = createRadarChart("radar-chart");
    updateRadarChart(radarChart, data.score);
}

document.addEventListener("DOMContentLoaded", () => {
    const tsCode = document.getElementById("stock-code").textContent;
    loadStock(tsCode);
});

document.getElementById("code-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        loadStock(e.target.value);
    }
});
