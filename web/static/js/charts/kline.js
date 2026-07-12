// K线主图组件 — ECharts candlestick + 均线 + 信号标注

function createKlineChart(containerId) {
    const chart = echarts.init(document.getElementById(containerId));

    const option = {
        backgroundColor: "transparent",
        animation: false,
        grid: { left: "5%", right: "3%", top: "5%", bottom: "10%" },
        xAxis: {
            type: "category",
            data: [],
            axisLine: { lineStyle: { color: "#2a2a4a" } },
            axisLabel: { color: "#888", fontSize: 10 },
        },
        yAxis: {
            type: "value",
            scale: true,
            axisLine: { lineStyle: { color: "#2a2a4a" } },
            axisLabel: { color: "#888", fontSize: 10 },
            splitLine: { lineStyle: { color: "#1a1a2e" } },
        },
        dataZoom: [
            { type: "inside", start: 60, end: 100 },
            { type: "slider", start: 60, end: 100, height: 20, bottom: 0 },
        ],
        tooltip: {
            trigger: "axis",
            axisPointer: { type: "cross" },
            backgroundColor: "#1a1a2e",
            borderColor: "#2a2a4a",
            textStyle: { color: "#e0e0e0" },
        },
        legend: {
            data: ["K线", "MA5", "MA10", "MA20", "MA60"],
            textStyle: { color: "#888" },
            top: 0,
        },
        series: [
            {
                name: "K线",
                type: "candlestick",
                data: [],
                itemStyle: {
                    color: "#e74c3c",
                    color0: "#00b386",
                    borderColor: "#e74c3c",
                    borderColor0: "#00b386",
                },
            },
            { name: "MA5", type: "line", data: [], smooth: true, lineStyle: { width: 1 }, symbol: "none" },
            { name: "MA10", type: "line", data: [], smooth: true, lineStyle: { width: 1 }, symbol: "none" },
            { name: "MA20", type: "line", data: [], smooth: true, lineStyle: { width: 1 }, symbol: "none" },
            { name: "MA60", type: "line", data: [], smooth: true, lineStyle: { width: 1 }, symbol: "none" },
        ],
    };

    chart.setOption(option);
    window.addEventListener("resize", () => chart.resize());
    return chart;
}

function updateKlineChart(chart, klines, indicators) {
    if (!klines || klines.length === 0) return;

    const dates = klines.map((k) => k.date);
    const ohlc = klines.map((k) => [k.open, k.close, k.low, k.high]);

    const closes = klines.map((k) => k.close);
    const ma = (n) => {
        const result = [];
        for (let i = 0; i < closes.length; i++) {
            if (i < n - 1) { result.push(null); continue; }
            let sum = 0;
            for (let j = i - n + 1; j <= i; j++) sum += closes[j];
            result.push(parseFloat((sum / n).toFixed(2)));
        }
        return result;
    };

    chart.setOption({
        xAxis: { data: dates },
        series: [
            { name: "K线", data: ohlc },
            { name: "MA5", data: ma(5) },
            { name: "MA10", data: ma(10) },
            { name: "MA20", data: ma(20) },
            { name: "MA60", data: ma(60) },
        ],
    });
}
