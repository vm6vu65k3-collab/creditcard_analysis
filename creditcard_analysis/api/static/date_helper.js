// 時間處理
let latestYm = null;
let earliest = null;
function resolvePeriod(){
    const startEl = document.querySelector("#start_month");
    const endEl = document.querySelector("#end_month");

    const startInput = startEl?.value?.trim() || "";
    const endInput = endEl?.value?.trim() || "";

    // 都沒輸入
    if(!startInput && !endInput) {
        const endMonth = latestYm || dateToYm(new Date());
        const startMonth = `${endMonth.slice(0, 4)}01`;
        return {startMonth, endMonth};
    }
    // 只輸入結束
    if (!startInput && endInput) {
        const startMonth = earliest || `201401`;
        if (startEl) startEl.value = startMonth;
        return {startMonth, endMonth: endInput};
    }
    // 只輸入起始
    if (startInput && !endInput) {
        const endMonth = latestYm || dateToYm(new Date());
        if (endEl) endEl.value = endMonth;
        return {startMonth: startInput, endMonth};
    }
    // 兩個都有輸入
    return {startMonth: startInput, endMonth: endInput};

}

function ymToDate(ym){
    const y = Number(ym.slice(0, 4));
    const m = Number(ym.slice(4, 6));
    return new Date(y, m - 1, 1);
}

function dateToYm(d){
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    return `${y}${m}`;
}

function addMonths(d, delta){
    return new Date(d.getFullYear(), d.getMonth() + delta, 1);
}