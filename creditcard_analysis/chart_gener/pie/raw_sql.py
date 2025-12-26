from sqlalchemy import text 
from ..utils import clamp, where_sql_params, check_valid_column
def build_sql_for_pie(
    x_axis     : str,
    value      : str,
    topn       : int | None = None,
    start_month: str | None = None,
    end_month  : str | None = None,
    industry   : str | None = None,
    age_level  : str | None = None
):
    
    check_valid_column(x_axis = x_axis, value = value)
    

    where_sql, params = where_sql_params(
        start_month,
        end_month,
        industry,
        age_level
    )

    is_time_x = (x_axis == "ym")
    default_topn = 20
    eff_topn = clamp(topn if topn else default_topn, 1 ,200)
    order_clause = "ORDER BY x ASC" if is_time_x else "ORDER BY amount DESC"
    limit_clause = "LIMIT :limit"

    sql = f"""
    SELECT
        u.x,
        SUM(u.pct) AS amount
    FROM (
        SELECT
            CASE 
                WHEN s.pct < 10 THEN '其他' 
                ELSE s.x 
            END AS x,
            s.pct
        FROM (
            SELECT 
                t.{x_axis} AS x,
                ROUND((t.group_amount / totals.total_amount), 2) * 100 AS pct
            FROM (
                SELECT 
                    {x_axis},
                    SUM({value}) AS group_amount
                FROM clean_data
                {where_sql}
                GROUP BY {x_axis}
            ) t
            CROSS JOIN (
                SELECT SUM({value}) AS total_amount
                FROM clean_data
                {where_sql}
            ) totals
        ) s
    ) u
    GROUP BY x
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