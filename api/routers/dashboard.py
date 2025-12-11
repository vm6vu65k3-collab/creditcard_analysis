from datetime import datetime 
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func, cast, desc
from sqlalchemy.orm import Session
from ...models import CleanedData
from ...utils import get_db, DashboardResponse, TrendPoint, TopIndustry

router = APIRouter(prefix = "/api/dashboard", tags = ['dashboard'])

@router.get("/overview", response_model = DashboardResponse)
def overview(
    db: Session = Depends(get_db), 
    start_month: str | None = None,
    end_month  : str | None = None,
    industry   : str | None = None,
    age_level  : str | None = None
    ):

    today = datetime.today()
    this_month = today.replace(day=1)

    if start_month is None and end_month is None:
        end_month = this_month
        start_month = end_month - relativedelta(months = 11)
    
    elif start_month is not None and end_month is None:
        end_month = this_month
        start_month = datetime.strptime(start_month, "%Y%m").replace(day=1)
    elif end_month is not None and start_month is None:
        end_month = datetime.strptime(end_month, "%Y%m").replace(day=1)
        start_month = end_month - relativedelta(years=3)
    else:
        start_month = datetime.strptime(start_month, "%Y%m").replace(day=1)
        end_month = datetime.strptime(end_month, "%Y%m").replace(day=1)
    
    start_month = start_month.strftime("%Y%m")
    end_month = end_month.strftime("%Y%m")
        
    base = db.query(CleanedData)


    if age_level is not None:
        base = base.filter(CleanedData.age_level == age_level)
    base = base.filter(
        CleanedData.ym >= start_month,
        CleanedData.ym <= end_month
    )

    
    trend_q = base 
    if industry is not None:
        trend_q = trend_q.filter(CleanedData.industry == industry)
    
    trend_rows = (
        trend_q
        .with_entities(
            CleanedData.ym.label("ym"),
            (func.sum(CleanedData.trans_total) / 1000000000).label("amount")
        )
        .group_by(CleanedData.ym)
        .order_by(CleanedData.ym)
        .all()
    )
    trend = [TrendPoint(ym = r.ym, amount = r.amount) for r in trend_rows]

    
    top_rows = (
        base
        .with_entities(
            CleanedData.industry.label("industry"),
            (func.sum(CleanedData.trans_total) / 1000000000).label("amount")
        )
        .group_by(CleanedData.industry)
        .order_by(desc("amount"))
        .all()
    )
    topn = [TopIndustry(industry = r.industry, amount = r.amount) for r in top_rows]
    
    return DashboardResponse(trend = trend, topn = topn)

