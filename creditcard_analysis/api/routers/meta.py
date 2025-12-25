from fastapi import APIRouter 
from sqlalchemy.orm import Session 
from ...models import CleanedData
from ...database import SessionLocal
from ...utils import ColumnName, MetricColumn, ChartType, Option, MetaPayload, Db

router = APIRouter(prefix = "/meta", tags = ["meta"])

@router.get("/column", response_model = list[Option])
def column_list():
    return [Option(key = t.name, value = t.value) for t in ColumnName]

@router.get("/value", response_model = list[Option])
def value_list():
    return [Option(key = t.name, value = t.value) for t in MetricColumn]

@router.get("/year_month", response_model = list[Option])
def year_month_list(db: Db):
    rows = (
        db.query(CleanedData.ym)
          .distinct()
          .order_by(CleanedData.ym)
          .all()
    )
    return [Option(key = ym[0], value = ym[0]) for ym in rows]

@router.get("/chart_type", response_model = list[Option])
def chart_type_list():
    return [Option(key = t.name, value = t.value) for t in ChartType]

@router.get("/industry", response_model = list[Option])
def industry_list(db: Db):
    rows = (
        db.query(CleanedData.industry)
            .distinct()
            .order_by(CleanedData.industry)
            .all()
    )
    return [Option(key = ind[0], value = ind[0]) for ind in rows]

@router.get("/age_level", response_model = list[Option])
def age_level_list(db: Db):
    rows = (
        db.query(CleanedData.age_level)
          .distinct()
          .order_by(CleanedData.age_level)
          .all()
    )
    return [Option(key = age[0], value = age[0]) for age in rows]