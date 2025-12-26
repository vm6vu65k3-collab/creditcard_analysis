from sqlalchemy import text 
from ..utils import clamp, where_sql_params, check_valid_column

def build_sql_for_heatmap(
        x_axis     : str,
        y_axis     : str,
        value      : str,
        value2     : str,
        start_month: str | None = None,
        end_month  : str | None = None,
        industry   : str | None = None,
        age_level  : str | None = None
    ):
    if value != "trans_total" or value2 != "trans_count":
        raise ValueError("heatmap 只允許 trans_total / trans_count")

    check_valid_column(x_axis, y_axis, value, value2)

    where_sql, params = where_sql_params(
        start_month, end_month, industry, age_level
    )

    order_clause = "ORDER BY industry, age_level" 
    if x_axis == "age_level":
        order_clause = f"ORDER BY age_level ASC, industry"
    elif y_axis == "age_level":
        order_clause = f"ORDER BY age_level ASC, industry"


    sql = f"""
        SELECT
            {x_axis} AS industry,
            {y_axis} AS age_level,
            SUM({value}) / NULLIF(SUM({value2}), 0)  AS avg_amount
        FROM clean_data
        {where_sql}
        GROUP BY {x_axis}, {y_axis}
        {order_clause}
    """

    ym_sql = """
        SELECT 
            MIN(ym) AS earliest_ym,
            MAX(ym) AS latest_ym
        FROM clean_data
    """


    return text(sql), text(ym_sql), params