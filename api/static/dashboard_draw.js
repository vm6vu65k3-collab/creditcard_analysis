let trendchart = null;
let topnchart = null;

function getEcharts(){
    const ec = window.echarts;
    if (!ec) {
        console.error("ECharts 尚未載入");
        return null;
    }
    return ec;
}

function renderTrendChart(data) {
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


    
    const xAxisName = "年月";
    const yAxisName = "金額(十億元)";
    const startMonth = document.querySelector("#start_month").value 
                    ? document.querySelector("#start_month").value 
                    : `${new Date().getFullYear()}01`;
    const endMonth = document.querySelector("#end_month").value 
                    ? document.querySelector("#end_month").value
                    : "目前";
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


    
    const xAxisName = "產業";
    const yAxisName = "金額(十億元)";
    const startMonth = document.querySelector("#start_month").value 
                        ? document.querySelector("#start_month").value 
                        : `${new Date().getFullYear()}01`;
    const endMonth = document.querySelector("#end_month").value 
                        ? document.querySelector("#end_month").value
                        : "目前";
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
            formatter: (p) => Math.round(p.value).toLocaleString()
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