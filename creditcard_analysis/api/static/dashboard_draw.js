let trendchart = null;
let topnchart = null;
let monthchart = null;

function getEcharts(){
    const ec = window.echarts;
    if (!ec) {
        console.error("ECharts 尚未載入");
        return null;
    }
    return ec;
}

// 折線趨勢圖
function renderTrendChart(data, opts = {}) {
    const { onYmClick } = opts; 
    const board = document.querySelector("#trend_chart");
    if (!board) return;
    if (!board.style.height) {
        board.style.height = "400px";
    }
    const ec = getEcharts();
    if (!ec) return;

    if (!trendchart) {
        trendchart = ec.init(board);
    }

    trendchart.off("click");
    trendchart.on("click", (params) => {
        if (params?.componentType !== 'series') return;
        const ym = params.name;
        if (onYmClick) onYmClick(ym);
    });


    if (Array.isArray(data) && data.length) {
        latestYm = data[data.length - 1].ym;
        earliestYm = data[0].ym;
    }
    
    const { startMonth, endMonth } = resolvePeriod();

    const xAxisName = "年月";
    const yAxisName = "金額(十億元)";
    const industry = document.querySelector("#industry_select").value 
                    ? `[${document.querySelector("#industry_select").value}] `
                    : [];
    const age_level = document.querySelector("#age_level_select").value
                    ? `\n${document.querySelector("#age_level_select").value}`
                    : [];
    const period = `${startMonth}-${endMonth}`;
    const titleText = `${period}${age_level} ${industry}消費趨勢`;

    

    const options = {
        title: {
            text: titleText,
            left: "center"
        },
        xAxis: {
            type: "category",
            name: xAxisName,
            data: data.map(d => d.ym)
        },
        yAxis: { type: "value", name: yAxisName},
        series: [
            {
                name: yAxisName,
                type: "line",
                smooth: true,
                data: data.map(d => d.amount),
            }
        ],
        tooltip: {
            trigger: "axis",
            formatter: (params) => {
                const item = params[0];
                const ym = item.axisValue;
                const y = item.value;
                
                return `
                    ${xAxisName}：${ym}<br/>
                    ${yAxisName}：${y.toLocaleString()}<br/>
                `;
            }
        }
    };

    trendchart.setOption(options, true);
}

// 排行長條圖
function renderTopnChart(data) {
    const board = document.querySelector("#topn_chart");
    if (!board) return;
    if (!board.style.height) {
        board.style.height = "400px";
    }
    const ec = getEcharts();
    if (!ec) return;

    if (!topnchart) {
        topnchart = ec.init(board);
    }

    const { startMonth, endMonth} = resolvePeriod();
    
    const xAxisName = "產業";
    const yAxisName = "金額(十億元)";
    const age_level = document.querySelector("#age_level_select").value
                    ? `\n${document.querySelector("#age_level_select").value}`
                    : [];
    const period = `${startMonth}-${endMonth}`;
    const titleText = `${period}${age_level} 各產業排行`;

    const showLabelOnSeries = true;
    const labelConfig = showLabelOnSeries 
        ? {
            show: true,
            position: "outside",
            formatter: (p) => Math.round(Number(p.value))
            // formatter: (p) => {
            //     const v = Number(p.value);
            //     if (!Number.isFinite(v)) return "0.00";
            //     return v.toLocaleString(undefined, {
            //         minimumFractionDigits: 2,
            //         maximumFractionDigits: 2
            //     });
            // }
          }
        : {
            show: false
          };

    const options = {
        title: {
            text: titleText,
            left: "center"
        },
        xAxis: {
            type: "category",
            name: xAxisName,
            data: data.map(d => d.industry),
        },
        yAxis: { type: "value", name: yAxisName},
        series: [
            {
                name: yAxisName,
                type: "bar",
                smooth: true,
                data: data.map(d => d.amount),
                label: labelConfig
            }
        ],
        tooltip: {
            trigger: "axis",
            formatter: (params) => {
                const item = params[0];
                const name = item.axisValue;
                const y    = item.value;
                return `
                    ${xAxisName}：${name}<br/>
                    ${yAxisName}：${y.toLocaleString()}<br/>
                `;
            }
        }
    };

    topnchart.setOption(options, true);
}

// 月排行長條圖
function renderTopnPerMonthChart(ym, rows, ctx = {}) {
    const { industrySelected, topN = 7 } = ctx;
    
    const board = document.querySelector("#topn_per_month_chart");
    if (!board) return;
    if (!board.style.height) board.style.height = "400px";

    const ec = getEcharts();
    if (!ec) return;

    if (!monthchart) monthchart = ec.init(board);

    const xAxisName = "產業";
    const yAxisName = "金額(十億元)";
    
    if (industrySelected) {
        monthchart.clear()
        monthchart.setOption({
            title: { text: "當月產業組成（已選擇單一產業，略）", left: "center" },
            graphic: [{
                type: "text",
                left: "center",
                top: "middle",
                style: { text: "請清除產業別篩選以查看組成", fontSize: 14 }
            }]
        });
        return;
    }

    if (!ym || !Array.isArray(rows) || rows.length === 0) {
        monthchart.clear();
        monthchart.setOption({
            title: { text: `${ym || ""} 當月產業排行`, left: "center" },
            graphic: [{
              type: "text",
              left: "center",
              top: "middle",
              style: { text: "該月份無資料", fontSize: 14 }
            }]
        });
        return;
    }

    const titleText = `${ym} 當月產業排行`;
    const showLabelOnSeries = true;
    const labelConfig = showLabelOnSeries
        ? {
            show: true,
            position: 'outside',
            formatter: (p) => {
                const v = Number(p.value);
                if (!Number.isFinite(v)) return "0.00";
                return v.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }
        : { show: false};
        
    const options = {
        title: {
            text: titleText,
            left: 'center'
        },
        xAxis: {
            type: 'category',
            name: xAxisName,
            data: rows.map(r => r.industry)
        },
        yAxis: {type: 'value', name: yAxisName},
        series: [
            {
                name: yAxisName,
                type: 'bar',
                data: rows.map(r => r.amount),
                label: labelConfig
            }
        ],
        tooltip: {
            trigger: 'axis',
            formatter: (params) => {
                const item = params[0];
                const name = item.axisValue;
                const y = Number(item.value) || 0;
                return `
                    ${xAxisName}:${name}<br/>
                    ${yAxisName}:${y.toLocaleString()}<b/>
                `;
            }
        }
    };
    monthchart.setOption(options, true);
}