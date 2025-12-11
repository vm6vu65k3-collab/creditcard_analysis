import os 
os.environ["MPLBACKEND"] = "Agg"
import matplotlib 
matplotlib.use("Agg", force = True)

import pandas as pd 
from pathlib import Path 
import matplotlib.pyplot as plt 
from ...database import engine
from ...utils import ChartPoint
from .raw_sql import build_sql_for_pie
from ..utils import _validate_identifier, _safe_filename, _divisor_and_unit

plt.rcParams['font.sans-serif'] = ['PingFang TC', 'HeiTi TC', 'Arial Unicode MS', 'Microsoft JhengHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


allow_columns = {"ym", "industry", "age_level", "trans_count", "trans_total"}

def pie_draw(
        x_axis     : str,
        value      : str,
        title      : str,
        topn       : int,
        start_month: str,
        end_month  : str,
        industry   : str,
        age_level  : str
    ) -> tuple[str, list[ChartPoint]]:
    _validate_identifier(x_axis, allow_columns)
    _validate_identifier(value, allow_columns)

    sql, sql_params = build_sql_for_pie(
        x_axis,
        value,
        topn,
        start_month,
        end_month,
        industry,
        age_level
    )

    period = f"{start_month}-{end_month}"

    df = pd.read_sql(sql, engine, params = sql_params)
    if df.empty:
        raise ValueError("查無資料，請調整條件")

    df['x'] = df['x'].where(df['amount'] >= 0.10, other = "其他")

    points = [
        ChartPoint(
            x      = row['x'],
            amount = row['amount']
        )
        for _, row in df.iterrows()
    ]

    fig, ax = plt.subplots(figsize = (10, 8))

    labels = df['x']
    wedges, texts, autotexts = ax.pie(
        df['amount'],
        labels = labels,
        autopct = '%1.1f%%',
        counterclock = True,
        textprops = {"fontsize": 11} 
    )
    title_prefix = period if period and end_month else start_month or " "
    final_title = (title or f"{x_axis} x {value}")
    ax.set_title(f"{title_prefix}{final_title}".strip())    
    ax.legend(wedges, labels, title = x_axis, loc = 'center left', bbox_to_anchor = (1, 0.5))
    fig.tight_layout()
    
    out_dir = Path(__file__).resolve().parent.parent.parent / "chart_storage/pie"
    out_dir.mkdir(parents = True, exist_ok = True)

    base = "-".join([p for p in [period, final_title] if p]) or "chart"
    filename = f"{_safe_filename(base)}_.png"
    path = out_dir / filename

    fig.savefig(path, dpi = 300)
    plt.close()
    return f"chart_storage/pie/{filename}", points