import os 
os.environ["MPLBACKEND"] = "Agg"
import matplotlib 
matplotlib.use("Agg", force = True)

import re
import pandas as pd 
import seaborn as sns
from pathlib import Path 
import matplotlib.pyplot as plt 
from ...database import engine
from ...utils import ChartPoint 
from ..utils import _validate_identifier, _safe_filename, label_zh 
from ..heatmap import build_sql_for_heatmap

plt.rcParams['font.sans-serif'] = ['PingFang TC', 'HeiTi TC', 'Arial Unicode MS', 'Microsoft JhengHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

allow_columns = {"ym", "industry", "age_level", "trans_count", "trans_total"}

def age_sort_key(s: str) -> str:
    s = str(s).strip()
    if s.startswith('未滿20'):
        return 0
    m = re.search(r'\d+', s)
    return int(m.group()) if m else 999

def heatmap_draw(
        x_axis     : str,
        y_axis     : str,
        value      : str,
        value2     : str,
        title      : str,
        start_month: str | None,
        end_month  : str | None,
        industry   : str | None,
        age_level  : str | None
    ):

    # 1) 參數驗證
    _validate_identifier(x_axis, allow_columns)
    _validate_identifier(y_axis, allow_columns)
    _validate_identifier(value, allow_columns)
    _validate_identifier(value2, allow_columns)

    # 2) 取得SQL指令 及 參數
    sql, ym_sql, params = build_sql_for_heatmap(
        x_axis,
        y_axis,
        value,
        value2,
        start_month,
        end_month,
        industry,
        age_level
    )

    ym = pd.read_sql(ym_sql, engine)
    earliest_ym = ym.loc[0, 'earliest_ym']
    latest_ym = ym.loc[0, 'latest_ym']

    if start_month and end_month:
        period = f"{start_month}-{end_month}"
    elif start_month and not end_month:
        period = f"{start_month}-{latest_ym}"
    elif not start_month and end_month:
        period = f"{earliest_ym}-{end_month}"
    else:
        period = f"{earliest_ym}-{latest_ym}"
    
    # 3) 畫圖
    df = pd.read_sql(sql, engine, params = params)
    if df.empty:
        raise ValueError("查無資料，請調整條件")
    
    points = [
        ChartPoint(
            x = row['industry'],
            y = row['age_level'],
            amount = row['avg_amount']
        )
        for _, row in df.iterrows()
    ]

    df['age_level'] = df['age_level'].astype(str).str.strip()
    age_order = sorted(df['age_level'].dropna().unique(), key = age_sort_key)
    # print(age_order)
    df['age_level'] = pd.Categorical(df['age_level'], categories = age_order, ordered = True)

    x_label = label_zh(x_axis)
    y_label = label_zh(y_axis)
    pivot = df.pivot_table(index = 'age_level', columns = 'industry', values = 'avg_amount', aggfunc = 'first', sort = False)
    pivot = pivot.reindex(age_order)
    fig, ax = plt.subplots(figsize = (10, 8))
    sns.heatmap(pivot, annot = True, fmt = ',.2f', cmap = 'YlOrRd', ax = ax)
    final_title = title or f"  {x_label} x {y_label}_平均交易金額"
    ax.set_title(f"{period}{final_title}".strip())
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    fig.tight_layout()
    
    out_dir = Path(__file__).resolve().parent.parent.parent / "chart_storage/heatmap"
    out_dir.mkdir(parents = True, exist_ok = True)

    base = "_".join([p for p in [period, final_title] if p]) or "chart" 
    filename = f"{_safe_filename(base)}_.png"
    path = out_dir / filename

    fig.savefig(path, dpi = 300)
    plt.close() 

    return f"/chart_storage/heatmap/{filename}", points