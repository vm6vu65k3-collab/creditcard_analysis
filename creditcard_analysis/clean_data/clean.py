import json 
import pandas as pd 
import requests
import argparse
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime 
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.mysql import insert as mysql_insert 

from ..database import engine
from .create_ssl import build_ssl_context, SSLContextAdapter
from ..utils import handling_missing_value, handling_duplicate_value



# =========================
# Config
# =========================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "raw_data"

OPEN_DATA_CSV_URL = "https://www.nccc.com.tw/dataDownload/Age%20Group/BANK_TWN_ALL_AG.CSV"

EXPECTED = ['ym', 'nation', 'industry', 'age_level', 'trans_count', 'trans_total']

COLS_MAP = {
    "年月": "ym",
    "地區": "nation",
    "信用卡產業別": "industry",
    "年齡層": "age_level",
    "信用卡交易筆數": "trans_count",
    "信用卡交易金額[新臺幣]": "trans_total"
}

# =========================
# Downlaod CSV
# =========================
def download_csv(csv_url: str, save_dir: Path, cafile: str | None = None) -> Path:
    save_dir.mkdir(parents = True, exist_ok = True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = save_dir / f"raw_open_data_{timestamp}.csv"
    
    ctx = build_ssl_context(cafile, relax_strict = True)
    session = requests.Session()
    session.mount("https://", SSLContextAdapter(ctx))

    try:
        with session.get(csv_url, timeout = (10, 60), stream = True) as resp:
            resp.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size = 1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        break 
    except requests.exceptions.RequestException as e:
        if file_path.exists():
            file_path.unlink(missing_ok = True)
        raise RuntimeError(f"下載失敗：{e}") from e 
    
    print(f"[INFO] CSV 已下載至：{file_path}")
    return file_path


# =========================
# load_raw_data
# =========================

def load_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        csv_path,
        encoding = 'utf-8-sig',
        na_values = ['', ' ', 'NaN', 'Na']
    )

    return df 

def load_json(json_file: Path) -> pd.DataFrame:
    try:
        with open(json_file, 'r', encoding = 'utf-8-sig') as f:
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
                    payload = list[payload.values()]
            if not isinstance(payload, list):
                raise ValueError("JSON 無法轉成 records_list")
        df = pd.DataFrame(payload)            
    except json.JSONDecodeError: 
        df = pd.read_json(json_file, lines = True, encoding = 'utf-8-sig')
    
    df = df.reset_index(drop = True)

    return df 

# =========================
# Transform
# =========================

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns = COLS_MAP)
    
    missing = [c for c in EXPECTED if c not in df.columns]
    if missing:
        raise ValueError(f"[INFO] 缺失欄位：{missing}，目前欄位：{df.columns.tolist()}")
    
    df = df[EXPECTED].copy()

    for col in ['trans_count', 'trans_total']:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(',', ' ', regex = False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors = 'coerce')
    
    num_cols = ['trans_count', 'trans_total']
    str_cols = ['ym', 'nation', 'industry', 'age_level']
    df = handling_missing_value(df, num_cols, str_cols)
    df = handling_duplicate_value(df)

    df = df.astype(
        {
            "ym"         : str,
            "nation"     : str,
            "industry"   : str,
            "age_level"  : str,
            "trans_count": "int64",
            "trans_total": "int64"
        }
    ).copy()

    return df 


# =========================
# Load DB 
# =========================

def insert_into_mysql(df: pd.DataFrame, table_name = "clean_data", chunk_size = 1000) -> None:
    if df is None or df.empty:
        print("[INFO] df 為空，略過匯入")
        return 
    
    
    meta = MetaData()
    table = Table(table_name, meta, autoload_with = engine)
    records = df.to_dict(orient = 'records')
    total = len(records)

    print(f"[INFO] 準備匯入筆數：{total}")

    with engine.begin() as conn:
        for i in range(0, total, chunk_size):
            batch = records[i: i + chunk_size]
            stmt = mysql_insert(table).values(batch).prefix_with("IGNORE")
            conn.execute(stmt)
    
    print("[INFO] 匯入完成 (重複資料已自動略過)")


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
            raise ValueError("source = csv_url時，必須提供url")
        cafile: str | None = opts.cafile
        csv_path = download_csv(opts.url, opts.out_dir, cafile)
        df_raw = load_csv(csv_path)
    elif opts.source == "json_path":
        if not opts.path:
            raise ValueError("source = json_path時，必須提供path")
        df_raw = load_json(opts.path)
        print(f"[DEBUG] 原始：{len(df_raw)}")
    else:
        raise ValueError("source 只支援 csv_url 及 json_path")
    
    df = clean_data(df_raw)
    print(f"[DEBUG] 清理後：{len(df)}")
    insert_into_mysql(df, opts.table_name)
    
    print("[INFO] ETL完成\n")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description = "ETL for NCCC load (CSV_URL / JSON) -> MySQL")
    p.add_argument("--source", default = None, help = "資料來源型態")
    p.add_argument("--url", default = None, help = "source = csv_url時的下載URL")
    p.add_argument("--path", default = None, help = "source = json_path時的本機JSON / JSONL 檔案路徑")
    p.add_argument("--out_dir", default = str(DATA_DIR), help = "下載檔案儲存資料夾(csv_url 模式用)")
    p.add_argument("--table_name", default = "clean_data", help = "匯入資料表名稱")
    p.add_argument("--cafile", default = None, help = "指定 CA bundle 檔案")

    return p


def main():
    print(f"[TIME] {datetime.now()}")
    parser = build_parser()
    args = parser.parse_args()
    
    opts = ETLOptions(
        source     = args.source,
        url        = args.url if args.url else (OPEN_DATA_CSV_URL if args.source == "csv_url" else None),
        path       = Path(args.path).expanduser().resolve() if args.path else None,
        out_dir    = Path(args.out_dir).expanduser().resolve(),
        table_name = args.table_name,
        cafile     = args.cafile
    )

    run_etl(opts)

if __name__ == "__main__":
    main()