async function loadDashboard(){
    const params     = new URLSearchParams();
    
    const startMonth = document.querySelector("#start_month").value;
    const endMonth   = document.querySelector("#end_month").value;
    const industry   = document.querySelector("#industry_select").value;
    const ageLevel   = document.querySelector("#age_level_select").value;
    if ((startMonth && endMonth) && (startMonth > endMonth)) {
        alert("起始月必須早於結束月");
        return;
    }
    if (startMonth) params.append("start_month", startMonth);
    if (endMonth) params.append("end_month", endMonth);
    if (industry) params.append("industry", industry);
    if (ageLevel) params.append("age_level", ageLevel); 
    
    
    try {
        
        const ps = params.toString();
        const url = ps ? `/api/dashboard/overview?${ps}` : "/api/dashboard/overview";

        const response = await fetch(url);
        if (!response.ok) throw new Error ('Failed fetch /api/dashboard/overview');
        
        const data  = await response.json();
        const trend = data.trend || [];
        const topn  = data.topn || [];
        
        renderTrendChart(trend);
        renderTopnChart(topn);
    } catch (err) {
        console.error(err);
        alert(err.message);
    } 
    finally {
        reset_form_for_dashboard();
    }
}

function bindEvents() {
    const btn = document.querySelector("#apply_filter");
    if (!btn) {
        console.error("找不到 #apply_filter按鈕");
        return;
    }
    btn.addEventListener("click", async (evt) => {
        evt.preventDefault();
        await loadDashboard();
    });
}

window.addEventListener("DOMContentLoaded", async () => {
    await Promise.all([
        load_year_month(),
        load_options_for_dashboard() 
    ]);
    
    bindEvents();

    await loadDashboard();
});


// load_year_month();
// load_options_for_dashboard();
// bindEvents();