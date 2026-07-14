// API 请求封装
const API = {
    async getStockAnalysis(tsCode, days = 120) {
        const res = await fetch(`/api/stock/${tsCode}?days=${days}`);
        return res.json();
    },

    async getStockKline(tsCode, days = 120) {
        const res = await fetch(`/api/stock/${tsCode}/kline?days=${days}`);
        return res.json();
    },

    async getStockSignals(tsCode, days = 120) {
        const res = await fetch(`/api/stock/${tsCode}/signals?days=${days}`);
        return res.json();
    },

    async screener(strategy = "b1", maxStocks = 500) {
        const res = await fetch(`/api/screener?strategy=${strategy}&max_stocks=${maxStocks}`);
        return res.json();
    },

    async historicalScreener(req) {
        const res = await fetch("/api/screener/historical", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(req),
        });
        return res.json();
    },

    async searchStocks(q, limit = 20) {
        const res = await fetch(`/api/stock/search/all?q=${encodeURIComponent(q)}&limit=${limit}`);
        return res.json();
    },

    async getStockScore(tsCode) {
        const res = await fetch(`/api/screener/score/${tsCode}`);
        return res.json();
    },

    async backtest(req) {
        const res = await fetch("/api/backtest", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(req),
        });
        return res.json();
    },

    async tuneBacktest(req) {
        const res = await fetch("/api/backtest/tune", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(req),
        });
        return res.json();
    },

    async historicalScreener(req) {
        const res = await fetch("/api/backtest/screener", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(req),
        });
        return res.json();
    },

    async trainingScreen(req) {
        const res = await fetch("/api/training/screen", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(req),
        });
        return res.json();
    },

    async trainingKline(req) {
        const res = await fetch("/api/training/kline", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(req),
        });
        return res.json();
    },

    async diagnosePortfolio(holdings, days = 100) {
        const res = await fetch("/api/portfolio/diagnose", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ holdings, days }),
        });
        return res.json();
    },
};
