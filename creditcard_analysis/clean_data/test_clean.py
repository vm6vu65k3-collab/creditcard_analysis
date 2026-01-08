import json
import requests
import pandas as pd 
from pathlib import Path 
from datetime import datetime 


from .test_ssl import build_ssl_context, SSLContextAdapter

#============
# Config
#============
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "test_raw_data"
TABLE_NAME = 'test_table'

OPEN_DATA_CSV_URL = "https://www.nccc.com.tw/dataDownload/Age%20Group/BANK_TWN_ALL_AG.CSV"

COLS_MAP = {
    '年月'          : 'ym',
    '地區'          : 'nation',
    '信用卡產業別'      : 'industry',
    '年齡層'         : 'age_level',
    '信用卡交易筆數'     : 'trans_count',
    '信用卡交易金額[新臺幣]': 'trans_total'
}

EXPECTED = ['ym', 'nation', 'industry', 'age_level', 'trans_count', 'trans_total']


#============
# Extract 
#============
def download_csv(csv_url: str, save_dir: Path, cafile: str | None) -> Path:
    save_dir.mkdir(exist_ok = True, parents = True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = save_dir / f"raw_data{ts}.csv"

    ctx = build_ssl_context(cafile, relax_strict = True)
    session = requests.Session()
    session.mount("http://", SSLContextAdapter(ctx))

    try:
        with session.get(csv_url, timeout = (10, 60), stream = True) as resp:
            resp.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size = 1024 * 1024):
                    if chunk:
                        f.write(chunk)
    except requests.exceptions.RequestException as e:
        if file_path.exists():
            file_path.unlink(missing_ok = True)
        raise RuntimeError(f"下載失敗：{e}") from e 
    
    print(f"[INFO] CSV 已下載至：{file_path}")
    return file_path

#==================== load_csv ====================
def load_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        csv_path,
        encoding = 'utf-8-sig',
        na_values = [' ', '', 'NaN', 'Na']
    )

    return df 

def load_json(json_path: Path) -> pd.DataFrame:
    try:
        with open(json_path, 'r', encoding = 'utf-8-sig') as f:
            payload = json.load(f)
            if isinstance(payload, dict):
                found = None 
                for k, v in payload.items():
                    if isinstance(v, list) and (not v or isinstance(v[0], dict)):
                        found = v 
                        if found is not None:
                            payload = found 
                    elif payload and all(isinstance(v, dict) for v in payload.values()):
                        payload = list(payload.values())
            if not isinstance(payload, list):
                raise ValueError("JSON 無法轉成 records list")
        
        df = pd.DataFrame(payload)
    
    except json.JSONDecodeError:
        df = pd.read_json(json_path, lines = True, encoding = 'utf-8-sig')
    
    df = df.reset_index(drop = True)

    return df