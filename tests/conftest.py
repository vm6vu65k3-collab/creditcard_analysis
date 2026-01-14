import sys
import pytest
import logging 
from pathlib import Path 

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    
from creditcard_analysis.utils.schemas import (
    ColumnName, ChartType, Filter, ParamsJSON,
    ParamsFigure, ChartIn
)

def pytest_configure(config):
    Path("logs").mkdir(exist_ok = True)

    handlers = [
        logging.StreamHandler(),
        logging.FileHandler("logs/pytest.log", encoding = 'utf-8-sig')
    ]

    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers = handlers,
        force = True
    )

@pytest.fixture
def make_chartin():
    def _make(chart_type: ChartType, x_axis = ColumnName.industry, y_axis = None):
        return ChartIn(
            chart_type = chart_type,
            params_json = ParamsJSON(x_axis = x_axis, y_axis = y_axis),
            params_figure = ParamsFigure(),
            create_by = 1,
            filters = Filter()
        )
    return _make
