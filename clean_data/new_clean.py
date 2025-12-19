import json, pandas as pd 
import argparse
import requests
from dataclasses import dataclass 
from datetime import datetime
from pathlib import Path
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.mysql import insert as mysql_insert
from database import engine   
from .create_ssl import build_ssl_context, SSLContextAdapter
from utils import handling_duplicate_value, handling_missing_value

# =========================
# Config
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "open_data_downloads"

DEFAULT_CSV_URL = "https://www.nccc.com.tw/dataDownload/Age%20Group/BANK_TWN_ALL_AG.CSV"


# =========================
# Download (CSV URL)
# =========================
def download_for_csv(url: str, save_dir: Path, cafile: bool | str = True) -> Path:
    save_dir.mkdir(parents = True, exist_ok = True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"raw_data_{timestamp}.csv"

    ctx = build_ssl_context(cafile = cafile, relax_strict = True)
    session = requests.Session()
    session.mount("https://", SSLContextAdapter(ctx))

    try:
        with session.get(url, timeout = (10, 60), stream = True) as resp:
            resp.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size = 1024*1024):
                    if chunk:
                        f.write(chunk)
    except requests.exceptions.RequestException as e:
        if file_path.exists():
            file_path.unlink(missing_ok = True)
        raise RuntimeError(f"下載失敗:{e}") from e
    
    print(f"[INFO] CSV已下載至 {file_path}")
    return file_path 

# =========================
# Loaders (CSV / JSON)
# =========================
def load_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        csv_path,
        encoding = "utf-8-sig",
        na_values = ["", " ", "NaN", "Na"]
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

    return df     
   

# =========================
# Transform (Common)
# =========================
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
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

    num_cols = ['trans_count', 'trans_total']
    str_cols = ['ym', 'nation', 'industry', 'age_level']
    df = handling_missing_value(df, num_cols, str_cols)
    df = handling_duplicate_value(df)

    df = df.astype({
        "ym"         : str,
        "nation"     : str,
        "industry"   : str,
        "age_level"  : str,
        "trans_count": "int64",
        "trans_total": "int64"
    })

    return df 

# =========================
# Load (DB) - MySQL INSERT IGNORE
# =========================
def insert_into_mysql(df: pd.DataFrame, table_name: str = "clean_data", chunksize: int = 1000):
    if df is None or df.empty:
        print("[INFO] df 為空，略過匯入")
        return 
    
    meta = MetaData()
    table = Table(table_name, meta, autoload_with = engine)

    records = df.to_dict(orient = "records")
    total = len(records)

    print(f"[INFO] 準備匯入資料筆數： {total}")

    with engine.begin() as conn:
        for i in range(0, total, chunksize):
            batch = records[i: i + chunksize]
            stmt = mysql_insert(table).values(batch).prefix_with("IGNORE")
            conn.execute(stmt)
    
    print("[INFO] 匯入完成 (重複鍵已自動略過)")



@dataclass 
class ETLOptions:
    source    : str
    url       : str | None = None
    path      : Path | None = None
    out_dir   : Path = DATA_DIR
    table_name: str = "clean_data"
    cafile    : str | None = None

def run_etl(opts: ETLOptions) -> None:
    if opts.source == "csv_url":
        if not opts.url:
            raise ValueError("source = csv_url 時必須提供 url")
        cafile: str | None = opts.cafile 
        csv_path = download_for_csv(opts.url, opts.out_dir, cafile = cafile)
        df_raw = load_csv(csv_path)
    elif opts.source == "json_file":
        if not opts.path:
            raise ValueError("source = json_file 時必須提供 path")
        df_raw = load_json(opts.path)
    else:
        raise ValueError("source 只支援 csv_url 或 json_file")
    
    df = clean_data(df_raw)
    insert_into_mysql(df, table_name = opts.table_name)
    print("[INFO] ETL完成\n")



def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ETL for NCCC open data (CSV URL / local JSON) -> MySQL")
    p.add_argument("--source", required=True, choices=["csv_url", "json_file"], help="資料來源型態")
    p.add_argument("--url", default=None, help="source=csv_url 時的下載 URL")
    p.add_argument("--path", default=None, help="source=json_file 時的本機 JSON/JSONL 檔案路徑")
    p.add_argument("--out-dir", default=str(DATA_DIR), help="下載檔案儲存資料夾（csv_url 模式用）")
    p.add_argument("--table", default="clean_data", help="匯入的資料表名稱")
    p.add_argument("--cafile", default=None, help="指定 CA bundle 檔案（例如 /etc/ssl/cert.pem）")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    opts = ETLOptions(
        source=args.source,
        url=args.url if args.url else (DEFAULT_CSV_URL if args.source == "csv_url" else None),
        path=Path(args.path).expanduser().resolve() if args.path else None,
        out_dir=Path(args.out_dir).expanduser().resolve(),
        table_name=args.table,
        cafile=args.cafile,
    )
    run_etl(opts)


if __name__ == "__main__":
    main()