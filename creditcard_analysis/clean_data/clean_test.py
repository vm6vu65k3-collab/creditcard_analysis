import json
import requests
import argparse 
import pandas as pd 
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.mysql import insert as mysql_insert


from ..database import engine
from .ssl_test import build_ssl_context, SSLContextAdapter 
from ..utils import handling_missing_value, handling_duplicate_value


# =========================
# Config
# =========================
BASE_DIR = Path(__file__).resolve().parent 
DATA_DIR = BASE_DIR / f"test_raw_data"
TABLE_NAME = 'clean_data'

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


# =========================
# Download CSV 
# =========================
def download_data(csv_url: str, save_dir: Path, cafile: str | None = None) -> Path:
    save_dir.mkdir(exist_ok = True, parents = True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = save_dir / f"test_raw_data{ts}.csv"
    
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
    except requests.exceptions.RequestException as e:
        if file_path.exists():
            file_path.unlink(missing_ok = True)
        raise RuntimeError(f"下載失敗：{e}") from e

    print(f"[INFO] CSV 已下載至：{file_path}")
    return file_path


# =========================
# Load csv_data
# =========================
def load_csv(csv_file: Path) -> pd.DataFrame:
    df = pd.read_csv(
        csv_file,
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
                if found is not None:
                    payload = found 
                elif payload and all(isinstance(v, list) for v in payload.values()):
                    payload = list(payload.values())
            if not isinstance(payload, list):
                raise ValueError("JSON 無法轉成 records list")
        df = pd.DataFrame(payload)
    except json.JSONDecodeError:
        df = pd.read_json(json_file, lines = True, encoding = 'utf-8-sig')
    
    df = df.reset_index(drop = True)

    return df 


# =========================
# Transform 
# =========================
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns = COLS_MAP).copy()

    missing = [c for c in EXPECTED if c not in df.columns.tolist()]
    if missing:
        print(f"[INFO] 缺失欄位：{missing} 目前欄位：{df.columns.tolist()}")
    
    for cols in ['trans_count', 'trans_total']:
        df[cols] = (
            df[cols]
            .astype(str)
            .str.replace(',', '', regex = False)
            .str.strip()
        )
        df[cols] = pd.to_numeric(df[cols], errors = 'coerce')

    df = df.astype(
        {
            'ym'         : str,
            'nation'     : str,
            'industry'   : str,
            'age_level'  : str,
            'trans_count': 'int64',
            'trans_total': 'int64'
        }
    )

    num_cols = ['trans_count', 'trans_total']
    str_cols = ['ym', 'nation', 'industry', 'age_level']
    df = handling_missing_value(df, num_cols, str_cols)
    df = handling_duplicate_value(df)

    df = df[EXPECTED]

    return df 

# =========================
# Load DB 
# =========================
def insert_into_db(df: pd.DataFrame, table_name: str = 'clean_data', chunk_size = 1000) -> None:
    if df is None or df.empty:
        print('[INFO] df 為空，略過匯入')
        return 
    
    meta = MetaData()
    table = Table(table_name, meta, autoload_with = engine)
    records = df.to_dict(orient = 'records')
    total = len(records)
    
    print(f"[INFO] 準備匯入資料筆數：{total}")
    
    with engine.begin() as conn:
        for i in range(0, total, chunk_size):
            batch = records[i: i + chunk_size]
            stmt = mysql_insert(table).values(batch).prefix_with('IGNORE')
            conn.execute(stmt)
    
    print(f"[INFO] 資料已匯入'{table_name}'")


@dataclass 
class ETLOption:
    source    : str
    url       : str | None = None
    file      : Path | None = None
    out_dir   : Path = DATA_DIR
    table_name: str = TABLE_NAME
    cafile    : str | None = None


def run_etl(opts: ETLOption) -> None:
    if opts.source == "csv_url":
        if not opts.url:
            raise ValueError("source = csv_url時必須提供url")
        csv_file = download_data(opts.url, opts.out_dir, opts.cafile)
        df_raw = load_csv(csv_file)
    elif opts.source == "json_file":
        if not opts.file:
            raise ValueError("source = json_file時必須提供file")
        df_raw = load_json(opts.file)
    else:
        raise ValueError("source 只支援 CSV_URL 及 JSON_FILE")
    
    df = clean_data(df_raw)
    insert_into_db(df, TABLE_NAME)
    
    print("[INFO] ETL完成\n")

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description = 'ETL for NCCC ( CSV / JSON ) -> MySQL')
    p.add_argument('--source', default = None, help = '資料來源型態')
    p.add_argument('--url', default = None, help = 'source = csv_url時所需的下載URL')
    p.add_argument('--file', default = None, help = 'source = json_file時所需的檔案路徑')
    p.add_argument('--out_dir', default = DATA_DIR, help = 'CSV下載路徑')
    p.add_argument('--table_name', default = None, help = '匯入資料表名稱')
    p.add_argument('--cafile', default = None, help = '指定 CA bundle 檔案')

    return p 


def main():
    print(f"[INFO] {datetime.now()}")
    parser = build_parser()
    args = parser.parse_args()
    
    opts = ETLOption(
        source     = args.source,
        url        = args.url if args.url else (OPEN_DATA_CSV_URL if args.source == 'csv_url' else None),
        file       = Path(args.file).expanduser().resolve() if args.file else None,
        out_dir    = Path(args.out_dir).expanduser().resolve(),
        table_name = args.table_name,
        cafile     = args.cafile
    )

    run_etl(opts)


if __name__ == "__main__":
    main()
