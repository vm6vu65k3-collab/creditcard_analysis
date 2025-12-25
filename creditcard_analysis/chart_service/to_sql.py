import json, hashlib 
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from ..models import ChartRequest, ChartResult, ResultStatus
from ..utils import get_object_by_column, ChartIn, ChartType, ChartPoint
from ..chart_gener import bar_draw, line_draw, pie_draw, heatmap_draw

class ChartParamsError(Exception):
    def __init__(
        self,
        message: str,
        code   : str = "INVALID_PARAMS",
        field  : str | None = None
    ):
        super().__init__(message)
        self.message = message
        self.code    = code
        self.field   = field

def _stable_json(obj) -> str:
    data = jsonable_encoder(obj, by_alias = True, exclude_none = True)
    return json.dumps(data, sort_keys = True, ensure_ascii = False,separators = (",", ":"))

def _make_cache_key(payload: ChartIn) -> str:
    packed = {
        "chart_type"   : payload.chart_type,
        "params_json"  : payload.params_json,
        "params_figure": payload.params_figure,
        "start_month"  : payload.filters.start_month,
        "end_month"    : payload.filters.end_month,
        "topn"         : payload.filters.topn,
        "industry"     : payload.filters.industry,
        "age_level"    : payload.filters.age_level
    }
    s = _stable_json(packed).encode("utf-8")
    return hashlib.sha256(s).hexdigest()

def to_db_fields(p: ChartIn, cache_key: str):
    return {
        "chart_type"   : p.chart_type.value,
        "params_json"  : jsonable_encoder(p.params_json),
        "params_figure": jsonable_encoder(p.params_figure),
        "cache_key"    : cache_key,
        "status"       : ResultStatus.PENDING.value,
        "file_path"    : None,
        "create_by"    : p.create_by
    }

def to_db_request(p: ChartIn, result_id: int, cache_hit: bool):
    return {
        "chart_type": p.chart_type.value,
        "params_json": jsonable_encoder(p.params_json),
        "cache_hit": cache_hit,
        "result_id": result_id,
    }
    
    
def record_to_sql(db, payload: ChartIn):
    points: list[ChartPoint] | None = None
    cache_key = _make_cache_key(payload)
    result_fields = to_db_fields(payload, cache_key)
    pf  = payload.params_json
    f   = payload.filters
    fig = payload.params_figure

    x_axis = pf.x_axis.value
    y_axis = pf.y_axis.value if pf.y_axis is not None else None
    value  = pf.value.value  if pf.value is not None else None 
    value2 = pf.value2.value if pf.value2 else None
    
    if payload.chart_type == ChartType.heatmap and y_axis is None:
        raise ChartParamsError(
            message = "heatmap 必須提供 y_axis",
            code    = "HEATMAP_MISSING_y_axis",
            field   = "y_axis"
            )

    if payload.chart_type == ChartType.pie and y_axis is not None:
        raise ChartParamsError(
            message = "pie 不需要 y_axis",
            code    = "PIE_NO_NEED_ y_axis",
            field   = "y_axis"
            )

    # ===== 快取命中：直接回傳，但先記一筆 ChartRequest(cache_hit=True) =====
    exist = get_object_by_column(db, ChartResult, "cache_key", cache_key)
    if exist:
        request_fields = to_db_request(payload, exist.id, cache_hit = True)
        db.add(ChartRequest(**request_fields))
        db.commit()
        return {
            "key": cache_key, 
            "url": exist.file_path if exist.status == ResultStatus.READY else None,
            "points": exist.points_json
        }
    else:
        # ===== 新增 ChartResult(PENDING) =====
        try:   
            pending = ChartResult(**result_fields)
            db.add(pending)
            db.flush()
        except IntegrityError:
            db.rollback()
            exist = get_object_by_column(db, ChartResult, "cache_key", cache_key)
            if not exist:
                raise
            request_fields = to_db_request(payload, exist.id, cache_hit = True)
            db.add(ChartRequest(**request_fields))
            db.commit()
            return {"key": cache_key, "url": exist.file_path, "points": exist.points_json}

        # ===== 繪圖 =====
        if payload.chart_type == ChartType.bar:
            file_path, points = bar_draw(
                x_axis = x_axis, value = value, 
                title       = fig.set_title,
                topn        = f.topn,
                start_month = f.start_month,
                end_month   = f.end_month,
                industry    = f.industry,
                age_level   = f.age_level         
            )
        elif payload.chart_type == ChartType.line:
            file_path, points = line_draw(
                x_axis      = x_axis, value = value,
                title       = fig.set_title,
                topn        = f.topn,
                start_month = f.start_month,
                end_month   = f.end_month,
                industry    = f.industry,
                age_level   = f.age_level
            )
        elif payload.chart_type == ChartType.pie:
            file_path, points = pie_draw(
                x_axis      = x_axis, value = value,
                title       = fig.set_title,
                topn        = f.topn,
                start_month = f.start_month,
                end_month   = f.end_month,
                industry    = f.industry,
                age_level   = f.age_level
            )
        elif payload.chart_type == ChartType.heatmap:
            file_path, points = heatmap_draw(
                x_axis, y_axis, value, value2,
                fig.set_title,
                f.start_month,
                f.end_month,
                f.industry,
                f.age_level 
            )

        pending.file_path = file_path
        pending.status = ResultStatus.READY.value
        pending.points_json = jsonable_encoder(points) if points is not None else None
        request_fields = to_db_request(payload, pending.id, cache_hit = False)
        db.add(ChartRequest(**request_fields))
        db.commit()

        return {
            "key": cache_key, 
            "url": file_path, 
            "points": pending.points_json
        }