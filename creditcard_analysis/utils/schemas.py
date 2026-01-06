from enum import Enum
from pydantic import BaseModel, PositiveInt, Field, field_validator, model_validator
from typing import Optional, Tuple, Union, List

#資料庫中允許的欄位名稱

class ChartPoint(BaseModel):
    x     : str
    y     : Optional[Union[float, str]] | None = None
    amount: float | None = None
    share : float | None = None
    growth: float | None = None

class ColumnName(str, Enum):
    year_month  = "ym"
    industry    = "industry"
    age_level   = "age_level"

class ChartType(str, Enum):
    bar  = "bar"
    line = "line"
    pie  = "pie"
    heatmap = "heatmap"
        
class MetricColumn(str, Enum):
    trans_count = "trans_count"
    trans_total = "trans_total"

class Filter(BaseModel):
    start_month  : Optional[str] = None
    end_month    : Optional[str] = None
    topn         : Optional[PositiveInt] = None
    industry     : Optional[str] = None
    age_level    : Optional[str] = None

class ParamsJSON(BaseModel):
    x_axis: ColumnName
    y_axis: Optional[ColumnName] = None
    value : Optional[MetricColumn] = None 
    value2: Optional[MetricColumn] = None
    
    @model_validator(mode = "after")
    def check(self):
        if self.y_axis is not None and self.y_axis == self.x_axis:
            raise ValueError("y_axis 不應與 x_axis 相同")
        return self
        
class ParamsFigure(BaseModel):
    figsize    : Tuple[float, float] = Field(default = (10.0, 8.0), description = "(width, height) in inches")
    set_title  : Optional[str]       = None
    set_xlabel : Optional[str]       = None
    set_ylabel : Optional[str]       = None

    @field_validator("figsize")
    @classmethod 
    def normalize_figsize(cls, v):
        if isinstance(v, (list, tuple)) and len(v) == 2:
            w, h = float(v[0]), float(v[1])
            if w <= 0 or h <= 0:
                raise ValueError("figsize 需為正數")
            return (w, h)
        raise ValueError("figsize 長度應為 2 的序列，例如 [10, 8]")


class ChartIn(BaseModel):
    chart_type   : ChartType
    params_json  : ParamsJSON
    params_figure: ParamsFigure
    create_by    : int
    filters      : Filter

    
    
    @model_validator(mode = "after")
    def cross_checks(self) -> "ChartIn":
        if self.chart_type == ChartType.heatmap and self.params_json.y_axis is None:
            raise ValueError("heatmap 必須提供 y_axis")
        return self

class ChartOut(BaseModel):
    key   : str
    url   : Optional[str] = None
    points: list[ChartPoint] | None = None


class TrendPoint(BaseModel):
    ym    : str
    amount: float

class TopIndustry(BaseModel):
    industry: str
    amount  : float

class TopnPerMonth(BaseModel):
    ym      : str
    industry: str
    amount  : float

class DashboardResponse(BaseModel):
    trend    : List[TrendPoint]
    topn     : List[TopIndustry]
    topn_per_month: List[TopnPerMonth]

