import json, pandas as pd 
from pathlib import Path 

BASE_DIR = Path(__file__).resolve().parent 

def loand_and_clean_json(json_path: Path) -> pd.DataFrame:
    try:
        with open(json_path, 'r', encoding = 'utf-8-sig') as f:
            payload = json.load(f)
        if isinstance(payload, dict):
            found = None 
            for k, v in payload.items():
                if isinstance(v, list) and (not v or isinstance(v[0], dict)):
                    found = v 
                    break
            if found is not None:
                payload = found 
            elif payload and all(isinstance(v, dict) for v in payload.values()):
                payload = list(payload.values())
        
        if not isinstance(payload, list):
            raise ValueError("JSON 結構無法轉成records list")
            
        df = pd.DataFrame(payload)
    except json.JSONDecodeError:
        df = pd.read_json(json_path, lines = True, encoding = 'utf-8-sig')

    
    df = df.reset_index(drop = True)
    
    cols_map = {
        "年月"               : "ym",
        "地區"               : "nation",
        "信用卡產業別"         : "industry",
        "年齡層"              : "age_level",
        "信用卡交易筆數"       : "trans_count",
        "信用卡交易金額[新臺幣]": "trans_total"
    }
    
    df = df.rename(columns = cols_map)

    expected = ['ym', 'nation', 'industry', 'age_level', 'trans_count', 'trans_total']
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"缺失欄位：{missing}，目前欄位：{df.columns.tolist()}")
    
    df = df[expected].copy()
    print(df.head(10))
    return df 

loand_and_clean_json(BASE_DIR/"test_open_data"/"json_data.json")