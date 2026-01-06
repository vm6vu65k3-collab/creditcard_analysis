from datetime import datetime 
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func, cast, desc
from sqlalchemy.orm import Session
from ...models import CleanedData
from ...utils import get_db, DashboardResponse, TrendPoint, TopIndustry, TopnPerMonth

router = APIRouter(prefix = "/api/dashboard", tags = ['dashboard'])

UNIT_PER_AMOUNT = 1000000000

def ym_to_dt(ym: str) -> datetime:
    return datetime.strptime(str(ym), '%Y%m').replace(day = 1)

@router.get("/overview", response_model = DashboardResponse)
def overview(
    db: Session = Depends(get_db), 
    start_month: str | None = None,
    end_month  : str | None = None,
    industry   : str | None = None,
    age_level  : str | None = None
    ):

    latest_ym, earliest_ym = db.query(
        func.max(CleanedData.ym), 
        func.min(CleanedData.ym)
        ).one()
    
    latest_ym = ym_to_dt(latest_ym)
    earliest_ym = ym_to_dt(earliest_ym)

    if start_month is None and end_month is None:
        end_month   = latest_ym
        start_month = latest_ym.replace(month = 1)

    elif start_month is not None and end_month is None:
        end_month   = latest_ym
        start_month = ym_to_dt(start_month)
    
    elif end_month is not None and start_month is None:
        end_month   = ym_to_dt(end_month)
        start_month = earliest_ym
    
    else:
        start_month = ym_to_dt(start_month)
        end_month   = ym_to_dt(end_month)
    
    start_month = start_month.strftime("%Y%m")
    end_month   = end_month.strftime("%Y%m")

    base = db.query(CleanedData).filter(
        CleanedData.ym >= start_month,
        CleanedData.ym <= end_month
    )

    if age_level is not None:
        base = base.filter(CleanedData.age_level == age_level)
    
    trend_q = base 
    if industry is not None:
        trend_q = trend_q.filter(CleanedData.industry == industry)
    
    trend_rows = (
        trend_q
        .with_entities(
            CleanedData.ym.label("ym"),
            (func.sum(CleanedData.trans_total) / UNIT_PER_AMOUNT).label("amount")
        )
        .group_by(CleanedData.ym)
        .order_by(CleanedData.ym)
        .all()
    )
    trend = [TrendPoint(ym = r.ym, amount = float(r.amount)) for r in trend_rows]
    
    amount = (func.sum(CleanedData.trans_total) / UNIT_PER_AMOUNT).label('amount')
    topn_per_month_rows= (
        base
        .with_entities(
            CleanedData.ym.label('ym'),
            CleanedData.industry.label('industry'),
            amount
        )
        .group_by(CleanedData.ym, CleanedData.industry)
        .order_by(CleanedData.ym, amount.desc())
        .all()
    )
    topn_per_month = [
        TopnPerMonth(ym = r.ym, industry = r.industry, amount = float(r.amount)) 
        for r in topn_per_month_rows
    ]
    
    
    top_rows = (
        base
        .with_entities(
            CleanedData.industry.label("industry"),
            (func.sum(CleanedData.trans_total) / UNIT_PER_AMOUNT).label("amount")
        )
        .group_by(CleanedData.industry)
        .order_by(desc("amount"))
        .all()
    )
    topn = [TopIndustry(industry = r.industry, amount = float(r.amount)) for r in top_rows]
    return DashboardResponse(trend = trend, topn = topn, topn_per_month = topn_per_month)

