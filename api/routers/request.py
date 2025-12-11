from fastapi import APIRouter, HTTPException
from ...utils import Db, ChartIn, ChartOut, ColumnName, ChartType
from ...chart_service import record_to_sql, ChartParamsError


router = APIRouter(prefix = "/api/request", tags = ['request'])

@router.post("/", response_model = ChartOut, status_code = 201)
def request_chart(payload: ChartIn, db: Db):
    try:
        return record_to_sql(db, payload)
    except ChartParamsError as e:
        raise HTTPException(
            status_code = 422,
            detail = {
                "msg": e.message,
                "code": e.code,
                "field": e.field
            }
        ) 