import os 
os.environ["MPLBACKEND"] = "Agg"
import matplotlib 
matplotlib.use("Agg", force = True)

import pandas as pd 
from pathlib import Path 
import matplotlib.pyplot as plt 
import matplotlib.ticker as mticker
# from ..utils import get_path
from ...database import engine
from ...utils import ChartPoint
from .raw_sql import build_sql_raw
from ..utils import _validate_identifier, _safe_filename, _divisor_and_unit, add_share_and_growth, label_zh



plt.rcParams['font.sans-serif'] = ['PingFang TC', 'HeiTi TC', 'Arial Unicode MS', 'Microsoft JhengHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


allow_columns = {"ym", "industry", "age_level", "trans_count", "trans_total"}


    
def bar_draw(
        x_axis     : str,
        value      : str,
        title      : str,
        topn       : int,
        start_month: str,
        end_month  : str,
        industry   : str,
        age_level  : str
    ) -> tuple[str, list[ChartPoint]]:
    # 1) 驗證
    _validate_identifier(x_axis, allow_columns)
    _validate_identifier(value, allow_columns)

    # 2) 取 SQL + params
    sql, params = build_sql_raw(
        x_axis,
        value,     
        topn,       
        start_month,
        end_month,
        industry,
        age_level
    ) 
    
    period = f"{start_month}-{end_month}"

    # 3) 查資料（記得帶 params)
    df = pd.read_sql(sql, engine, params = params)
    if df.empty:
        raise ValueError("查無資料，請調整條件")
    
    # 4) 單位換算（版本 B）
    div, unit_label = _divisor_and_unit(value)
    df['amount'] = (df['raw_amount'] / div).round(2)

    data = add_share_and_growth(df, group_col = "x")

    points = [
        ChartPoint(
            x = row['x'],
            y = row['amount'],
            share = row.get("share"),
            growth = row.get("growth"),
        )
        for _, row in data.iterrows()
    ]

    # 5) 畫圖（條形圖示例）
    fig, ax = plt.subplots(figsize = (10, 8))
    bar = ax.bar(data['x'], data['amount'], color = 'steelblue', edgecolor = 'black')
    
    # 標題/座標
    x_label = label_zh(x_axis)
    y_label = label_zh(value)
    title_prefix = period if period and end_month else start_month or " "
    final_title = (title or f"{x_label} x {y_label}") + (" " + unit_label if unit_label else "")
    ax.set_title(f"{title_prefix}{final_title}".strip())
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if x_axis == "age_level":
        ax.set_xticklabels(data['x'], rotation = 45)
    
    # Y 軸刻度格式
    if not data['amount'].empty:
        ax.set_ylim(0, data['amount'].max() * 1.1)

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))

    # 標籤
    ax.bar_label(bar, labels = [f'{v:,.0f}' for v in data['amount']], fontsize = 12)
    

    fig.tight_layout()
    
    # 6) 輸出檔案
    out_dir = Path(__file__).resolve().parent.parent.parent / "chart_storage/bar"
    out_dir.mkdir(parents = True, exist_ok = True)
    
    base = "-".join([p for p in [period, final_title] if p]) or "chart"
    filename = f"{_safe_filename(base)}_.png"
    path = out_dir / filename

    fig.savefig(path, dpi = 300)
    plt.close()
    print("Save to:", path)
    return f"/chart_storage/bar/{filename}", points