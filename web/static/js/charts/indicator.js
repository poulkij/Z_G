// 通达信式自定义副图 — 支持多窗口、指标切换、配置存 localStorage

const SUB_INDICATORS = {
    MACD: { name: "MACD", params: { fast: 12, slow: 26, signal: 9 } },
    KDJ: { name: "KDJ", params: { n: 9, m1: 3, m2: 3 } },
    RSI: { name: "RSI", params: { n: 6 } },
    WR: { name: "WR", params: { n: 14 } },
    VOLUME: { name: "VOL", params: {} },
    BOLL: { name: "BOLL", params: { n: 20, k: 2 } },
    OBV: { name: "OBV", params: {} },
};

function getDefaultSubConfig() {
    return {
        windows: [
            { indicator: "VOLUME", params: {} },
            { indicator: "MACD", params: {} },
        ],
    };
}

function loadSubConfig() {
    try {
        const saved = localStorage.getItem("subChartConfig");
        return saved ? JSON.parse(saved) : getDefaultSubConfig();
    } catch {
        return getDefaultSubConfig();
    }
}

function saveSubConfig(config) {
    localStorage.setItem("subChartConfig", JSON.stringify(config));
}

function createSubWindowContainer(parentId, index, indicatorName) {
    const parent = document.getElementById(parentId);
    const div = document.createElement("div");
    div.className = "chart-sub";
    div.id = `sub-chart-${index}`;

    const toolbar = document.createElement("div");
    toolbar.className = "sub-toolbar";

    const select = document.createElement("select");
    for (const key of Object.keys(SUB_INDICATORS)) {
        const opt = document.createElement("option");
        opt.value = key;
        opt.textContent = key;
        if (key === indicatorName) opt.selected = true;
        select.appendChild(opt);
    }
    select.addEventListener("change", (e) => {
        const config = loadSubConfig();
        config.windows[index].indicator = e.target.value;
        config.windows[index].params = SUB_INDICATORS[e.target.value].params;
        saveSubConfig(config);
        renderSubWindows(parentId);
    });
    toolbar.appendChild(select);

    const closeBtn = document.createElement("button");
    closeBtn.textContent = "\u00d7";
    closeBtn.title = "删除副图";
    closeBtn.addEventListener("click", () => {
        const config = loadSubConfig();
        if (config.windows.length > 1) {
            config.windows.splice(index, 1);
            saveSubConfig(config);
            renderSubWindows(parentId);
        }
    });
    toolbar.appendChild(closeBtn);

    div.appendChild(toolbar);
    parent.appendChild(div);
    return div;
}

function createAddSubButton(parentId) {
    const parent = document.getElementById(parentId);
    const btn = document.createElement("button");
    btn.textContent = "+ 添加副图";
    btn.style.cssText = "background:var(--card-bg);border:1px solid var(--border);color:var(--text-dim);padding:4px 12px;border-radius:4px;cursor:pointer;margin-top:4px;";
    btn.addEventListener("click", () => {
        const config = loadSubConfig();
        if (config.windows.length < 3) {
            config.windows.push({ indicator: "RSI", params: SUB_INDICATORS.RSI.params });
            saveSubConfig(config);
            renderSubWindows(parentId);
        }
    });
    parent.appendChild(btn);
}

function renderSubWindows(parentId) {
    const parent = document.getElementById(parentId);
    parent.innerHTML = "";
    const config = loadSubConfig();

    const charts = [];
    config.windows.forEach((win, i) => {
        const container = createSubWindowContainer(parentId, i, win.indicator);
        const chart = echarts.init(container);
        charts.push({ chart, indicator: win.indicator });
    });

    createAddSubButton(parentId);

    window.addEventListener("resize", () => charts.forEach((c) => c.chart.resize()));
    return charts;
}

function calcIndicator(indicator, klines, indicatorsSnapshot) {
    if (!klines || klines.length === 0) return { dates: [], series: [] };

    const closes = klines.map((k) => k.close);
    const vols = klines.map((k) => k.volume);
    const highs = klines.map((k) => k.high);
    const lows = klines.map((k) => k.low);
    const dates = klines.map((k) => k.date);

    if (indicator === "VOLUME") {
        return {
            dates,
            series: [{
                name: "成交量",
                type: "bar",
                data: vols.map((v, i) => ({
                    value: v,
                    itemStyle: { color: klines[i].close >= klines[i].open ? "#e74c3c" : "#00b386" },
                })),
            }],
        };
    }

    if (indicator === "MACD") {
        const ema = (n) => {
            const result = [];
            let prev = closes[0];
            for (let i = 0; i < closes.length; i++) {
                prev = (closes[i] * 2 + prev * (n - 1)) / (n + 1);
                result.push(prev);
            }
            return result;
        };
        const ema12 = ema(12);
        const ema26 = ema(26);
        const dif = ema12.map((v, i) => v - ema26[i]);
        let deaPrev = dif[0];
        const dea = dif.map((v) => { deaPrev = (deaPrev * 8 + v * 2) / 10; return deaPrev; });
        const macd = dif.map((v, i) => 2 * (v - dea[i]));
        return {
            dates,
            series: [
                { name: "DIF", type: "line", data: dif.map((v) => +v.toFixed(4)), symbol: "none", lineStyle: { width: 1 } },
                { name: "DEA", type: "line", data: dea.map((v) => +v.toFixed(4)), symbol: "none", lineStyle: { width: 1 } },
                {
                    name: "MACD",
                    type: "bar",
                    data: macd.map((v) => ({
                        value: +v.toFixed(4),
                        itemStyle: { color: v >= 0 ? "#e74c3c" : "#00b386" },
                    })),
                },
            ],
        };
    }

    if (indicator === "KDJ") {
        let k = 50, d = 50;
        const kArr = [], dArr = [], jArr = [];
        for (let i = 0; i < closes.length; i++) {
            const start = Math.max(0, i - 8);
            const hh = Math.max(...highs.slice(start, i + 1));
            const ll = Math.min(...lows.slice(start, i + 1));
            const rsv = hh === ll ? 0 : (closes[i] - ll) / (hh - ll) * 100;
            k = (2 / 3) * k + (1 / 3) * rsv;
            d = (2 / 3) * d + (1 / 3) * k;
            kArr.push(+k.toFixed(2));
            dArr.push(+d.toFixed(2));
            jArr.push(+(3 * k - 2 * d).toFixed(2));
        }
        return {
            dates,
            series: [
                { name: "K", type: "line", data: kArr, symbol: "none", lineStyle: { width: 1 } },
                { name: "D", type: "line", data: dArr, symbol: "none", lineStyle: { width: 1 } },
                { name: "J", type: "line", data: jArr, symbol: "none", lineStyle: { width: 1, color: "#e94560" } },
            ],
        };
    }

    if (indicator === "RSI") {
        const rsi = [];
        for (let i = 0; i < closes.length; i++) {
            if (i < 6) { rsi.push(50); continue; }
            let gain = 0, loss = 0;
            for (let j = i - 5; j <= i; j++) {
                const diff = closes[j] - closes[j - 1];
                if (diff > 0) gain += diff;
                else loss -= diff;
            }
            rsi.push(loss === 0 ? 100 : 100 - 100 / (1 + gain / loss));
        }
        return {
            dates,
            series: [{ name: "RSI6", type: "line", data: rsi.map((v) => +v.toFixed(2)), symbol: "none", lineStyle: { width: 1 } }],
        };
    }

    if (indicator === "WR") {
        const wr = [];
        for (let i = 0; i < closes.length; i++) {
            if (i < 13) { wr.push(-50); continue; }
            const hh = Math.max(...highs.slice(i - 13, i + 1));
            const ll = Math.min(...lows.slice(i - 13, i + 1));
            wr.push(hh === ll ? -50 : (hh - closes[i]) / (hh - ll) * -100);
        }
        return {
            dates,
            series: [{ name: "WR", type: "line", data: wr.map((v) => +v.toFixed(2)), symbol: "none", lineStyle: { width: 1 } }],
        };
    }

    if (indicator === "BOLL") {
        const ma20 = [], upper = [], lower = [];
        for (let i = 0; i < closes.length; i++) {
            if (i < 19) { ma20.push(null); upper.push(null); lower.push(null); continue; }
            const slice = closes.slice(i - 19, i + 1);
            const avg = slice.reduce((a, b) => a + b, 0) / 20;
            const std = Math.sqrt(slice.reduce((s, v) => s + (v - avg) ** 2, 0) / 20);
            ma20.push(+avg.toFixed(2));
            upper.push(+(avg + 2 * std).toFixed(2));
            lower.push(+(avg - 2 * std).toFixed(2));
        }
        return {
            dates,
            series: [
                { name: "上轨", type: "line", data: upper, symbol: "none", lineStyle: { width: 1 } },
                { name: "中轨", type: "line", data: ma20, symbol: "none", lineStyle: { width: 1 } },
                { name: "下轨", type: "line", data: lower, symbol: "none", lineStyle: { width: 1 } },
            ],
        };
    }

    if (indicator === "OBV") {
        const obv = [0];
        for (let i = 1; i < closes.length; i++) {
            const prev = obv[i - 1];
            if (closes[i] > closes[i - 1]) obv.push(prev + vols[i]);
            else if (closes[i] < closes[i - 1]) obv.push(prev - vols[i]);
            else obv.push(prev);
        }
        return {
            dates,
            series: [{ name: "OBV", type: "line", data: obv, symbol: "none", lineStyle: { width: 1 } }],
        };
    }

    return { dates, series: [] };
}

function updateSubCharts(subCharts, klines, indicators) {
    subCharts.forEach(({ chart, indicator }) => {
        const data = calcIndicator(indicator, klines, indicators);
        chart.setOption({
            backgroundColor: "transparent",
            animation: false,
            grid: { left: "5%", right: "3%", top: "10%", bottom: "15%" },
            xAxis: {
                type: "category",
                data: data.dates || [],
                axisLine: { lineStyle: { color: "#2a2a4a" } },
                axisLabel: { color: "#888", fontSize: 9 },
            },
            yAxis: {
                type: "value",
                scale: true,
                axisLine: { lineStyle: { color: "#2a2a4a" } },
                axisLabel: { color: "#888", fontSize: 9 },
                splitLine: { lineStyle: { color: "#1a1a2e" } },
            },
            tooltip: {
                trigger: "axis",
                backgroundColor: "#1a1a2e",
                borderColor: "#2a2a4a",
                textStyle: { color: "#e0e0e0" },
            },
            legend: { textStyle: { color: "#888", fontSize: 9 }, top: 0 },
            series: data.series || [],
        });
    });
}
