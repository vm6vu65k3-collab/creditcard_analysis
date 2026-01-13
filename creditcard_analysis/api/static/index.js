async function init() {
    await load_year_month();
    bindEvents();
}

init().catch(console.error);


const ANALYSIS_CONFIG = {
    "1": {
        chart_type: "bar",
        x_axis    : "industry",
        value     : "trans_total",
        set_title : "各產業交易金額"
    },
    "2": {
        chart_type: "heatmap",
        x_axis    : "industry",
        y_axis    : "age_level",
        value     : "trans_total",
        value2    : "trans_count",
        set_title : "各產業所有族群平均消費金額"
    }
};

const DEFAULT_CREATE_BY = 999999;

async function top_analysis(kind) {
    const config = ANALYSIS_CONFIG[kind];
    if (!config) {
        console.error("未知的分析種類", kind);
        alert("未知的分析種類");
        return;
    }

    if (chart) {
        chart.dispose();
        chart = null;
    }

    const { chart_type, x_axis, y_axis, value, value2, set_title} = config;
    const params_json = { x_axis, value};
    if (y_axis) params_json.y_axis = y_axis;
    if (value2) params_json.value2 = value2;

    const payload = {
        chart_type,
        params_json,
        params_figure: {set_title},
        create_by: DEFAULT_CREATE_BY,
        filters: getDefaultFilters()
    };

    console.log(payload);
    try {
        const response = await fetch("/api/request", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });
        
        if(!response.ok) {
            const err = response.json().catch();
            throw new Error(`製圖失敗：${response.status} ${JSON.stringify(err)}`);
        }
        
        const result = await response.json();
        const points = result.points || [];
        const period = `${payload.filters.start_month}-${payload.filters.end_month}`;

        if (chart_type === "bar") {
            
            renderChart(chart_type, period, points, {
                x_axis,
                value,
                set_title,
            });
        } else if (chart_type === "heatmap") {
            renderHeatMap(period, points, {
                x_axis,
                y_axis,
                set_title
            })
        } else {
            console.error("未知的分種類", chart_type);
            alert("未知的分析種類");
            return;
        }

    } catch(err) {
        console.error(err);
        alert(err.message);
    }
}

function bindEvents(){
    document.querySelectorAll("[data-analysis]").forEach(btn => {
        btn.addEventListener("click", () => {            
            const kind = btn.dataset.analysis;
            top_analysis(kind);
        });
    });
}

// bindEvents();