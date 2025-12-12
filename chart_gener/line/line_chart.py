import os 
os.environ["MPLBACKEND"] = "Agg"
import matplotlib 
matplotlib.use("Agg", force = True)

import pandas as pd 
from pathlib import Path 
import matplotlib.pyplot as plt 
import matplotlib.ticker as mticker
from database import engine
from utils import ChartIn, ChartPoint
from .raw_sql import build_sql_for_line
from ..utils import _validate_identifier, _safe_filename, _divisor_and_unit, add_share_and_growth

plt.rcParams['font.sans-serif'] = ['PingFang TC', 'HeiTi TC', 'Arial Unicode MS', 'Micorsoft JhengHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False 

allow_columns = {"ym", "industry", "age_level", "trans_count", "trans_total"}

def line_draw(
        x_axis     : str,
        value      : str,
        title      : str,
        topn       : int,
        start_month: str,
        end_month  : str,
        industry   : str,
        age_level  : str
    ) -> tuple[str, list[ChartPoint]]: 

    # 1) 參數驗證
    _validate_identifier(x_axis, allow_columns)
    _validate_identifier(value, allow_columns)

    # 2) 取得 SQL指令 及 參數
    sql, params = build_sql_for_line(
        x_axis      = x_axis,
        value       = value,
        topn        = topn,
        start_month = start_month,
        end_month   = end_month,
        industry    = industry,
        age_level   = age_level
    )

    period = f"{start_month}-{end_month}"
    
    # 3) 查要畫圖的資料
    df = pd.read_sql(sql, engine, params = params)
    if df.empty:
        raise ValueError("查無資料，請調整條件")
    
    # 4) 資料數值過大可以換算
    div, unit_label = _divisor_and_unit(value)
    df['amount'] = (df['raw_amount'] / div).round(2)
    
    data = add_share_and_growth(df, group_col = "x")

    points = [
        ChartPoint(
            x = row['x'],
            y = row['amount'],
            share = row['share'],
            growth = row['growth']
        )
        for _, row in data.iterrows()
    ]

    # 5) 畫圖
    fig, ax = plt.subplots(figsize = (10, 8))
    line = ax.plot(data['x'], data['amount'], marker = 'o', color = 'steelblue')

    title_prefix = period if period and end_month else start_month or ""
    final_title = (title or f"{x_axis} x {value}") + (" " + unit_label if unit_label else "")
    ax.set_title(f"{title_prefix}{final_title}".strip())
    ax.set_xlabel(x_axis)
    ax.set_ylabel(value)

    # Y軸刻度
    if not data['amount'].empty:
        ax.set_ylim(0, data['amount'].max() * 1.1)
    
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    if x_axis == "age_level":
        ax.set_xticklabels(data['x'], rotation = 45)

    fig.tight_layout()

    # 6) 輸出檔案
    out_dir = Path(__file__).resolve().parent.parent.parent / "chart_storage/line"
    out_dir.mkdir(parents = True, exist_ok = True)

    base = "-".join([p for p in [period, final_title] if p]) or "chart"
    filename = f"{_safe_filename(base)}_.png"
    path = out_dir / filename 

    fig.savefig(path, dpi = 300)
    plt.close()
    return f"/chart_storage/line/{filename}", points