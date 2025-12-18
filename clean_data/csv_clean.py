# clean_data/csv_clean.py
from __future__ import annotations

import argparse
import json
import ssl
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import certifi
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.mysql import insert as mysql_insert
from urllib3.poolmanager import PoolManager

from database import engine
from utils import handling_missing_value, handling_duplicate_value


# =========================
# Config
# =========================
DEFAULT_CSV_URL = "https://www.nccc.com.tw/dataDownload/Age%20Group/BANK_TWN_ALL_AG.CSV"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "open_data_downloads"

EXPECTED_COLS = ["ym", "nation", "industry", "age_level", "trans_count", "trans_total"]

# 常見中文欄名 → 英文欄名（若原本就是英文欄名則不影響）
COLS_MAP = {
    "年月": "ym",
    "地區": "nation",
    "信用卡產業別": "industry",
    "年齡層": "age_level",
    "信用卡交易筆數": "trans_count",
    "信用卡交易金額[新臺幣]": "trans_total",
}


# =========================
# SSL handling (Requests)
# =========================
def build_ssl_context(
    cafile: str | None = None,
    relax_strict: bool = True,
) -> ssl.SSLContext:
    """
    建立 SSLContext：
    - 預設使用 certifi CA bundle（requests 同源）
    - relax_strict=True 會關掉 VERIFY_X509_STRICT，避免 Python/openssl 對缺 SKI 的嚴格檢查
    """
    ca = cafile or certifi.where()
    ctx = ssl.create_default_context(cafile=ca)

    if relax_strict and hasattr(ctx, "verify_flags") and hasattr(ssl, "VERIFY_X509_STRICT"):
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT

    return ctx


class SSLContextAdapter(HTTPAdapter):
    """讓 requests 使用自訂 SSLContext（含 relax strict / 指定 CA）。"""

    def __init__(self, ssl_context: ssl.SSLContext, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        pool_kwargs["ssl_context"] = self.ssl_context
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            **pool_kwargs,
        )


def build_requests_session(
    cafile: str | None = None,
    relax_strict: bool = True,
) -> requests.Session:
    s = requests.Session()
    ctx = build_ssl_context(cafile=cafile, relax_strict=relax_strict)
    s.mount("https://", SSLContextAdapter(ctx))
    return s


# =========================
# Download (CSV URL)
# =========================
def download_csv(url: str, save_dir: Path, session: requests.Session) -> Path:
    """
    下載 CSV（stream）並以 .part 原子化落地。
    """
    save_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"raw_open_data_{ts}.csv"
    tmp_path = file_path.with_suffix(file_path.suffix + ".part")

    try:
        with session.get(
            url,
            timeout=(10, 60),
            stream=True,
            headers={"User-Agent": "creditcard_analysis/1.0"},
        ) as resp:
            resp.raise_for_status()

            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

        tmp_path.replace(file_path)

        if file_path.stat().st_size == 0:
            file_path.unlink(missing_ok=True)
            raise RuntimeError("下載成功但檔案大小為 0 bytes（疑似上游回空）")

        print(f"[INFO] CSV 已下載至：{file_path} ({file_path.stat().st_size} bytes)")
        return file_path

    except requests.exceptions.RequestException as e:
        tmp_path.unlink(missing_ok=True)
        file_path.unlink(missing_ok=True)
        raise RuntimeError(f"下載失敗：{e}") from e


# =========================
# Loaders (CSV / JSON)
# =========================
def load_csv(csv_path: Path) -> pd.DataFrame:
    return pd.read_csv(
        csv_path,
        encoding="utf-8-sig",
        na_values=["", " ", "NaN", "Na", "nan", "NULL", "null"],
    )


def _unwrap_json_payload(payload: Any) -> list[dict]:
    """
    支援：
    - list[dict]
    - dict 包 data/records/result list[dict]
    - dict values 全是 dict → 轉 list(values)
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

        if payload and all(isinstance(v, dict) for v in payload.values()):
            return list(payload.values())

    raise ValueError("JSON 結構不是 records list，也不是 dict 包 records")


def load_json(json_path: Path) -> pd.DataFrame:
    """
    支援：
    - JSON（list 或 dict 包 records）
    - JSONL（lines=True）
    """
    try:
        with open(json_path, "r", encoding="utf-8-sig") as f:
            payload = json.load(f)
        records = _unwrap_json_payload(payload)
        df = pd.DataFrame(records)
    except json.JSONDecodeError:
        df = pd.read_json(json_path, lines=True, encoding="utf-8")

    return df.reset_index(drop=True)


# =========================
# Transform (Common)
# =========================
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.rename(columns=COLS_MAP)

    # 若沒有任何可識別欄名，但剛好是 6 欄，則視為固定欄序
    if not set(EXPECTED_COLS).issubset(df.columns) and len(df.columns) == 6:
        df.columns = EXPECTED_COLS

    missing = [c for c in EXPECTED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"缺失欄位：{missing}；目前欄位：{df.columns.tolist()}")

    df = df[EXPECTED_COLS].copy()

    # 數值欄位去逗號、轉 numeric
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

    df = handling_missing_value(df, num_cols, str_cols)
    df = handling_duplicate_value(df)

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
    依賴 DB 已建立 UNIQUE KEY。
    INSERT IGNORE：重複鍵自動略過，確保 ETL 可重跑。
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
    url: str
    path: Path | None
    out_dir: Path
    table_name: str
    cafile: str | None
    relax_ssl: bool


def run_etl(opts: ETLOptions) -> None:
    if opts.source == "csv_url":
        session = build_requests_session(cafile=opts.cafile, relax_strict=opts.relax_ssl)
        csv_path = download_csv(opts.url, opts.out_dir, session=session)
        df_raw = load_csv(csv_path)

    elif opts.source == "json_file":
        if opts.path is None:
            raise ValueError("source=json_file 時必須提供 --path")
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
    p.add_argument(
        "--source",
        choices=["csv_url", "json_file"],
        default="csv_url",
        help="資料來源型態（預設 csv_url）",
    )
    p.add_argument("--url", default=DEFAULT_CSV_URL, help="source=csv_url 時的下載 URL")
    p.add_argument("--path", default=None, help="source=json_file 時的本機 JSON/JSONL 檔案路徑")
    p.add_argument("--out-dir", default=str(DATA_DIR), help="下載檔案儲存資料夾（csv_url 模式用）")
    p.add_argument("--table", default="clean_data", help="匯入的資料表名稱")
    p.add_argument("--cafile", default=None, help="指定 CA bundle 檔案（例如 /etc/ssl/cert.pem）")
    p.add_argument(
        "--relax-ssl",
        action="store_true",
        default=True,
        help="放寬嚴格 X.509 檢查（預設啟用，可避免 Missing Subject Key Identifier）",
    )
    p.add_argument(
        "--strict-ssl",
        dest="relax_ssl",
        action="store_false",
        help="使用嚴格 X.509 檢查（如確定站台憑證完整才建議）",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

    opts = ETLOptions(
        source=args.source,
        url=args.url,
        path=Path(args.path).expanduser().resolve() if args.path else None,
        out_dir=Path(args.out_dir).expanduser().resolve(),
        table_name=args.table,
        cafile=args.cafile,
        relax_ssl=args.relax_ssl,
    )
    run_etl(opts)


if __name__ == "__main__":
    t1 = datetime.now()
    main()
    t2 = datetime.now()
    print(f"所需時間 {t2 - t1}")