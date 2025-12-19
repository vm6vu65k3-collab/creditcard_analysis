import requests
import pandas as pd 
import json
from pathlib import Path 
from sqlalchemy import text
from datetime import datetime 
from database import engine
from sqlalchemy.exc import SQLAlchemyError 
from utils import handling_missing_value, handling_duplicate_value

OPEN_DATA_CSV_URL = "https://www.nccc.com.tw/dataDownload/Age%20Group/BANK_TWN_ALL_AG.CSV"

BASE_DIR = Path(__file__).resolve().parent 
DATA_DIR = BASE_DIR / "test_open_data"
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.mysql import insert as mysql_insert

from database import engine
from utils import handling_missing_value, handling_duplicate_value


# =========================
# Config
# =========================
DEFAULT_CSV_URL = "https://www.nccc.com.tw/dataDownload/Age%20Group/BANK_TWN_ALL_AG.CSV"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "open_data_downloads"

EXPECTED_COLS = ["ym", "nation", "industry", "age_level", "trans_count", "trans_total"]

# 可能遇到的中文欄名 → 英文欄名
COLS_MAP = {
    "年月": "ym",
    "地區": "nation",
    "信用卡產業別": "industry",
    "年齡層": "age_level",
    "信用卡交易筆數": "trans_count",
    "信用卡交易金額[新臺幣]": "trans_total",
}


# =========================
# Download (CSV URL)
# =========================
def download_csv(url: str, save_dir: Path, verify: bool | str = True) -> Path:
    """
    Download a CSV file via HTTP(S) and save to save_dir with timestamped filename.
    verify:
      - True/False
      - or path to CA bundle (e.g. "/etc/ssl/cert.pem")
    """
    save_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"raw_open_data_{ts}.csv"
    tmp_path = file_path.with_suffix(file_path.suffix + ".part")

    try:
        with requests.get(
            url,
            timeout=(10, 60),
            stream=True,
            verify=verify,
            headers={"User-Agent": "creditcard_analysis/1.0"},
        ) as resp:
            resp.raise_for_status()
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

        # 原子化 rename
        tmp_path.replace(file_path)

        if file_path.stat().st_size == 0:
            file_path.unlink(missing_ok=True)
            raise RuntimeError("下載完成但檔案大小為 0 bytes（疑似上游回空）")

    except requests.exceptions.RequestException as e:
        tmp_path.unlink(missing_ok=True)
        file_path.unlink(missing_ok=True)
        raise RuntimeError(f"下載失敗：{e}") from e

    print(f"[INFO] CSV 已下載至：{file_path} ({file_path.stat().st_size} bytes)")
    return file_path


# =========================
# Loaders (CSV / JSON)
# =========================
def load_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        csv_path,
        encoding="utf-8-sig",
        na_values=["", " ", "NaN", "Na", "nan", "NULL", "null"],
    )
    return df


def _unwrap_json_payload(payload: Any) -> list[dict]:
    """
    將常見 JSON 結構拆成 records list[dict]：
    - list[dict] 直接回傳
    - dict 包一層 data/records/result
    - dict 且 values 全是 dict → 轉 list(values)
    """
    if isinstance(payload, list):
        if payload and not isinstance(payload[0], dict):
            raise ValueError("JSON list 不是由 dict 組成")
        return payload

    if isinstance(payload, dict):
        for k in ("data", "records", "result"):
            v = payload.get(k)
            if isinstance(v, list) and (not v or isinstance(v[0], dict)):
                return v

        # dict values 全是 dict → 視為 records
        if payload and all(isinstance(v, dict) for v in payload.values()):
            return list(payload.values())

    raise ValueError("JSON 結構不是 records list，也不是 dict 包 records")


def load_json(json_path: Path) -> pd.DataFrame:
    """
    支援：
    - 標準 JSON（list 或 dict 包 list）
    - JSON Lines（.jsonl），自動 fallback
    """
    try:
        with open(json_path, "r", encoding="utf-8-sig") as f:
            payload = json.load(f)
        records = _unwrap_json_payload(payload)
        df = pd.DataFrame(records)
    except json.JSONDecodeError:
        # JSONL
        df = pd.read_json(json_path, lines=True, encoding="utf-8")

    df = df.reset_index(drop=True)
    return df


# =========================
# Transform (Common)
# =========================
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    # 先做欄名映射（中文→英文），英文已存在則不影響
    df = df.rename(columns=COLS_MAP).copy()

    # 如果欄位很多，只挑需要的欄位（並檢查缺失）
    missing = [c for c in EXPECTED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"缺失欄位：{missing}；目前欄位：{df.columns.tolist()}")

    df = df[EXPECTED_COLS].copy()

    # 先把數字欄位做去逗號、轉 numeric（避免 "1,234" 轉 int 失敗）
    for col in ("trans_count", "trans_total"):
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    num_cols = ["trans_count", "trans_total"]
    str_cols = ["ym", "nation", "industry", "age_level"]

    df = handling_missing_value(df, num_cols=num_cols, cat_cols=str_cols)
    df = handling_duplicate_value(df)

    # 最終 dtype
    df = df.astype(
        {
            "ym": str,
            "nation": str,
            "industry": str,
            "age_level": str,
            "trans_count": "int64",
            "trans_total": "int64",
        }
    ).copy()

    return df


# =========================
# Load (DB) - MySQL INSERT IGNORE
# =========================
def insert_into_mysql_ignore(df: pd.DataFrame, table_name: str = "clean_data", chunksize: int = 1000) -> None:
    """
    依賴 DB 已建 UNIQUE KEY。使用 INSERT IGNORE 避免重複鍵報錯，確保 ETL 可重跑。
    """
    if df is None or df.empty:
        print("[INFO] df 為空，略過匯入")
        return

    meta = MetaData()
    table = Table(table_name, meta, autoload_with=engine)

    records = df.to_dict(orient="records")

    total = len(records)
    print(f"[INFO] 準備匯入資料筆數：{total}")

    with engine.begin() as conn:
        for i in range(0, total, chunksize):
            batch = records[i:i + chunksize]
            stmt = mysql_insert(table).values(batch).prefix_with("IGNORE")
            conn.execute(stmt)

    print("[INFO] 匯入完成（重複鍵已自動略過）")


# =========================
# Orchestrator
# =========================
@dataclass
class ETLOptions:
    source: str
    url: str | None = None
    path: Path | None = None
    out_dir: Path = DATA_DIR
    table_name: str = "clean_data"
    cafile: str | None = None  # 若需指定 CA bundle


def run_etl(opts: ETLOptions) -> None:
    if opts.source == "csv_url":
        if not opts.url:
            raise ValueError("source=csv_url 時必須提供 url")
        verify: bool | str = opts.cafile if opts.cafile else True
        csv_path = download_csv(opts.url, opts.out_dir, verify=verify)
        df_raw = load_csv(csv_path)

    elif opts.source == "json_file":
        if opts.path is None:
            raise ValueError("source=json_file 時必須提供 path")
        df_raw = load_json(opts.path)

    else:
        raise ValueError("source 只支援 csv_url 或 json_file")

    df = clean_data(df_raw)
    insert_into_mysql_ignore(df, table_name=opts.table_name)
    print("[INFO] ETL 完成\n")


# =========================
# CLI
# =========================
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

def download_csv(url: str, save_dir: Path) -> Path:
    save_dir.mkdir(parents = True, exist_ok = True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"raw_data_{timestamp}.csv"
    
    try:
        with requests.get(url, timeout = (10, 60), verify = False, stream = True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size = 1024*1024):
                    if chunk:
                        f.write(chunk)
    except requests.exceptions.RequestException as e:
        if file_path.exists():
            file_path.unlink()
        raise RuntimeError(f"下載失敗：{e}") from e
    
    print(f"[INFO] CSV 已下載至 {file_path}")
    return file_path


def load_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        csv_path,
        encoding = "utf-8-sig",
        na_values = ["", " ", "NaN", "Na"]
    )
    return df 

def load_json(json_path: Path) -> pd.DataFrame:
    try:
        with open(json_path, "r", encoding = "utf-8-sig") as f:
            payload = json.load(f)
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

    return df 
   

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

    num_cols = ['trans_count', 'trans_total']
    str_cols = ['ym', 'nation', 'industry', 'age_level']
    df = handling_missing_value(df, num_cols, str_cols)
    df = handling_duplicate_value(df)

    df = df.astype({
        "ym"         : str,
        "nation"     : str,
        "industry"   : str,
        "age_level"  : str,
        "trans_count": int,
        "trans_total": int
    }).copy()

    return df

def insert_into_sql(df: pd.DataFrame, table_name: str = "clean_data", chunksize: int = 1000):
    if df is None or df.empty:
        print("[INFO] df 為空，略過匯入")
        return 
    
    records = df.to_dict(orient = "records")
    
    with engine.begin() as conn:
        try:
            rows = conn.execute(text(f"SELECT DISTINCT ym, nation, industry, age_level FROM {table_name}")).all()
            existing_keys = {(ym, nation, industry, age_level) for ym, nation, industry, age_level in rows}
        except SQLAlchemyError as e:
            print(f"[WARN] 查詢既有資料失敗，原因：{e}")
            existing_keys = set()

        df = df.copy()
        df['key'] = list(zip(df['ym'], df['nation'], df['industry'], df['age_level']))
        mask_new = ~df['key'].isin(existing_keys)
        df_new = df.loc[mask_new].drop(columns = ['key'])

        if df_new.empty:
            print("[INFO] 沒有新資料需匯入，結束")
            return 

        print(f"[INFO] 準備匯入資料筆數：{len(df_new)}")

        df_new.to_sql(
            name = table_name,
            con = conn,
            index = False,
            if_exists = 'append',
            method = 'multi',
            chunksize = 1000
        ) 

        print("[INFO] 匯入完成")


def run_etl(source: str, url:str | None = None, path: Path | None = None):
    if source == "csv_url":
        if not url:
            raise ValueError("source=csv_url 時必須提供url")
        csv_path = download_csv(url, DATA_DIR)
        df_raw = load_csv(csv_path)
    elif source == "json_file":
        if path is None:
            raise ValueError("source = json_file 時必須提供path")
        df_raw = load_json(path)
    else:
        raise ValueError("source 只支援 csv_url 或 json_file")
    
    df = clean_data(df_raw)
    insert_into_sql(df)
    print("\n")

if __name__ == "__run_etl__":
    run_etl(OPEN_DATA_CSV_URL)