// 針對可下拉選項的欄位做載入的處理
function fillSelect(selector, options, {
    placeholder = "- 請選擇 -",
    nullable = false, 
} = {}) {
    const el = document.querySelector(selector);
    el.replaceChildren();
    const frag = document.createDocumentFragment();
    const ph = document.createElement("option");
    ph.value = "";
    ph.textContent = placeholder;
    ph.selected = true;

    frag.appendChild(ph);
    
    options.forEach(({ key, value}) => {
        const opt = document.createElement("option");
        opt.value = value;
        opt.textContent = value;
        frag.appendChild(opt);
    });
    el.appendChild(frag);

    el.value = "";
    el.classList.add("is_placeholder");
    el.addEventListener("change", () => {
        el.classList.toggle("is_placeholder", el.value === "");
    })
}

// 篩選圖上數值的欄位
async function load_value( value2Nullable = true) {
    try {
        const response = await fetch("/meta/value");
        if (!response.ok) throw new Error("Failed fetch /value");
        const value = await response.json();

        fillSelect("#value", value);
        
        const value2El = document.querySelector("#value2");
        if (value2Nullable && value2El) {
            fillSelect("#value2", value);
        }
    } catch(err) {
        console.error(err);
    }
}

// 載入年月份清單
async function load_year_month() {
    try {
        const response = await fetch("/meta/year_month");
        if (!response.ok) throw new Error("Failed fetch /year_month");
        const ym = await response.json();
        
        fillSelect("#start_month", ym);
        fillSelect("#end_month", ym);
    } catch (err) {
        console.error(err);
    }
}

// 載入欄位名稱
async function load_options({ yNullable = false} = {}){
    try {
        const response = await fetch("/meta/column");
        if (!response.ok) throw new Error("Failed fetch /column");
        const column = await response.json();

        const yEl = document.querySelector("#y_axis");
        fillSelect("#x_axis", column);
        if (yEl) {
            if (!yNullable) {
                fillSelect("#y_axis", column);        
            }
        }

    } catch (err) {
        console.error(err);
    }
}

function reset_form(){
    ["create_by", "set_title"].forEach(id => {
        const el = document.getElementById(id); 
        if(el) el.value = "";
    });

    ['start_month', 'end_month', 'x_axis', 'y_axis', 'value', 'value2'].forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.selectedIndex = 0;
        el.value = "";
        el.classList.add("is_placeholder");
    });
}

function normalize(start_month, end_month) {
    const normal = (v) => {
        if (v == null) return "";
        if (v === "" || v === "null") return "";
        return v;
    };

    const s = normal(start_month);
    const e = normal(end_month);
    let period = "";
    if (s && e) {
    period = `${s}-${e}`;
    } else if (s) {
        period = `${s}-截至本月`
    } else if (e) {
        period = `截至${e}`
    }
    return period;
}


// ==================== 儀表板用 ====================
async function load_options_for_dashboard(){
    try {
        const response = await fetch('/meta/industry');
        if (!response.ok) throw new Error ("Failed fetch /meta/industry")
        const industry = await response.json();
        fillSelect("#industry_select", industry)

        const response1 = await fetch('/meta/age_level');
        if (!response1.ok) throw new Error('Failed fetch /age_level')
        const age_level = await response1.json();
        fillSelect("#age_level_select", age_level)

    } catch(err) {
        console.error(err);
    }
}

function reset_form_for_dashboard(){
    ['start_month', 'end_month', 'industry_select', 'age_level_select'].forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.selectedIndex = 0;
        el.value = "";
        el.classList.add("is_placeholder");
    });
}
