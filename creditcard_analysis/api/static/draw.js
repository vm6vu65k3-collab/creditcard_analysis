let chart = null;

function ageSortKey(label) {
    const s = String(label).trim();
    if (s.startsWith('未滿20')) return 0;
    const m = s.match(/\d+/);
    return m ? parseInt(m[0], 10) : 999;
}

function sortAgeLabels(labels) {
    return [...labels].sort((a, b) => {
        const ka = ageSortKey(a);
        const kb = ageSortKey(b);
        if (ka !== kb) return ka - kb;
        return String(a).localeCompare(String(b), 'zh-hant');
    });
}

function sortPointsByAgeLevel(points){
    return [...points].sort((a, b) => {
        const ka = ageSortKey(a.x);
        const kb = ageSortKey(b.x);
        if (ka !== kb) return ka - kb;
        return String(a.x).localeCompare(string(b.x), 'zh-Hant');
    });
}


function getEcharts() {
    const ec = window.echarts;
    if (!ec) {
        console.error("ECharts 尚未載入");
        return null;
    }
    return ec;
}

// =========================== 長條、折線圖 ============================== //
function renderChart(chart_type, period, points, ctx){
    if (!points.length) {
        console.warn("沒有points，可以考慮顯示提示訊息");
        return;
    }
    const { x_axis, y_axis, set_title} = ctx;
   
    const sortedPoints = (x_axis === "age_level") && (chart_type === "line")
        ? sortPointsByAgeLevel(points)
        : points;

    const board = document.querySelector("#board");
    const ec = getEcharts();
    if (!ec) return;
    
    if (!chart) {
        chart = ec.init(board);
    }
    
    const X_AXIS_LABEL = {
        industry: "產業別",
        age_level: "年齡層",
        ym: "年月"
    };

    const Y_AXIS_LABEL = {
        trans_total: "交易金額 (十億元)",
        trans_count: "交易筆數 (千萬筆)"
    };

    const X_DIM_DISPLAY_NAME = {
        industry: "產業",
        age_level: "年齡層",
        ym: "年月"
    };

    const xAxisName = X_AXIS_LABEL[x_axis] || x_axis || "分類";
    const yAxisName = Y_AXIS_LABEL[y_axis] || y_axis || "數值";
    const dimLabel = X_DIM_DISPLAY_NAME[x_axis] || "分類";
    const title = set_title === "" ? "" : `-${set_title}`;
    const titleText = `${period}${title}` || (chart_type === "line" ? "折現圖" : "長條圖");

    const seriesType = chart_type === "line" ? "line" : "bar";

    const showLabelOnSeries = 
        chart_type === "bar" && points.length <= 20;

    const labelConfig = showLabelOnSeries 
        ? {
            show: true,
            position: chart_type === "bar" ? "outside" : "top",
            formatter: (p) => Math.round(p.value).toLocaleString()
          }
        : {
            show: false
          };

    const option = {
        title: {
            text: titleText,
            left: "center"
        },
        xAxis: {
            type: "category",
            name: xAxisName,
            data: sortedPoints.map(p => p.x),
            axisLabel: {
                rotate: x_axis === "age_level" ? 45 : 0
            }
        },
        yAxis: { type: "value", name: yAxisName},
        series: [
            {
                name: yAxisName,
                type: seriesType,
                smooth: chart_type === "line",
                data: sortedPoints.map(p => ({
                    value : p.y,
                    share : p.share,
                    growth: p.growth,
                    name  : p.x,
                })),
                label: labelConfig
            },
        ],
        // 移動到長條圖或折線圖點上顯示的數值
        tooltip: {
            trigger: "axis",
            formatter: (params) => {
                const item = params[0];
                const p = item.data;
                const y = item.value;
                const share  = p.share  != null ? (p.share * 100).toFixed(1) + "%" : "-";
                const growth = p.growth != null ? (p.growth * 100).toFixed(1) + "%" : "-";
                
                const unit = y_axis === "trans_count" ? "筆" : "元";
                console.log(item);
                console.log(p);
                console.log(y);
                return `
                    ${dimLabel}：${p.name}<br/>
                    ${yAxisName}:${y.toLocaleString()} ${unit}<br/>
                    佔比：${share}<br/>
                    成長率：${growth}
                `;
            },
        },
    };

    chart.setOption(option, true);
}

// =========================== 圓餅圖 ============================== //
function renderPieChart(period, points, ctx){
    if(!points.length) {
        console.warn("沒有points");
        return;
    }

    const {x_axis, set_title} = ctx;
    const board = document.querySelector("#board");
    const ec = getEcharts();
    if (!ec) return;
    
    if (!chart) {
        chart = ec.init(board);
    }

    const X_AXIS_LABEL = {
        industry : "產業別",
        age_level: "年齡層",
        ym: "年月"
    }

    const X_DIM_DISPLAY_NAME = {
        industry : "產業",
        age_level: "年齡層",
        ym: "年月"
    };


    // const VALUE_LABEL = {
    //     trans_total: "交易金額"
    // }

    const xAxisName = X_AXIS_LABEL[x_axis] || x_axis || "分類";
    const dimLabel  = X_DIM_DISPLAY_NAME[x_axis] || "分類";
    const titleText = set_title ? `${period}_${set_title}`: `${period}_${xAxisName}圓餅圖`;
    
    const option = {
        title: {
            text: titleText,
            left: "center"
        },
        legend: {
            top: "bottom",
            left: "center"
        },
        series: [
            {
                type  : "pie",
                name  : dimLabel,
                radius: "60%",
                data  : points.map(p => ({
                    name: p.x,
                    value: p.amount,
                })),
                label: {
                    show: true,
                    position: "inside",
                    formatter: p => `${p.value}%`,
                    color: "#000"
                },
                labelLine: {show: false},
            },
            {
                type: "pie",
                radius: "60%",
                data: points.map(p => ({
                    name: p.x,
                    value: p.amount,
                })),
                label: {
                    show: true,
                    position: "outside",
                    formatter: p => p.name,
                    color: "#000"
                },
                labelLine: {
                    show: true,
                    length: 20,
                    length2: 30
                },
                // itemStyle: {
                //     opacity: 0.3
                // },
                emphasis: { disabled: true},
                tooltip: { show: false}
            },

        ]
    };
    chart.setOption(option);
}

// =========================== 熱力圖 ============================== //
function renderHeatMap(period, points, ctx) {
    if (!points.length) {
        console.warn("沒有points");
        return;
    }

    const {x_axis, y_axis, set_title} = ctx;
    const board = document.querySelector("#board");
    const ec = getEcharts();
    if (!ec) return;

    if (!chart) {
        chart = ec.init(board);
    }

    const AXIS_LABEL = {
        industry: "產業別",
        age_level: "年齡層",
        ym: "年月"
    };

    const xAxisName = AXIS_LABEL[x_axis] || x_axis || "欄";
    const yAxisName = AXIS_LABEL[y_axis] || y_axis || "列";
    const titleText = set_title ? `${period}_${set_title}` : `${period}_${xAxisName} x ${yAxisName}`;

    let xCategories = [...new Set(points.map(p => p.x))];
    let yCategories = [...new Set(points.map(p => p.y))];

    if (x_axis === "age_level") xCategories = sortAgeLabels(xCategories);
    if (y_axis === "age_level") yCategories = sortAgeLabels(yCategories);


    const data = points.map(p => {
        const xi = xCategories.indexOf(p.x);
        const yi = yCategories.indexOf(p.y);
        return [xi, yi, Math.round(p.amount)];
    });

    const values = points.map(p => p.amount);
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    console.log("heatmap", minVal, maxVal);
    const option = {
        title : {
            text: titleText,
            left: "center"
        },
        tooltip: {
            trigger: "item",
            position: "top",
            formatter: (params) => {
                const xLabel = xCategories[params.value[0]];
                const yLabel = yCategories[params.value[1]];
                const v      = Math.round(params.value[2]);

                return `
                    ${xAxisName}：${xLabel}<br/>
                    ${yAxisName}：${yLabel}<br/>
                    數值：${v.toLocaleString()}
                `;
            }
        },
        xAxis: {
            type: "category",
            name: xAxisName,
            data: xCategories,
            splitArea: { show: true}
        },
        yAxis: {
            type: "category", 
            name: yAxisName,
            data: yCategories,
            splitArea: { show: true},
            inverse: ctx.y_axis === "age_level"
        },
        grid: {
            top: 80,
            left: 80,
            right: 80,
            bottom: 100
        },
        visualMap: {
            min: minVal,
            max: maxVal,
            calculable: true,
            orient: "vertical",
            left: "right",
            top: "middle"
        },
        series: [
            {
                type: "heatmap",
                name: set_title || "熱力圖",
                data,
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowColor: "rgba(0, 0, 0, 0.5)"
                    }
                },
                label: {
                    show: true,
                    position: "inside",
                    color: "#000",
                    formatter: (p) => {
                        const raw = Array.isArray(p.value) ? Math.round(p.value[2]) : p.value;
                        if (raw == null || isNaN(raw)) return "";

                        return Number(raw).toLocaleString("zh-TW", {
                            // minimumFractionDigits: 2,
                            // maximumFractionDigits: 2,
                        });
                    }
                }
            }
        ]
    };
    
    chart.setOption(option, true);
}