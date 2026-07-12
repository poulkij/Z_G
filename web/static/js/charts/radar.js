// 评分雷达图

function createRadarChart(containerId) {
    const chart = echarts.init(document.getElementById(containerId));

    chart.setOption({
        backgroundColor: "transparent",
        radar: {
            indicator: [
                { name: "综合", max: 100 },
                { name: "B1", max: 100 },
                { name: "趋势", max: 100 },
                { name: "量价", max: 100 },
                { name: "风险", max: 100 },
            ],
            axisName: { color: "#888", fontSize: 11 },
            splitLine: { lineStyle: { color: "#2a2a4a" } },
            splitArea: { areaStyle: { color: ["#1a1a2e", "#0f0f1e"] } },
            axisLine: { lineStyle: { color: "#2a2a4a" } },
        },
        series: [{
            type: "radar",
            data: [{
                value: [0, 0, 0, 0, 0],
                areaStyle: { color: "rgba(233,69,96,0.3)" },
                lineStyle: { color: "#e94560", width: 2 },
            }],
        }],
    });

    window.addEventListener("resize", () => chart.resize());
    return chart;
}

function updateRadarChart(chart, score) {
    if (!score) return;
    chart.setOption({
        series: [{
            data: [{
                value: [score.score, score.b1_score, score.trend_score, score.volume_score, score.risk_score],
                name: score.name || score.ts_code,
            }],
        }],
    });
}
