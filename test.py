from pprint import pprint
from pydantic import ValidationError 
from ..utils import ChartIn
import json

payload = {
    "chart_type": "heatmap",
    "params_json": {
        "x_axis": "industry",
        "y_axis": "age_level",
        "value": "trans_total",
        "value2": "trans_count"
    },
    "params_figure": {
        "set_title": "所有產業各族群平均金額"
    },
    "create_by": 99116,
    "filters": {
        "start_month": "201401",
        "end_month": "202111"
    }
}

pprint(payload)

# try: 
#     obj = ChartIn.model_validate(payload)
#     print("OK", obj)
# except ValidationError as e:
#     print(e.json(indent = 2))