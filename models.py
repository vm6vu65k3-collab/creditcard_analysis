import enum
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, ForeignKey, JSON, Enum, func
from sqlalchemy.orm import relationship
from .database import Base 

class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key = True, comment = 'ID主鍵')

class ResultStatus(enum.Enum):
    PENDING = "PENDING"
    READY   = "READY"
    FAILED  = "FAILED"

class ChartRequest(BaseModel):
    __tablename__ = "chart_requests"
    chart_type  = Column(String(50), nullable = False, comment = "圖形類別")
    params_json = Column(JSON, nullable = False, comment = "參數")
    cache_hit   = Column(Boolean, default = False, nullable = False, comment = "是否命中快取")
    result_id   = Column(Integer, ForeignKey("chart_results.id", ondelete = "CASCADE"), nullable = True, comment = "結果ID")
    create_at   = Column(DateTime, server_default = func.now(), comment = "查詢時間")
    
    result = relationship("ChartResult", back_populates = "requests")

    def __repr__(self):
        return (f"<ChartRequest(id = {self.id}, chart_type = {self.chart_type},"
                f"cache_hit = {self.cache_hit}, result_id = {self.result_id})>" 
        )

class ChartResult(BaseModel):
    __tablename__ = "chart_results"
    chart_type    = Column(String(50), nullable = False, comment = "圖形類別")
    params_json   = Column(JSON, nullable = False, comment = "參數")
    params_figure = Column(JSON, nullable = False, comment = "圖表大項")
    points_json   = Column(JSON, nullable = True, comment = "圖表指標")
    cache_key     = Column(String(100), nullable = False, unique = True, index = True, comment = '唯一索引')
    status        = Column(Enum(ResultStatus, name = "result_status_enum"),
                    default  = ResultStatus.PENDING,
                    nullable = False,
                    comment  = "產製狀態"
    )
    file_path = Column(String(100), nullable = True, comment = "圖檔路徑")
    create_by = Column(Integer, nullable = True, comment = "建立者ID")
    create_at = Column(DateTime, server_default = func.now(), comment = "建立時間")
    update_at = Column(DateTime, server_default = func.now(), onupdate = func.now(), comment = "更新時間")
    
    requests = relationship("ChartRequest", back_populates = "result", 
                            cascade = "all, delete-orphan", passive_deletes = True)

    def __repr__(self):
        return (f"<ChartResult(id = {self.id}, chart_type = {self.chart_type},"
                f"cache_key = {self.cache_key}, status = {self.status.name})>"
        )
    
class CleanedData(BaseModel):
    __tablename__ = "clean_data"
    ym          = Column (String(20), nullable = False, comment = "年月")
    nation      = Column(String(20), nullable = False, comment = "地區")
    industry    = Column(String(20), nullable = False, comment = "產業別")
    age_level   = Column(String(20), nullable = False, comment = "年齡層")
    trans_count = Column(BigInteger, nullable = False, comment = "交易筆數")
    trans_total = Column(BigInteger, nullable = False, comment = "交易金額")