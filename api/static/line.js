
async function generate_chart(){
    const chart_type = "line";
    const start_month = document.querySelector("#start_month")?.value || null;
    const end_month   = document.querySelector("#end_month")?.value || null;
    const x_axis      = document.querySelector("#x_axis")?.value;
    const y_axis      = document.querySelector("#value")?.value;
    // const value       = document.querySelector("#value")?.value;
    const createByRaw = document.querySelector("#create_by")?.value;
    const create_by   = Number(createByRaw);
    const set_title   = document.querySelector("#set_title")?.value.trim() ?? "";

    if (!x_axis || !y_axis || !createByRaw){
        alert("員工編號、Ｘ軸、Y軸 不可空白");
        return;
    }
    
    if ((end_month && start_month) && (start_month > end_month)){
        alert("起始月比須早於結束月");
        return;
    } 


    const payload = {
        chart_type,
        params_json: {x_axis, value: y_axis},
        params_figure: {set_title},
        create_by: Number.isFinite(create_by)? create_by : 0,
        filters: {
            start_month,
            end_month
        }
    };
    try {
        const response = await fetch("/api/request", {
            method: "POST",
            headers: {"Content-type": "application/json"},
            body: JSON.stringify(payload)
    
        });
        if (!response.ok) {
            const err = await response.json().catch();
            throw new Error (`製圖失敗：${response.status} ${JSON.stringify(err)}`);
        }
        const result = await response.json();
        const points = result.points || [];
        const period = normalize(start_month, end_month);

        renderChart(chart_type, period, points, {
            x_axis,
            y_axis,
            set_title
        });

        const btnDownload = document.querySelector("#btn_download_img");
        if (btnDownload) {
            btnDownload.onclick = () => {
                if (!result.url) return;
                const a = document.createElement("a");
                a.href = result.url;
                a.download = set_title || `${chart_type}chart`;
                a.click();   
            };
        }
        
    } catch (err) {
        console.error(err);
        alert(err.message);
    } finally {
        reset_form();
    }   
}

function bindEvents() {
    const btn = document.querySelector("#btn_generate");
    if (!btn) {
        console.error("找不到 #btn_generate按鈕");
        return;
    }
    btn.addEventListener("click", (evt) => {
        evt.preventDefault();
        generate_chart();
    });
}

load_year_month();
load_options({ yNullable: true});
load_value({ value2Nullable: false});
bindEvents();