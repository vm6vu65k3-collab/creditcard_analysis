from sqlalchemy import text 
from sqlalchemy.dialects import mysql
from ..utils import clamp, where_sql_params, check_valid_column, DIM_COLS, METRIC_COLS

def build_sql_raw(
        x_axis     : str,
        value      : str,
        topn       : int | None = None,
        start_month: str | None = None,
        end_month  : str | None = None,
        industry   : str | None = None,
        age_level  : str | None = None,
):
    check_valid_column(x_axis, value = value)

    # select_y = f", {y_axis} AS y" if y_axis else ""
    
    where_sql, params = where_sql_params(
        start_month = start_month,
        end_month   = end_month,
        industry    = industry,
        age_level   = age_level
    )
    
    # group_y  = f", {y_axis}"      if y_axis else ""

    is_time_x = (x_axis == 'ym')
    default_topn = 20
    eff_topn = clamp(topn if topn is not None else default_topn, 1, 200)

    order_clause = "ORDER BY x ASC" if is_time_x else "ORDER BY raw_amount DESC" 
    limit_clause = "" if is_time_x else "LIMIT :limit"

    

    sql = f"""
        SELECT
            {x_axis} AS x,
            SUM({value}) AS raw_amount
        FROM clean_data
        {where_sql}
        GROUP BY {x_axis}
        {order_clause}
        {limit_clause}
    """

    if not is_time_x:
        params['limit'] = eff_topn

    ym_sql = """
        SELECT
            MIN(ym) AS earliest_ym,
            MAX(ym) AS latest_ym
        FROM clean_data
    """

    return text(sql), text(ym_sql), params