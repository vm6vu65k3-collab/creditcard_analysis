import re, pandas as pd  

DIM_COLS    = {"ym", "industry", "age_level"}
METRIC_COLS = {"trans_count", "trans_total"}

LABEL_ZH = {
    "ym"         : "年月",
    "industry"   : "產業別",
    "age_level"  : "年齡層",
    "trans_count": "交易筆數",
    "trans_total": "交易金額"
}

def label_zh(key: str) -> str:
    return LABEL_ZH.get(key, key)

def _validate_identifier(name:str, allowed):
    if name is None:
        return 
    if name not in allowed:
        raise ValueError(f"invalid column: {name}")

def _safe_filename(s: str) -> str:
    return re.sub(r"[^-\w\u4e00-\u9fff]", "-", s).strip("_")

def _divisor_and_unit(metric: str) -> tuple[int, str]:
    if metric == "trans_count":
        return 10_000_000, " (單位：千萬筆) "
    elif metric == "trans_total":
        return 1_000_000_000, " (單位：十億元)"
    else:
        return 1, ""
    
def check_valid_column(
        x_axis: str | None = None,
        y_axis: str | None = None,
        value: str | None = None,
        value2: str | None = None,
):
    errors: list[str] = []
    
    checks = [
        ("x_axis", x_axis, DIM_COLS),
        ("y_axis", y_axis, DIM_COLS),
        ("value", value, METRIC_COLS),
        ("value2", value2, METRIC_COLS),
    ]

    for name, v, allowed in checks:
        if v is None:
            continue 
        if name == "y_axis" and v is None:
            continue 
        if v not in allowed:
            errors.append(f"{name}={v!r} 不在資料欄位裡")
    if errors:
        msg = " ; ".join(errors)
        raise ValueError(msg)
    

def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(n, hi))

def where_sql_params(
    start_month: str | None = None,
    end_month  : str | None = None,
    industry   : str | None = None,
    age_level  : str | None = None
):
    conds: list[str] = []
    params: dict[str, str] = {}
    if start_month is not None:
        conds.append("ym>= :yf")
        params['yf'] = start_month 
    
    if end_month is not None:
        conds.append("ym <= :yt")
        params['yt'] = end_month 
    
    if industry is not None:
        conds.append("industry = :industry")
        params['industry'] = industry 
    
    if age_level is not None:
        conds.append("age_level = :age_level")
        params['age_level'] = age_level
    
    where_sql = ("WHERE " + " AND ".join(conds)) if conds else ""

    return where_sql, params 

def add_share_and_growth(df: pd.DataFrame, group_col: str, time_col: str | None = None):
    df = df.copy()
    
    total = df['amount'].sum()
    df['share'] = (df['amount'] / total).round(2)
    
    if time_col is not None:
        df = df.sort_values([group_col, time_col])
        df["growth"] = df.groupby(group_col)["amount"].pct_change()
    else:
        df['growth'] = None
    
    return df


