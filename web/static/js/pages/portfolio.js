// 持仓诊断页交互

async function runDiagnose() {
    const input = document.getElementById("holdings-input").value.trim();
    const container = document.getElementById("diagnose-result");
    const holdings = input.split("\n").map((s) => s.trim()).filter((s) => s.length > 0);

    if (holdings.length === 0) {
        container.innerHTML = '<p style="color:var(--text-dim)">请输入至少一个股票代码</p>';
        return;
    }

    container.innerHTML = '<p style="color:var(--text-dim)">诊断中...</p>';

    try {
        const data = await API.diagnosePortfolio(holdings, 100);

        let html = '<div style="display:grid;gap:1rem">';
        data.results.forEach((r) => {
            const riskColor = r.risk_level === "HIGH" || r.risk_level === "CRITICAL" ? "var(--red)" : r.risk_level === "MEDIUM" ? "var(--accent)" : "var(--green)";
            html += `<div style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:1.5rem">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem">
                    <h3 style="color:var(--accent)">${r.ts_code} ${r.name}</h3>
                    <span style="color:${riskColor};font-weight:bold;font-size:0.85rem">${r.risk_level}</span>
                </div>
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:0.75rem;margin-bottom:0.75rem">
                    <div><span style="color:var(--text-dim);font-size:0.8rem">当前价</span><br>${r.price.toFixed(2)}</div>
                    <div><span style="color:var(--text-dim);font-size:0.8rem">KDJ-J</span><br>${r.kdj_j.toFixed(1)}</div>
                    <div><span style="color:var(--text-dim);font-size:0.8rem">BBI</span><br>${r.bbi.toFixed(2)}</div>
                    <div><span style="color:var(--text-dim);font-size:0.8rem">白线</span><br>${r.white_line.toFixed(2)}</div>
                    <div><span style="color:var(--text-dim);font-size:0.8rem">黄线</span><br>${r.yellow_line.toFixed(2)}</div>
                    <div><span style="color:var(--text-dim);font-size:0.8rem">防卖飞</span><br>${r.sell_score}/5 ${r.sell_score_desc}</div>
                    <div><span style="color:var(--text-dim);font-size:0.8rem">麒麟阶段</span><br>${r.kirin_phase}</div>
                    <div><span style="color:var(--text-dim);font-size:0.8rem">止损价</span><br>${r.stop_loss ? r.stop_loss.toFixed(2) : "-"}</div>
                    <div><span style="color:var(--text-dim);font-size:0.8rem">目标价</span><br>${r.target_price ? r.target_price.toFixed(2) : "-"}</div>
                </div>`;

            if (r.macd_veto) {
                html += '<p style="color:var(--red);font-size:0.85rem;margin-bottom:0.5rem">⚠ MACD 一票否决（不能买）</p>';
            }

            if (r.exit_signals.length > 0) {
                html += '<div style="margin-bottom:0.5rem"><span style="color:var(--text-dim);font-size:0.85rem">卖出信号:</span><br>';
                r.exit_signals.forEach((sig) => {
                    html += `<span style="color:var(--green);font-size:0.85rem;margin-right:0.5rem">${sig.signal_type || sig.type || JSON.stringify(sig).substring(0, 50)}</span>`;
                });
                html += '</div>';
            }

            if (r.buy_signals.length > 0) {
                html += '<div style="margin-bottom:0.5rem"><span style="color:var(--text-dim);font-size:0.85rem">买入信号:</span><br>';
                r.buy_signals.forEach((sig) => {
                    html += `<span style="color:var(--red);font-size:0.85rem;margin-right:0.5rem">${sig.strategy || sig.signal_type || sig.type || JSON.stringify(sig).substring(0, 50)}</span>`;
                });
                html += '</div>';
            }

            if (r.recommendation) {
                html += `<p style="color:var(--text);font-size:0.85rem;margin-top:0.5rem;padding:0.5rem;background:var(--bg);border-radius:4px">${r.recommendation}</p>`;
            }

            html += '</div>';
        });
        html += '</div>';
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<p style="color:var(--red)">诊断失败: ${e.message}</p>`;
    }
}
