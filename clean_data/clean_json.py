import json
import pandas as pd 
from pathlib import Path 

BASE_DIR = Path(__file__).resolve().parent

def load_and_clean_json(json_path: Path) -> pd.DataFrame:
    try:
        with open(json_path, "r", encoding = "utf-8-sig") as f:
            payload = json.load(f)
        print(payload[0])
        if isinstance(payload, dict):
            for k in ("data", "records", "result"):
                if isinstance(payload.get(k), list):
                    payload = payload[k]
                    break 
            else:
                if payload and all(isinstance(v, dict) for v in payload.values()):
                    payload = list(payload.values())
        if not isinstance(payload, list):
            raise ValueError("JSON 結構不是 records list，也不是dict 包 records")

        df = pd.DataFrame(payload)      
    except json.JSONDecodeError:
        df = pd.read_json(json_path, lines = True, encoding = "utf-8")

    df = df.reset_index(drop = True)    

    col_map = {
        "年月"               : "ym",
        "地區"               : "nation",
        "信用卡產業別"         : "industry",
        "年齡層"              : "age_level",
        "信用卡交易筆數"       : "trans_count",
        "信用卡交易金額[新臺幣]": "trans_total"
    }

    df = df.rename(columns = col_map)

    expected = ['ym', 'nation', 'industry', 'age_level', 'trans_count', 'trans_total']
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"欄位缺少：{missing}; 目前欄位：{df.columns.tolist()}")
    
    df = df[expected].copy()
    print(df.head(10))
    return df 

load_and_clean_json(BASE_DIR/"test_open_data"/"json_data.json")
